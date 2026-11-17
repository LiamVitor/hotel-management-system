from src.models.demonstrativo import Demonstrativo
from src.services import demonstrativo_regras as regras
from src.services.caixa_service import CaixaService
from src.services.erros import ErroNegocio
from src.services.pagamento_regras import arredondar
from src.services.relatorios import escolher_granularidade
from src.utils.constantes import (CAIXA_TODAS, ORIGEM_DESPESA, ORIGEM_PAGAMENTO,
                                  ORIGEM_REEMBOLSO)
from src.utils.sessao import Sessao

ORIGENS = (CAIXA_TODAS, ORIGEM_PAGAMENTO, ORIGEM_REEMBOLSO, ORIGEM_DESPESA)


class DemonstrativoFinanceiroService:
    """Demonstrativo financeiro e fluxo de caixa de um período.

    Usa o caixa como fonte única: saldo inicial, entradas (pagamentos), saídas (reembolsos e
    despesas) e saldo final vêm de CaixaService, então o demonstrativo sempre fecha com a tela
    de Caixa.
    """

    def __init__(self, caixa=None):
        self.caixa = caixa or CaixaService()

    def demonstrativo(self, inicio, fim, origem=CAIXA_TODAS):
        """Fecha o período: saldo inicial, entradas, despesas, reembolsos e saldo final.

        Traz também o fluxo de caixa (agrupado por dia, semana ou mês conforme o tamanho do
        período) e as movimentações em ordem cronológica, cada uma com o saldo depois dela.
        origem: Todas, Pagamento, Reembolso ou Despesa; filtra só a lista de movimentações
        (o fechamento e o fluxo são sempre do caixa inteiro).
        """
        Sessao.exigir("relatorios.ver")
        if origem not in ORIGENS:
            raise ErroNegocio("Tipo de movimentação inválido.")
        resumo = self.caixa.resumo(inicio, fim)          # valida o período
        movimentos = self.caixa.movimentacoes(inicio, fim)
        granularidade = escolher_granularidade((fim - inicio).days + 1)
        fluxo = regras.agrupar_fluxo(movimentos, inicio, fim, resumo.saldo_inicial, granularidade)
        if origem != CAIXA_TODAS:
            movimentos = [m for m in movimentos if m.origem == origem]
        return Demonstrativo(
            resumo=resumo, variacao=arredondar(resumo.saldo_final - resumo.saldo_inicial),
            granularidade=granularidade, fluxo=fluxo, movimentacoes=movimentos)
