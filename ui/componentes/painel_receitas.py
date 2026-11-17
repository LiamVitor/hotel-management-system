"""Painel do demonstrativo de receitas: reservado x recebido (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import REL_RECEITAS
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.periodos import ATALHOS_RELATORIO, ESTE_MES, PERSONALIZADO, periodo_do_atalho
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao
from ui.componentes.cartao import Cartao
from ui.componentes.painel_relatorio import PainelRelatorio
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COMPARACAO = "Comparação com o período anterior"
FORMA = "Forma de pagamento"
QUARTO = "Quarto"
DIARIO = "Diário"
MENSAL = "Mensal"
VISOES = [COMPARACAO, FORMA, QUARTO, DIARIO, MENSAL]
CARTOES = ["Valor reservado", "Receita recebida", "Reembolsos", "A receber das reservas"]

_COLUNAS_PERIODO = [("Período", "periodo", 130), ("Reservado", "reservado", 150),
                    ("Recebido", "bruto", 150), ("Reembolsos", "reembolsado", 150),
                    ("Receita líquida", "recebido", 160)]
COLUNAS = {
    COMPARACAO: [("Indicador", "indicador", 260), ("Período atual", "atual", 140),
                 ("Período anterior", "anterior", 140), ("Variação", "variacao", 140),
                 ("Variação %", "percentual", 100)],
    FORMA: [("Forma de pagamento", "forma", 200), ("Pagamentos", "qtd", 100),
            ("Recebido", "bruto", 130), ("Reembolsos", "reembolsado", 130),
            ("Receita líquida", "recebido", 140), ("% do total", "percentual", 90)],
    QUARTO: [("Quarto", "numero", 80), ("Tipo", "tipo", 110), ("Reservas", "qtd", 80),
             ("Reservado", "reservado", 120), ("Receita líquida", "recebido", 125),
             ("Reembolsos", "reembolsado", 115), ("A receber", "a_receber", 115)],
    DIARIO: _COLUNAS_PERIODO,
    MENSAL: _COLUNAS_PERIODO,
}


class PainelReceitas(PainelRelatorio):
    TITULO = "Demonstrativo de receitas"
    CHAVE = REL_RECEITAS

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self, "Filtros")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="filtro")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Data inicial", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Data final", self._ao_digitar_periodo)
        self.visao = CampoSelecao(linha, "Detalhar por", VISOES, self._trocar_visao)
        for coluna, campo in enumerate((self.atalho, self.inicio, self.fim, self.visao)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 8, 0 if coluna == 3 else 8))

        self.cartoes = self.criar_indicadores(CARTOES)

        lista = Cartao(self)
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_info = ctk.CTkLabel(lista, text="", font=fonte(12), anchor="w", justify="left",
                                     text_color=COR_TEXTO_SUAVE, wraplength=880)
        self.lbl_info.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.registrar_nota(self.lbl_info)
        self.tabelas = {v: Tabela(lista, COLUNAS[v], altura=130) for v in VISOES}
        for v in VISOES:
            self.registrar_tabela(v, self.tabelas[v])
        self._visivel = None

        self.atalho.definir(ESTE_MES)
        self.visao.definir(COMPARACAO)
        self._definir_datas(*periodo_do_atalho(ESTE_MES))
        self._trocar_visao()

    # ---------- período ----------
    def _definir_datas(self, inicio, fim):
        self.inicio.definir(formatar_data(inicio))
        self.fim.definir(formatar_data(fim))

    def _ao_digitar_periodo(self):
        self.atalho.definir(PERSONALIZADO)
        if len(self.inicio.valor()) == 10 and len(self.fim.valor()) == 10:
            self.atualizar(silencioso=True)

    def _ao_escolher_atalho(self):
        atalho = self.atalho.valor()
        if atalho != PERSONALIZADO:
            self._definir_datas(*periodo_do_atalho(atalho))
            self.atualizar()

    def _trocar_visao(self):
        """Mostra a tabela da visão escolhida, no mesmo lugar."""
        escolhida = self.visao.valor() or COMPARACAO
        if self._visivel is not None:
            self._visivel.pack_forget()
        self._visivel = self.tabelas[escolhida]
        self._visivel.pack(fill="both", expand=True, padx=20, pady=(16, 8))
        self.atualizar(silencioso=True)

    # ---------- dados ----------
    def atualizar(self, silencioso=False):
        inicio, fim = self.inicio.data(), self.fim.data()
        try:
            if inicio is None or fim is None:
                raise ErroNegocio("Informe o período no formato dd/mm/aaaa.")
            dem = self.servicos.receitas.demonstrativo(inicio, fim)
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Período inválido", str(erro))
            return

        self.marcar_emissao(inicio, fim)
        r = dem.resumo
        self.cartoes["Valor reservado"].atualizar(formatar_moeda(r.reservado))
        self.cartoes["Receita recebida"].atualizar(formatar_moeda(r.recebido), VERDE)
        self.cartoes["Reembolsos"].atualizar(
            formatar_moeda(r.reembolsado), VERMELHO if r.reembolsado > 0 else None)
        self.cartoes["A receber das reservas"].atualizar(formatar_moeda(r.a_receber))

        s = self.servicos
        self.tabelas[COMPARACAO].carregar(s.linhas_receitas_comparacao(dem.comparacao))
        self.tabelas[FORMA].carregar(s.linhas_receitas_forma(dem.por_forma))
        self.tabelas[QUARTO].carregar(s.linhas_receitas_quarto(dem.por_quarto))
        self.tabelas[DIARIO].carregar(s.linhas_receitas_periodo(dem.por_dia))
        self.tabelas[MENSAL].carregar(s.linhas_receitas_periodo(dem.por_mes, mensal=True))

        texto = ("Reservado = valor total das reservas que entram no período (sem cancelamentos "
                 "e no-shows). Receita recebida = pagamentos − reembolsos pela data do "
                 "pagamento, inclusive o que ficou retido em cancelamentos; por isso as duas "
                 "colunas não precisam bater. ")
        texto += (f"Período anterior comparado: {formatar_data(dem.anterior_inicio)} a "
                  f"{formatar_data(dem.anterior_fim)}.")
        if self.visao.valor() == DIARIO and len(dem.por_dia) < (dem.fim - dem.inicio).days + 1:
            texto += " Período longo: o detalhamento diário mostra só os dias com movimento."
        self.lbl_info.configure(text=texto)
