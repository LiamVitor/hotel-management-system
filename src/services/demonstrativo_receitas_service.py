from src.models.demonstrativo_receitas import DemonstrativoReceitas
from src.repositories.receita_repository import ReceitaRepository
from src.services import receitas_regras as regras
from src.services.relatorios import validar_periodo
from src.utils.sessao import Sessao


class DemonstrativoReceitasService:
    """Demonstrativo de receitas: separa o que foi reservado do que foi efetivamente recebido."""

    def __init__(self, repo=None):
        self.repo = repo or ReceitaRepository()

    def demonstrativo(self, inicio, fim):
        """Receitas de inicio a fim (inclusive), comparadas com o período anterior de mesmo tamanho.

        - Reservado: reservas ativas que entram no período (cancelamento e no-show ficam de fora).
        - Recebido: pagamentos − reembolsos pela data do lançamento (inclui o que ficou retido
          em cancelamentos e no-shows).
        As duas bases são diferentes de propósito: o reservado segue a estadia; o recebido, o caixa.
        """
        Sessao.exigir("relatorios.ver")
        validar_periodo(inicio, fim)
        ant_inicio, ant_fim = regras.periodo_anterior(inicio, fim)
        reservado = self.repo.reservado(inicio, fim)
        recebimentos = self.repo.recebimentos(inicio, fim)
        resumo = regras.resumir(reservado, recebimentos)
        anterior = regras.resumir(self.repo.reservado(ant_inicio, ant_fim),
                                  self.repo.recebimentos(ant_inicio, ant_fim))
        return DemonstrativoReceitas(
            inicio=inicio, fim=fim, anterior_inicio=ant_inicio, anterior_fim=ant_fim,
            resumo=resumo, anterior=anterior, comparacao=regras.comparar(resumo, anterior),
            por_forma=regras.por_forma(recebimentos),
            por_quarto=regras.por_quarto(reservado, recebimentos),
            por_dia=regras.por_dia(reservado, recebimentos, inicio, fim),
            por_mes=regras.por_mes(reservado, recebimentos, inicio, fim))
