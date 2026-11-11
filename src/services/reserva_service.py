from datetime import datetime

from database.conexao import obter_conexao
from src.models.reserva import Reserva
from src.repositories.bloqueio_quarto_repository import BloqueioQuartoRepository
from src.repositories.hospede_repository import HospedeRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import bloqueio_regras
from src.services import reserva_regras as regras
from src.services.erros import ErroNegocio
from src.utils.filtros import normalizar_texto, parece_numerico
from src.utils.formatacao import apenas_digitos, formatar_data_hora
from src.utils.sessao import Sessao
from src.utils.constantes import (MOTIVO_CANCELAMENTO_MAX, MOTIVO_CANCELAMENTO_MIN,
                                  QUARTO_DISPONIVEL, QUARTO_MANUTENCAO, QUARTO_OCUPADO,
                                  RESERVA_CONFIRMADA, RESERVA_HOSPEDADA)


def _agora():
    """Hora atual sem microssegundos, igual ao que o banco guarda."""
    return datetime.now().replace(microsecond=0)


class ReservaService:
    def __init__(self, repo=None, quarto_repo=None, hospede_repo=None, usuario_repo=None,
                 bloqueio_repo=None):
        self.repo = repo or ReservaRepository()
        self.quarto_repo = quarto_repo or QuartoRepository()
        self.hospede_repo = hospede_repo or HospedeRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()
        self.bloqueio_repo = bloqueio_repo or BloqueioQuartoRepository()

    # ---------- consultas ----------
    def listar(self):
        return self.repo.listar()

    def pesquisar(self, termo="", situacao="", periodo_de=None, periodo_ate=None):
        """Filtra as reservas (mais recentes primeiro). Todos os filtros são opcionais.

        termo:   nome ou CPF do hóspede, número do quarto ou código da reserva
        situacao: Confirmada, Hospedada, Finalizada, Cancelada ou Não compareceu
        periodo_de / periodo_ate: traz as reservas que ocupam algum dia dentro do período
        """
        if periodo_de and periodo_ate and periodo_ate < periodo_de:
            raise ErroNegocio("No período, a data final deve ser igual ou posterior à inicial.")

        termo = (termo or "").strip()
        texto = normalizar_texto(termo)
        digitos = apenas_digitos(termo) if parece_numerico(termo) else ""
        hospedes = {h.id: h for h in self.hospede_repo.listar()} if termo else {}
        quartos = {q.id: q for q in self.quarto_repo.listar()} if termo else {}

        encontradas = []
        for r in self.repo.listar():
            if situacao and r.situacao != situacao:
                continue
            if periodo_de and r.data_saida < periodo_de:
                continue
            if periodo_ate and r.data_entrada > periodo_ate:
                continue
            if termo:
                hospede, quarto = hospedes.get(r.hospede_id), quartos.get(r.quarto_id)
                campos = [f"{r.id:04d}",
                          normalizar_texto(hospede.nome) if hospede else "",
                          normalizar_texto(quarto.numero) if quarto else ""]
                achou = any(texto in campo for campo in campos)
                if not achou and digitos and hospede:
                    achou = digitos in apenas_digitos(hospede.cpf)
                if not achou:
                    continue
            encontradas.append(r)
        return sorted(encontradas, key=lambda r: r.id, reverse=True)

    def buscar_por_id(self, reserva_id):
        return self.repo.buscar_por_id(reserva_id)

    def tem_conflito(self, quarto_id, entrada, saida):
        return bool(self.repo.listar_conflitantes(quarto_id, entrada, saida))

    def responsaveis(self, reservas):
        """{usuario_id: nome} de quem fez check-in, check-out, cancelamento ou no-show das reservas.

        Busca direto no repositório de usuários, pois listar usuários é restrito ao administrador.
        """
        ids = set()
        for r in reservas:
            ids |= {r.checkin_por, r.checkout_por, r.cancelada_por, r.noshow_por}
        ids -= {None}
        nomes = {}
        for usuario_id in ids:
            usuario = self.usuario_repo.buscar_por_id(usuario_id)
            nomes[usuario_id] = usuario.nome if usuario else "—"
        return nomes

    # ---------- criação ----------
    def criar_reserva(self, hospede_id, quarto_id, entrada, saida, numero_hospedes):
        Sessao.exigir("reservas.criar")
        try:
            regras.validar_periodo(entrada, saida)
        except ValueError as erro:
            raise ErroNegocio(str(erro))

        if self.hospede_repo.buscar_por_id(hospede_id) is None:
            raise ErroNegocio("Hóspede não encontrado.")
        quarto = self.quarto_repo.buscar_por_id(quarto_id)
        if quarto is None:
            raise ErroNegocio("Quarto não encontrado.")
        if quarto.situacao == QUARTO_MANUTENCAO:
            raise ErroNegocio("Quarto em manutenção.")
        bloqueios = self.bloqueio_repo.listar_sobrepostos(
            *bloqueio_regras.intervalo_da_reserva(entrada, saida), quarto_id=quarto_id)
        if bloqueios:
            b = bloqueios[0]
            raise ErroNegocio(f"Quarto bloqueado de {formatar_data_hora(b.inicio)} a "
                              f"{formatar_data_hora(b.fim)} ({b.motivo}).")
        if self.tem_conflito(quarto_id, entrada, saida):
            raise ErroNegocio("Quarto já reservado neste período.")
        try:
            regras.validar_capacidade(quarto, numero_hospedes)
        except ValueError as erro:
            raise ErroNegocio(str(erro))

        diarias = regras.calcular_diarias(entrada, saida)
        reserva = Reserva(
            hospede_id=hospede_id, quarto_id=quarto_id,
            data_entrada=entrada, data_saida=saida,
            valor_diaria=quarto.preco_diaria,
            valor_total=regras.calcular_total(diarias, quarto.preco_diaria),
            situacao=RESERVA_CONFIRMADA,
        )
        with obter_conexao() as conexao:
            return self.repo.criar(reserva, conexao=conexao)

    # ---------- mudanças de situação ----------
    def cancelar(self, reserva_id, motivo):
        """Cancela a reserva, exigindo o motivo.

        Grava o momento (data e hora de agora), o motivo e o usuário logado (Sessao).
        """
        Sessao.exigir("reservas.cancelar")
        motivo = (motivo or "").strip()
        if len(motivo) < MOTIVO_CANCELAMENTO_MIN:
            raise ErroNegocio("Informe o motivo do cancelamento.")
        if len(motivo) > MOTIVO_CANCELAMENTO_MAX:
            raise ErroNegocio(
                f"O motivo deve ter no máximo {MOTIVO_CANCELAMENTO_MAX} caracteres.")
        reserva = self._obter(reserva_id)
        if not regras.pode_cancelar(reserva):
            raise ErroNegocio("Só é possível cancelar reservas confirmadas, antes do check-in.")
        if not self.repo.registrar_cancelamento(reserva_id, _agora(), Sessao.usuario.id, motivo):
            raise ErroNegocio("A situação da reserva mudou. Atualize a tela e tente de novo.")
        return self._obter(reserva_id)

    def impedimento_no_show(self, reserva):
        """Texto com o motivo de a reserva não poder virar no-show, ou None se pode."""
        return regras.impedimento_no_show(reserva, _agora().date())

    def marcar_no_show(self, reserva_id):
        """Marca a reserva como 'Não compareceu'.

        Grava o momento (data e hora de agora) e o usuário logado (Sessao). A reserva deixa
        de bloquear o quarto, que volta a ficar livre para o período.
        """
        Sessao.exigir("reservas.noshow")
        reserva = self._obter(reserva_id)
        impedimento = self.impedimento_no_show(reserva)
        if impedimento:
            raise ErroNegocio(impedimento)
        if not self.repo.registrar_no_show(reserva_id, _agora(), Sessao.usuario.id):
            raise ErroNegocio("A situação da reserva mudou. Atualize a tela e tente de novo.")
        return self._obter(reserva_id)

    def fazer_checkin(self, reserva_id):
        """Registra a entrada do hóspede.

        Grava o momento real (data e hora de agora) e o usuário logado (Sessao). A data de
        entrada prevista da reserva continua como estava.
        """
        Sessao.exigir("reservas.checkin")
        reserva = self._obter(reserva_id)
        if not regras.pode_fazer_checkin(reserva):
            raise ErroNegocio("O check-in só é permitido para reservas confirmadas.")
        with obter_conexao() as conexao:       # reserva e quarto mudam juntos, ou nenhum muda
            if not self.repo.registrar_checkin(reserva_id, _agora(), Sessao.usuario.id,
                                               conexao=conexao):
                raise ErroNegocio("A situação da reserva mudou. Atualize a tela e tente de novo.")
            self.quarto_repo.atualizar_situacao(reserva.quarto_id, QUARTO_OCUPADO,
                                                conexao=conexao)
        return self._obter(reserva_id)

    def fazer_checkout(self, reserva_id):
        """Registra a saída do hóspede, com o momento real e o usuário logado (Sessao)."""
        Sessao.exigir("reservas.checkin")
        reserva = self._obter(reserva_id)
        if reserva.situacao != RESERVA_HOSPEDADA:
            raise ErroNegocio("O check-out só é permitido para hóspedes hospedados.")
        quando = _agora()
        if reserva.checkin_em is not None and quando < reserva.checkin_em:
            raise ErroNegocio("O horário do check-out não pode ser anterior ao do check-in.")
        with obter_conexao() as conexao:
            if not self.repo.registrar_checkout(reserva_id, quando, Sessao.usuario.id,
                                                conexao=conexao):
                raise ErroNegocio("A situação da reserva mudou. Atualize a tela e tente de novo.")
            self.quarto_repo.atualizar_situacao(reserva.quarto_id, QUARTO_DISPONIVEL,
                                                conexao=conexao)
        return self._obter(reserva_id)

    # ---------- internos ----------
    def _obter(self, reserva_id):
        reserva = self.repo.buscar_por_id(reserva_id)
        if reserva is None:
            raise ErroNegocio("Reserva não encontrada.")
        return reserva
