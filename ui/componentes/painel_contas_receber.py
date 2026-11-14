"""Painel do relatório de contas a receber (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import CONTAS_EM_ABERTO, FILTROS_CONTAS
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.janela_vencimento import abrir_vencimento
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, fonte

COLUNAS = [("Reserva", "reserva", 70), ("Hóspede", "hospede", 180), ("Total", "total", 105),
           ("Pago", "pago", 105), ("Saldo pendente", "saldo", 120), ("Vencimento", "vencimento", 100),
           ("Situação", "situacao", 150)]


class PainelContasReceber(ctk.CTkFrame):
    def __init__(self, master, servicos):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos
        self._contas = {}          # reserva_id -> ContaReceber da lista na tela

        filtro = Cartao(self, "Contas a receber")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="filtro")
        self.situacao = CampoSelecao(linha, "Situação", FILTROS_CONTAS, self.atualizar)
        self.venc_de = CampoData(linha, "Vencimento de", self._ao_digitar)
        self.venc_ate = CampoData(linha, "Vencimento até", self._ao_digitar)
        self.busca = CampoTexto(linha, "Buscar", "Hóspede, CPF, quarto ou código",
                                ao_mudar=self._ao_digitar)
        for coluna, campo in enumerate((self.situacao, self.venc_de, self.venc_ate, self.busca)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 8, 0 if coluna == 3 else 8))

        cartoes = ctk.CTkFrame(self, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        for i, nome in enumerate(["Total a receber", "Vencido", "A vencer", "Reservas em aberto"]):
            cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(cartoes, nome, "—")
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.cartoes[nome] = cartao

        lista = Cartao(self)
        lista.pack(fill="both", expand=True, pady=(16, 0))
        rodape = ctk.CTkFrame(lista, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=20, pady=(0, 14))
        self.lbl_info = ctk.CTkLabel(
            rodape, anchor="w", justify="left", font=fonte(12), text_color=COR_TEXTO_SUAVE,
            wraplength=640, text="Saldo = valor total − pagamentos + reembolsos. Sem vencimento "
                                 "definido, vale a data de entrada. Selecione uma reserva para "
                                 "alterar o vencimento.")
        self.lbl_info.pack(side="left")
        if Sessao.pode("pagamentos.registrar"):
            botao_secundario(rodape, "Alterar vencimento", self._alterar_vencimento, 170
                             ).pack(side="right")
        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        self.situacao.definir(CONTAS_EM_ABERTO)

    def _ao_digitar(self):
        self.atualizar(silencioso=True)

    @staticmethod
    def _ler(campo):
        """Data do campo: None se vazio (sem limite); erro se estiver pela metade ou inválida."""
        if not campo.valor():
            return None
        data = campo.data()
        if data is None:
            raise ErroNegocio("Informe as datas no formato dd/mm/aaaa.")
        return data

    def atualizar(self, silencioso=False):
        try:
            contas = self.servicos.contas_receber.listar(
                self.situacao.valor() or CONTAS_EM_ABERTO,
                self._ler(self.venc_de), self._ler(self.venc_ate), self.busca.valor())
            totais = self.servicos.contas_receber.totais(contas)
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Filtro inválido", str(erro))
            return
        self._contas = {c.reserva_id: c for c in contas}
        self.cartoes["Total a receber"].atualizar(formatar_moeda(totais["total_a_receber"]))
        self.cartoes["Vencido"].atualizar(
            formatar_moeda(totais["total_vencido"]),
            VERMELHO if totais["total_vencido"] > 0 else COR_TEXTO)
        self.cartoes["A vencer"].atualizar(formatar_moeda(totais["total_a_vencer"]))
        self.cartoes["Reservas em aberto"].atualizar(totais["qtd_em_aberto"])
        self.tabela.carregar(self.servicos.linhas_contas_receber(contas))

    def _alterar_vencimento(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Alterar vencimento", "Selecione uma reserva na lista.")
            return
        abrir_vencimento(self, self.servicos, self._contas[linha["id"]],
                         ao_atualizar=self.atualizar)
