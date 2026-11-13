from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import CAIXA_ENTRADA, CAIXA_SAIDA, CAIXA_TODAS
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.periodos import ATALHOS_RELATORIO, ESTE_MES, PERSONALIZADO, periodo_do_atalho
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.janela_saldo_inicial import abrir_saldo_inicial
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte
from ui.telas.tela_base import TelaBase

COLUNAS = [("Data/hora", "data_hora", 120), ("Tipo", "tipo", 65), ("Origem", "origem", 85),
           ("Descrição", "descricao", 240), ("Responsável", "responsavel", 115),
           ("Valor", "valor", 100), ("Saldo", "saldo", 100)]
TIPOS = [CAIXA_TODAS, CAIXA_ENTRADA, CAIXA_SAIDA]


class TelaCaixa(TelaBase):
    titulo = "Caixa"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self.corpo, "Período")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="filtro")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Data inicial", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Data final", self._ao_digitar_periodo)
        self.tipo = CampoSelecao(linha, "Movimentações", TIPOS, self.atualizar)
        for coluna, campo in enumerate((self.atalho, self.inicio, self.fim, self.tipo)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 8, 0 if coluna == 3 else 8))
        if Sessao.pode("caixa.configurar"):
            botao_secundario(linha, "Saldo inicial...", self.configurar_saldo, 150
                             ).grid(row=0, column=4, sticky="s", padx=(16, 0))

        cartoes = ctk.CTkFrame(self.corpo, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        nomes = ["Saldo no início do período", "Entradas", "Saídas", "Saldo final"]
        for i, nome in enumerate(nomes):
            cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(cartoes, nome, "—")
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.cartoes[nome] = cartao

        historico = Cartao(self.corpo, "Histórico de movimentações")
        historico.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_info = ctk.CTkLabel(historico, text="", font=fonte(12), anchor="w",
                                     justify="left", text_color=COR_TEXTO_SUAVE, wraplength=880)
        self.lbl_info.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.tabela = Tabela(historico, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.atalho.definir(ESTE_MES)
        self.tipo.definir(CAIXA_TODAS)
        self._definir_datas(*periodo_do_atalho(ESTE_MES))

    def _definir_datas(self, inicio, fim):
        self.inicio.definir(formatar_data(inicio))
        self.fim.definir(formatar_data(fim))

    def ao_exibir(self):
        self.atualizar(silencioso=True)

    def _ao_digitar_periodo(self):
        self.atalho.definir(PERSONALIZADO)
        if len(self.inicio.valor()) == 10 and len(self.fim.valor()) == 10:
            self.atualizar(silencioso=True)

    def _ao_escolher_atalho(self):
        atalho = self.atalho.valor()
        if atalho != PERSONALIZADO:
            self._definir_datas(*periodo_do_atalho(atalho))
            self.atualizar()

    def configurar_saldo(self):
        abrir_saldo_inicial(self, self.servicos, ao_atualizar=self.atualizar)

    def atualizar(self, silencioso=False):
        inicio, fim = self.inicio.data(), self.fim.data()
        try:
            if inicio is None or fim is None:
                raise ErroNegocio("Informe o período no formato dd/mm/aaaa.")
            resumo = self.servicos.caixa.resumo(inicio, fim)
            movimentos = self.servicos.caixa.movimentacoes(inicio, fim, self.tipo.valor())
            saldo = self.servicos.caixa.saldo_inicial()
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Período inválido", str(erro))
            return

        self.cartoes["Saldo no início do período"].atualizar(formatar_moeda(resumo.saldo_inicial))
        self.cartoes["Entradas"].atualizar(formatar_moeda(resumo.entradas), VERDE)
        self.cartoes["Saídas"].atualizar(formatar_moeda(resumo.saidas), VERMELHO)
        self.cartoes["Saldo final"].atualizar(
            formatar_moeda(resumo.saldo_final), VERMELHO if resumo.saldo_final < 0 else COR_TEXTO)
        self.tabela.carregar(self.servicos.linhas_caixa(movimentos))

        if saldo is None:
            texto = ("O saldo inicial ainda não foi definido: o caixa começa em zero e conta todo "
                     "o histórico de pagamentos, reembolsos e despesas.")
        else:
            texto = (f"Saldo inicial: {formatar_moeda(saldo.valor)} desde "
                     f"{formatar_data(saldo.data_referencia)}. "
                     "O caixa conta só o que aconteceu a partir dessa data.")
        if resumo.antes_do_caixa:
            texto = "Este período é anterior à data do saldo inicial, então não há saldo. " + texto
        else:
            texto = (f"Saídas = reembolsos ({formatar_moeda(resumo.saidas_reembolsos)}) + "
                     f"despesas ({formatar_moeda(resumo.saidas_despesas)}). " + texto)
        self.lbl_info.configure(text=texto)
