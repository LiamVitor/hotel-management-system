from src.repositories.relatorio_reservas_repository import RelatorioReservasRepository
from src.services import relatorio_reservas_regras as regras
from src.services.cancelamentos_regras import filtrar_por_texto
from src.services.erros import ErroNegocio
from src.services.relatorios import validar_periodo
from src.utils.constantes import (FILTROS_MOVIMENTOS, FILTROS_RESERVAS, MOVIMENTO_TODOS,
                                  RESERVAS_TODAS)
from src.utils.sessao import Sessao


class RelatorioReservasService:
    """Relatório de reservas por período: as reservas que ENTRAM no período (data de entrada
    prevista), com hóspede, quarto, noites, valor total, valor pago e situação.

    É a mesma base do 'Valor reservado' da ocupação e do demonstrativo de receitas.
    """

    def __init__(self, repo=None):
        self.repo = repo or RelatorioReservasRepository()

    def listar(self, inicio, fim, situacao=RESERVAS_TODAS, termo=""):
        """Reservas com entrada de inicio a fim (inclusive), da mais antiga para a mais nova.

        situacao: Todas, Confirmada, Hospedada, Finalizada, Cancelada ou Não compareceu.
        termo: nome ou CPF do hóspede, número do quarto ou código da reserva.
        """
        Sessao.exigir("relatorios.ver")
        if inicio is None or fim is None:
            raise ErroNegocio("Informe o período no formato dd/mm/aaaa.")
        validar_periodo(inicio, fim)
        if situacao not in FILTROS_RESERVAS:
            raise ErroNegocio("Situação de reserva inválida.")
        reservas = self.repo.reservas_com_entrada_no_periodo(
            inicio, fim, None if situacao == RESERVAS_TODAS else situacao)
        return filtrar_por_texto(reservas, termo)

    def totais(self, reservas):
        Sessao.exigir("relatorios.ver")
        return regras.totalizar_reservas(reservas)


class RelatorioMovimentosService:
    """Relatório de check-ins e check-outs: o que realmente aconteceu no período, com a data e a
    hora reais, o dia previsto, como um se compara ao outro e quem registrou."""

    def __init__(self, repo=None):
        self.repo = repo or RelatorioReservasRepository()

    def listar(self, inicio, fim, tipo=MOVIMENTO_TODOS, termo=""):
        """Check-ins e check-outs de inicio a fim (inclusive), em ordem cronológica.

        tipo: Todos, Check-in ou Check-out. termo: hóspede, CPF, quarto ou código da reserva.
        """
        Sessao.exigir("relatorios.ver")
        if inicio is None or fim is None:
            raise ErroNegocio("Informe o período no formato dd/mm/aaaa.")
        validar_periodo(inicio, fim)
        if tipo not in FILTROS_MOVIMENTOS:
            raise ErroNegocio("Tipo de movimento inválido.")
        movimentos = self.repo.movimentos_no_periodo(
            inicio, fim, None if tipo == MOVIMENTO_TODOS else tipo)
        return filtrar_por_texto(movimentos, termo)

    def totais(self, movimentos):
        Sessao.exigir("relatorios.ver")
        return regras.totalizar_movimentos(movimentos)
