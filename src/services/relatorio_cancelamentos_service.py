from src.repositories.cancelamento_repository import CancelamentoRepository
from src.services import cancelamentos_regras as regras
from src.services.erros import ErroNegocio
from src.services.relatorios import validar_periodo
from src.utils.constantes import (FILTROS_CANCELAMENTOS, RELATORIO_CANC_CANCELAMENTOS,
                                  RELATORIO_CANC_NO_SHOWS, RELATORIO_CANC_TODOS,
                                  RESERVA_CANCELADA, RESERVA_NO_SHOW)
from src.utils.sessao import Sessao

_SITUACAO_DO_FILTRO = {RELATORIO_CANC_TODOS: None, RELATORIO_CANC_CANCELAMENTOS: RESERVA_CANCELADA,
                       RELATORIO_CANC_NO_SHOWS: RESERVA_NO_SHOW}


class RelatorioCancelamentosService:
    """Relatório de reservas canceladas e de hóspedes que não compareceram (no-show).

    Cada linha traz hóspede, código, criação da reserva, entrada prevista, data e motivo do
    cancelamento (ou a data do no-show) e os valores: pago, retido pela regra da administração,
    reembolsado e ainda a reembolsar.
    """

    def __init__(self, repo=None):
        self.repo = repo or CancelamentoRepository()

    def listar(self, tipo=RELATORIO_CANC_TODOS, evento_de=None, evento_ate=None, termo=""):
        """Registros mais recentes primeiro.

        tipo: Todos, Cancelamentos ou No-shows. evento_de / evento_ate: período em que o
        cancelamento ou no-show aconteceu (datas inclusive, cada uma opcional).
        termo: nome ou CPF do hóspede, número do quarto ou código da reserva.
        """
        Sessao.exigir("relatorios.ver")
        if tipo not in FILTROS_CANCELAMENTOS:
            raise ErroNegocio("Tipo de registro inválido.")
        if evento_de and evento_ate:
            validar_periodo(evento_de, evento_ate)
        registros = [regras.calcular(r) for r in
                     self.repo.listar(_SITUACAO_DO_FILTRO[tipo], evento_de, evento_ate)]
        return regras.filtrar_por_texto(registros, termo)

    def totais(self, registros):
        """Quantidades e somas (pago, retido, reembolsado, a reembolsar) da lista."""
        Sessao.exigir("relatorios.ver")
        return regras.totalizar(registros)
