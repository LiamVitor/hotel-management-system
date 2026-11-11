from datetime import datetime

from src.models.bloqueio_quarto import BloqueioQuarto
from src.repositories.bloqueio_quarto_repository import BloqueioQuartoRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import bloqueio_regras as regras
from src.services.erros import ErroNegocio
from src.utils.constantes import MOTIVO_BLOQUEIO_MAX, MOTIVO_BLOQUEIO_MIN
from src.utils.formatacao import formatar_data, formatar_data_hora
from src.utils.sessao import Sessao


def _agora():
    """Hora atual sem microssegundos, igual ao que o banco guarda."""
    return datetime.now().replace(microsecond=0)


class BloqueioQuartoService:
    def __init__(self, repo=None, quarto_repo=None, reserva_repo=None, usuario_repo=None):
        self.repo = repo or BloqueioQuartoRepository()
        self.quarto_repo = quarto_repo or QuartoRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    # ---------- consultas ----------
    def historico(self, quarto_id=None, periodo_de=None, periodo_ate=None):
        """Histórico de bloqueios, do mais recente para o mais antigo.

        quarto_id: só desse quarto (None = todos); periodo_de / periodo_ate: datas, limites
        incluídos, para ver só os bloqueios que tocam o intervalo.
        """
        Sessao.exigir("bloqueios.ver")
        if periodo_de and periodo_ate and periodo_ate < periodo_de:
            raise ErroNegocio("A data final do período não pode ser anterior à inicial.")
        return self.repo.listar(quarto_id, periodo_de, periodo_ate)

    def buscar_por_id(self, bloqueio_id):
        return self.repo.buscar_por_id(bloqueio_id)

    def situacao(self, bloqueio):
        """Agendado, Em andamento ou Encerrado, conforme a hora de agora."""
        return regras.situacao_do_bloqueio(bloqueio, _agora())

    def responsaveis(self, bloqueios):
        """{usuario_id: nome} de quem registrou os bloqueios informados.

        Busca direto no repositório de usuários, pois listar usuários é restrito ao administrador.
        """
        nomes = {}
        for usuario_id in {b.usuario_id for b in bloqueios}:
            usuario = self.usuario_repo.buscar_por_id(usuario_id)
            nomes[usuario_id] = usuario.nome if usuario else "—"
        return nomes

    # ---------- registro ----------
    def registrar(self, quarto_id, inicio, fim, motivo):
        """Registra um período em que o quarto fica indisponível.

        inicio e fim são datetime (data e hora). Grava o usuário logado (Sessao) e o momento do
        registro. O bloqueio não pode ficar sobre outro bloqueio do mesmo quarto nem sobre uma
        reserva ativa: nesse caso a reserva precisa ser cancelada ou remarcada antes.
        """
        Sessao.exigir("bloqueios.gerenciar")
        quarto = self.quarto_repo.buscar_por_id(quarto_id)
        if quarto is None:
            raise ErroNegocio("Quarto não encontrado.")

        motivo = (motivo or "").strip()
        if len(motivo) < MOTIVO_BLOQUEIO_MIN:
            raise ErroNegocio("Informe o motivo do bloqueio.")
        if len(motivo) > MOTIVO_BLOQUEIO_MAX:
            raise ErroNegocio(f"O motivo deve ter no máximo {MOTIVO_BLOQUEIO_MAX} caracteres.")

        impedimento = regras.impedimento_do_periodo(inicio, fim, _agora())
        if impedimento:
            raise ErroNegocio(impedimento)

        existente = self.repo.listar_sobrepostos(inicio, fim, quarto_id)
        if existente:
            b = existente[0]
            raise ErroNegocio(f"O quarto {quarto.numero} já está bloqueado de "
                              f"{formatar_data_hora(b.inicio)} a {formatar_data_hora(b.fim)} "
                              f"({b.motivo}).")

        reservas = regras.reservas_em_conflito(self.reserva_repo.listar_por_quarto(quarto_id),
                                               quarto_id, inicio, fim)
        if reservas:
            lista = "; ".join(f"{r.id:04d} ({formatar_data(r.data_entrada)} a "
                              f"{formatar_data(r.data_saida)})" for r in reservas[:3])
            raise ErroNegocio(f"O quarto {quarto.numero} tem reserva neste período: {lista}. "
                              "Cancele ou remarque a reserva antes de bloquear.")

        return self.repo.criar(BloqueioQuarto(
            quarto_id=quarto_id, inicio=inicio, fim=fim, motivo=motivo,
            usuario_id=Sessao.usuario.id, criado_em=_agora()))
