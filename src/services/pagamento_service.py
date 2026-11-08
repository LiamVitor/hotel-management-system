import math
from datetime import datetime

from src.models.pagamento import Pagamento
from src.repositories.pagamento_repository import PagamentoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import pagamento_regras as regras
from src.services.erros import ErroNegocio
from src.utils.constantes import (FORMAS_PAGAMENTO, MOTIVO_REEMBOLSO_MAX, MOTIVO_REEMBOLSO_MIN,
                                  PAGAMENTO_NORMAL, PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA)
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao


class PagamentoService:
    def __init__(self, repo=None, reserva_repo=None, usuario_repo=None):
        self.repo = repo or PagamentoRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    # ---------- consultas ----------
    def listar_por_reserva(self, reserva_id):
        """Histórico financeiro da reserva (pagamentos e reembolsos), do mais antigo ao mais recente."""
        return self.repo.listar_por_reserva(reserva_id)

    def historico(self, reserva_id):
        """Lista de (Pagamento, nome de quem lançou), do mais antigo para o mais recente.

        Inclui os reembolsos. O nome é buscado direto no repositório de usuários porque
        listar usuários é restrito ao administrador, mas qualquer perfil precisa ver quem lançou.
        """
        nomes = {}
        resultado = []
        for pagamento in self.repo.listar_por_reserva(reserva_id):
            if pagamento.usuario_id not in nomes:
                usuario = self.usuario_repo.buscar_por_id(pagamento.usuario_id)
                nomes[pagamento.usuario_id] = usuario.nome if usuario else None
            resultado.append((pagamento, nomes[pagamento.usuario_id]))
        return resultado

    def resumo(self, reserva_id):
        """Total, quanto ficou pago (já sem os reembolsos), saldo pendente e situação."""
        reserva = self._obter_reserva(reserva_id)
        return regras.resumir(reserva.valor_total, self.repo.listar_por_reserva(reserva_id),
                              cancelada=reserva.situacao == RESERVA_CANCELADA)

    def reembolsaveis(self, reserva_id):
        """[(Pagamento, quanto ainda pode ser reembolsado)] dos pagamentos que ainda têm valor a devolver."""
        lancamentos = self.repo.listar_por_reserva(reserva_id)
        restante = regras.reembolsavel_por_pagamento(lancamentos)
        return [(p, restante[p.id]) for p in lancamentos
                if p.tipo == PAGAMENTO_NORMAL and restante[p.id] > 0]

    def totais_por_reserva(self):
        """{reserva_id: total pago já sem reembolsos} de todas as reservas, em uma consulta só."""
        return self.repo.totais_por_reserva()

    # ---------- lançamentos ----------
    def registrar(self, reserva_id, valor, forma, data_hora=None):
        """Lança um pagamento (parcial ou integral) em uma reserva.

        O responsável é sempre o usuário logado e a data/hora é a do momento do
        lançamento. O valor não pode passar do saldo pendente.
        """
        Sessao.exigir("pagamentos.registrar")
        reserva = self._obter_reserva(reserva_id)
        if reserva.situacao == RESERVA_CANCELADA:
            raise ErroNegocio("Não é possível registrar pagamento em uma reserva cancelada.")

        valor = self._validar_valor(valor, "pagamento")
        self._validar_forma(forma)

        saldo = self.resumo(reserva_id).saldo
        if saldo <= 0:
            raise ErroNegocio("Esta reserva já está quitada.")
        if valor > saldo:
            raise ErroNegocio(f"O valor excede o saldo pendente de {formatar_moeda(saldo)}.")

        return self.repo.criar(Pagamento(
            reserva_id=reserva_id, valor=valor, forma=forma, tipo=PAGAMENTO_NORMAL,
            usuario_id=Sessao.usuario.id, data_hora=data_hora or datetime.now()))

    def registrar_reembolso(self, reserva_id, valor, forma, motivo,
                            pagamento_origem_id=None, data_hora=None):
        """Registra a devolução de um valor ao hóspede.

        O reembolso é um novo lançamento no histórico da reserva: o pagamento original
        nunca é alterado nem excluído. Pode ser vinculado a um pagamento específico
        (pagamento_origem_id) ou apenas à reserva. Exige motivo; o responsável é o usuário
        logado e a data/hora é a do lançamento.
        """
        Sessao.exigir("pagamentos.reembolsar")
        self._obter_reserva(reserva_id)

        valor = self._validar_valor(valor, "reembolso")
        self._validar_forma(forma, "do reembolso")
        motivo = (motivo or "").strip()
        if len(motivo) < MOTIVO_REEMBOLSO_MIN:
            raise ErroNegocio("Informe o motivo do reembolso.")
        if len(motivo) > MOTIVO_REEMBOLSO_MAX:
            raise ErroNegocio(f"O motivo deve ter no máximo {MOTIVO_REEMBOLSO_MAX} caracteres.")

        lancamentos = self.repo.listar_por_reserva(reserva_id)
        if pagamento_origem_id is not None:
            origem = next((p for p in lancamentos if p.id == pagamento_origem_id), None)
            if origem is None:
                raise ErroNegocio("O pagamento informado não pertence a esta reserva.")
            if origem.tipo != PAGAMENTO_NORMAL:
                raise ErroNegocio("Só é possível reembolsar um pagamento, não outro reembolso.")
            restante = regras.reembolsavel_por_pagamento(lancamentos)[origem.id]
            if restante <= 0:
                raise ErroNegocio("Este pagamento já foi totalmente reembolsado.")
            if valor > restante:
                raise ErroNegocio("O valor excede o que ainda pode ser reembolsado deste "
                                  f"pagamento ({formatar_moeda(restante)}).")
        pago = regras.total_pago(lancamentos)
        if pago <= 0:
            raise ErroNegocio("Esta reserva não tem valor pago para reembolsar.")
        if valor > pago:
            raise ErroNegocio(f"O valor excede o total pago da reserva ({formatar_moeda(pago)}).")

        return self.repo.criar(Pagamento(
            reserva_id=reserva_id, valor=valor, forma=forma, tipo=PAGAMENTO_REEMBOLSO,
            motivo=motivo, pagamento_origem_id=pagamento_origem_id,
            usuario_id=Sessao.usuario.id, data_hora=data_hora or datetime.now()))

    # ---------- internos ----------
    def _obter_reserva(self, reserva_id):
        reserva = self.reserva_repo.buscar_por_id(reserva_id)
        if reserva is None:
            raise ErroNegocio("Reserva não encontrada.")
        return reserva

    @staticmethod
    def _validar_valor(valor, o_que):
        try:
            valor = regras.arredondar(float(valor))
        except (TypeError, ValueError):
            raise ErroNegocio(f"Informe um valor válido para o {o_que}.")
        if not math.isfinite(valor) or valor <= 0:
            raise ErroNegocio(f"O valor do {o_que} deve ser maior que zero.")
        return valor

    @staticmethod
    def _validar_forma(forma, de_que="de pagamento"):
        if forma not in FORMAS_PAGAMENTO:
            raise ErroNegocio(f"Selecione a forma {de_que}.")
