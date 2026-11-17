from datetime import date, datetime, timedelta

from src.repositories.conta_receber_repository import ContaReceberRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services import contas_receber_regras as regras
from src.services.erros import ErroNegocio
from src.services.relatorios import validar_periodo
from src.utils.constantes import (CONTAS_EM_ABERTO, FILTROS_CONTAS, RESERVA_CANCELADA,
                                  RESERVA_NO_SHOW, VENCIMENTO_MAX_DIAS_APOS_SAIDA)
from src.utils.formatacao import formatar_data
from src.utils.sessao import Sessao


def _agora():
    """Hora atual sem microssegundos, igual ao que o banco guarda."""
    return datetime.now().replace(microsecond=0)


class ContaReceberService:
    """Relatório de contas a receber: o que cada hóspede ainda precisa pagar.

    Cada reserva (que não foi cancelada nem virou no-show) é uma conta: valor total, valor já
    pago (pagamentos menos reembolsos), saldo pendente, vencimento e situação financeira.
    """

    def __init__(self, repo=None, reserva_repo=None):
        self.repo = repo or ContaReceberRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()

    def listar(self, filtro=CONTAS_EM_ABERTO, vencimento_de=None, vencimento_ate=None, termo=""):
        """Contas filtradas por situação, período de vencimento e texto (vencimento mais antigo primeiro).

        filtro: Em aberto, Vencidas, A vencer, Quitadas ou Todas.
        vencimento_de / vencimento_ate: datas (inclusive), cada uma opcional.
        termo: nome ou CPF do hóspede, número do quarto ou código da reserva.
        """
        Sessao.exigir("relatorios.ver")
        if filtro not in FILTROS_CONTAS:
            raise ErroNegocio("Filtro de situação inválido.")
        if vencimento_de and vencimento_ate:
            validar_periodo(vencimento_de, vencimento_ate)
        hoje = date.today()
        contas = [regras.calcular(c, hoje)
                  for c in self.repo.listar(vencimento_de, vencimento_ate)]
        return regras.filtrar(contas, filtro, termo)

    def totais(self, contas):
        """Somas da lista de contas (total a receber, vencido, a vencer, quantidades...)."""
        Sessao.exigir("relatorios.ver")
        return regras.totalizar(contas)

    def definir_vencimento(self, reserva_id, data_vencimento):
        """Registra a data de vencimento da reserva (quem e quando ficam gravados).

        Não vale para reserva cancelada ou de no-show. A data não pode ser anterior ao dia em
        que a reserva foi lançada nem passar de um ano depois da saída.
        """
        Sessao.exigir("pagamentos.registrar")
        if not isinstance(data_vencimento, date) or isinstance(data_vencimento, datetime):
            raise ErroNegocio("Informe a data de vencimento.")
        reserva = self.reserva_repo.buscar_por_id(reserva_id)
        if reserva is None:
            raise ErroNegocio("Reserva não encontrada.")
        if reserva.situacao in (RESERVA_CANCELADA, RESERVA_NO_SHOW):
            raise ErroNegocio("Reserva cancelada ou sem comparecimento não tem conta a receber.")
        if reserva.criada_em is not None and data_vencimento < reserva.criada_em.date():
            raise ErroNegocio("O vencimento não pode ser anterior à criação da reserva "
                              f"({formatar_data(reserva.criada_em.date())}).")
        limite = reserva.data_saida + timedelta(days=VENCIMENTO_MAX_DIAS_APOS_SAIDA)
        if data_vencimento > limite:
            raise ErroNegocio("O vencimento não pode passar de um ano depois da saída "
                              f"({formatar_data(limite)}).")
        if not self.reserva_repo.registrar_vencimento(
                reserva_id, data_vencimento, _agora(), Sessao.usuario.id):
            raise ErroNegocio("A situação da reserva mudou. Atualize a tela e tente de novo.")
        return self.reserva_repo.buscar_por_id(reserva_id)
