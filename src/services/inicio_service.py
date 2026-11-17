from datetime import date, timedelta

from src.models.inicio import FinanceiroInicio, ResumoInicio
from src.services import inicio_regras as regras
from src.services.bloqueio_quarto_service import BloqueioQuartoService
from src.services.caixa_service import CaixaService
from src.services.conta_receber_service import ContaReceberService
from src.services.erros import ErroPermissao
from src.services.quarto_service import QuartoService
from src.services.relatorios import relatorio_periodo
from src.services.reserva_service import ReservaService
from src.utils.constantes import (BLOQUEIO_EM_ANDAMENTO, CONTAS_EM_ABERTO, DIAS_OCUPACAO_INICIO,
                                  LIMITE_CONTAS_INICIO)
from src.utils.sessao import Sessao


class InicioService:
    """Monta o resumo da tela inicial reunindo o que os outros services já sabem.

    Não repete regra de ninguém: ocupação vem de `relatorios`, caixa de `CaixaService` e
    contas a receber de `ContaReceberService`. A parte financeira só vem para quem tem
    permissão (caixa.ver / relatorios.ver); para os outros perfis ela fica vazia.
    """

    def __init__(self, quartos=None, reservas=None, bloqueios=None, caixa=None, contas=None):
        self.quartos = quartos or QuartoService()
        self.reservas = reservas or ReservaService()
        self.bloqueios = bloqueios or BloqueioQuartoService()
        self.caixa = caixa or CaixaService()
        self.contas = contas or ContaReceberService()

    def resumo(self, hoje=None):
        hoje = hoje or date.today()
        fim = hoje + timedelta(days=DIAS_OCUPACAO_INICIO - 1)
        quartos = self.quartos.listar()
        reservas = self.reservas.listar()

        bloqueios = self._bloqueios(hoje, fim)
        em_andamento = {b.quarto_id for b in bloqueios if self.bloqueios.situacao(b) == BLOQUEIO_EM_ANDAMENTO}
        previsao = relatorio_periodo(self.reservas.listar_para_relatorio(hoje, fim),
                                     quartos, hoje, fim, bloqueios)

        financeiro, caixa_sem_saldo = self._financeiro(hoje)
        totais = financeiro.totais_contas if financeiro else None
        return ResumoInicio(
            hoje=hoje,
            indicadores=regras.indicadores(quartos, reservas, hoje),
            reservas_hoje=regras.reservas_do_dia(reservas, hoje),
            ocupacao_prevista=previsao["barras"],
            situacao_quartos=regras.contar_situacoes(quartos),
            alertas=regras.alertas(reservas, quartos, em_andamento, hoje, totais, caixa_sem_saldo),
            financeiro=financeiro,
        )

    def _bloqueios(self, inicio, fim):
        """Bloqueios que tocam o período; sem permissão para vê-los, a lista vem vazia."""
        try:
            return self.bloqueios.historico(periodo_de=inicio, periodo_ate=fim)
        except ErroPermissao:
            return []

    def _financeiro(self, hoje):
        """(FinanceiroInicio ou None, caixa sem saldo inicial?) conforme as permissões."""
        financeiro = FinanceiroInicio()
        caixa_sem_saldo = False
        if Sessao.pode("caixa.ver"):
            financeiro.caixa = self.caixa.resumo(hoje.replace(day=1), hoje)
            caixa_sem_saldo = self.caixa.saldo_inicial() is None
        if Sessao.pode("relatorios.ver"):
            contas = self.contas.listar(CONTAS_EM_ABERTO)
            financeiro.totais_contas = self.contas.totais(contas)
            financeiro.contas_abertas = contas[:LIMITE_CONTAS_INICIO]
        if financeiro.caixa is None and financeiro.totais_contas is None:
            return None, False
        return financeiro, caixa_sem_saldo
