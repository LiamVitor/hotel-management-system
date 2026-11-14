"""Painel do demonstrativo financeiro e fluxo de caixa (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import (CAIXA_TODAS, GRANULARIDADE_DIA, GRANULARIDADE_MES,
                                  ORIGEM_DESPESA, ORIGEM_PAGAMENTO, ORIGEM_REEMBOLSO)
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.periodos import ATALHOS_RELATORIO, ESTE_MES, PERSONALIZADO, periodo_do_atalho
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

HISTORICO = "Histórico de movimentações"
FLUXO = "Fluxo de caixa"
VISOES = [HISTORICO, FLUXO]
ORIGENS = {"Todas": CAIXA_TODAS, "Entradas (pagamentos)": ORIGEM_PAGAMENTO,
           "Reembolsos": ORIGEM_REEMBOLSO, "Despesas": ORIGEM_DESPESA}
CARTOES = ["Saldo inicial", "Entradas", "Despesas", "Reembolsos", "Saldo final"]

LIMITE_LINHAS = 300   # um período longo pode ter milhares de movimentações; a tela mostra as últimas

COLUNAS_HISTORICO = [("Data/hora", "data_hora", 120), ("Origem", "origem", 85),
                     ("Descrição", "descricao", 290), ("Responsável", "responsavel", 115),
                     ("Valor", "valor", 100), ("Saldo", "saldo", 100)]
COLUNAS_FLUXO = [("Período", "periodo", 170), ("Entradas", "entradas", 120),
                 ("Despesas", "despesas", 120), ("Reembolsos", "reembolsos", 120),
                 ("Variação", "variacao", 120), ("Saldo final", "saldo", 130)]
NOME_GRUPO = {GRANULARIDADE_DIA: "dia", GRANULARIDADE_MES: "mês"}


class PainelDemonstrativo(ctk.CTkFrame):
    def __init__(self, master, servicos):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos

        filtro = Cartao(self, "Demonstrativo financeiro")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="filtro")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Data inicial", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Data final", self._ao_digitar_periodo)
        self.visao = CampoSelecao(linha, "Visualizar", VISOES, self._trocar_visao)
        self.origem = CampoSelecao(linha, "Movimentações", list(ORIGENS), self.atualizar)
        for coluna, campo in enumerate((self.atalho, self.inicio, self.fim, self.visao,
                                        self.origem)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 6, 0 if coluna == 4 else 6))

        cartoes = ctk.CTkFrame(self, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        for i, nome in enumerate(CARTOES):
            cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(cartoes, nome, "—", tamanho_valor=21)
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 6, 0 if i == len(CARTOES) - 1 else 6))
            self.cartoes[nome] = cartao

        lista = Cartao(self)
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_info = ctk.CTkLabel(lista, text="", font=fonte(12), anchor="w", justify="left",
                                     text_color=COR_TEXTO_SUAVE, wraplength=880)
        self.lbl_info.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.tabela_historico = Tabela(lista, COLUNAS_HISTORICO, altura=130)
        self.tabela_fluxo = Tabela(lista, COLUNAS_FLUXO, altura=130)

        self.atalho.definir(ESTE_MES)
        self.visao.definir(HISTORICO)
        self.origem.definir("Todas")
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
        """Mostra o histórico detalhado ou o fluxo de caixa, no mesmo lugar."""
        mostrar, esconder = ((self.tabela_historico, self.tabela_fluxo)
                             if self.visao.valor() != FLUXO
                             else (self.tabela_fluxo, self.tabela_historico))
        esconder.pack_forget()
        mostrar.pack(fill="both", expand=True, padx=20, pady=(16, 8))
        self.atualizar(silencioso=True)

    # ---------- dados ----------
    def atualizar(self, silencioso=False):
        inicio, fim = self.inicio.data(), self.fim.data()
        try:
            if inicio is None or fim is None:
                raise ErroNegocio("Informe o período no formato dd/mm/aaaa.")
            dem = self.servicos.demonstrativo.demonstrativo(
                inicio, fim, ORIGENS.get(self.origem.valor(), CAIXA_TODAS))
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Período inválido", str(erro))
            return

        r = dem.resumo
        self.cartoes["Saldo inicial"].atualizar(formatar_moeda(r.saldo_inicial))
        self.cartoes["Entradas"].atualizar(formatar_moeda(r.entradas_pagamentos), VERDE)
        self.cartoes["Despesas"].atualizar(formatar_moeda(r.saidas_despesas), VERMELHO)
        self.cartoes["Reembolsos"].atualizar(formatar_moeda(r.saidas_reembolsos), VERMELHO)
        self.cartoes["Saldo final"].atualizar(
            formatar_moeda(r.saldo_final), VERMELHO if r.saldo_final < 0 else COR_TEXTO)

        movimentos = dem.movimentacoes
        self.tabela_historico.carregar(
            self.servicos.linhas_caixa(movimentos[-LIMITE_LINHAS:]))
        self.tabela_fluxo.carregar(
            self.servicos.linhas_fluxo_caixa(dem.fluxo, dem.granularidade))

        sinal = "+" if dem.variacao >= 0 else "−"
        texto = (f"Saldo final = saldo inicial {formatar_moeda(r.saldo_inicial)} + entradas "
                 f"{formatar_moeda(r.entradas)} − despesas {formatar_moeda(r.saidas_despesas)} − "
                 f"reembolsos {formatar_moeda(r.saidas_reembolsos)} "
                 f"(variação do período: {sinal} {formatar_moeda(abs(dem.variacao))}). ")
        if r.antes_do_caixa:
            texto = ("Este período é anterior à data do saldo inicial do caixa, então não há "
                     "saldo nem movimentações. ")
        elif self.visao.valor() == FLUXO:
            texto += (f"Fluxo agrupado por {NOME_GRUPO.get(dem.granularidade, 'semana')}; "
                      "os grupos de uma linha só mostram o que aconteceu naquele intervalo.")
        elif len(movimentos) > LIMITE_LINHAS:
            texto += (f"Mostrando as {LIMITE_LINHAS} últimas de {len(movimentos)} movimentações; "
                      "reduza o período para ver as anteriores.")
        self.lbl_info.configure(text=texto)
