"""Painel do relatório de reservas por período (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import FILTROS_RESERVAS, REL_RESERVAS, RESERVAS_TODAS
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.periodos import ATALHOS_RELATORIO, ESTE_MES, PERSONALIZADO, periodo_do_atalho
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.painel_relatorio import PainelRelatorio
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, fonte

COLUNAS = [("Reserva", "reserva", 60), ("Hóspede", "hospede", 150), ("Quarto", "quarto", 60),
           ("Entrada", "entrada", 80), ("Saída", "saida", 80), ("Noites", "noites", 55),
           ("Total", "total", 90), ("Pago", "pago", 90), ("Situação", "situacao", 100)]
CARTOES = [["Reservas", "Valor reservado", "Noites reservadas", "Valor pago"],
           ["Canceladas", "Não compareceram"]]


class PainelReservasPeriodo(PainelRelatorio):
    TITULO = "Reservas por período"
    ROTULO_PERIODO = "Entrada"
    CHAVE = REL_RESERVAS

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self, "Filtros")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="filtro")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Entrada de", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Entrada até", self._ao_digitar_periodo)
        self.situacao = CampoSelecao(linha, "Situação", FILTROS_RESERVAS, self.atualizar)
        self.busca = CampoTexto(linha, "Buscar", "Hóspede, CPF, quarto ou código",
                                ao_mudar=self._ao_digitar)
        for coluna, campo in enumerate((self.atalho, self.inicio, self.fim, self.situacao,
                                        self.busca)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 6, 0 if coluna == 4 else 6))

        self.cartoes = self.criar_indicadores(CARTOES)

        lista = Cartao(self)
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_info = ctk.CTkLabel(
            lista, anchor="w", justify="left", font=fonte(12), text_color=COR_TEXTO_SUAVE,
            wraplength=880,
            text="Reservas com data de entrada prevista dentro do período, de qualquer "
                 "situação (use o filtro Situação). Valor reservado e noites não contam "
                 "canceladas nem no-shows. Valor pago = pagamentos − reembolsos. Duplo clique "
                 "em uma linha abre os detalhes da reserva.")
        self.lbl_info.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.registrar_nota(self.lbl_info)
        self.tabela = Tabela(lista, COLUNAS, altura=150,
                             ao_duplo_clique=lambda l: abrir_detalhes(self, self.servicos, l["id"]))
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(16, 8))
        self.registrar_tabela("Reservas por período", self.tabela)

        self.atalho.definir(ESTE_MES)
        self.situacao.definir(RESERVAS_TODAS)
        inicio, fim = periodo_do_atalho(ESTE_MES)
        self.inicio.definir(formatar_data(inicio))
        self.fim.definir(formatar_data(fim))
        self.atualizar(silencioso=True)

    def _ao_digitar(self):
        self.atualizar(silencioso=True)

    def _ao_digitar_periodo(self):
        self.atalho.definir(PERSONALIZADO)
        if len(self.inicio.valor()) == 10 and len(self.fim.valor()) == 10:
            self.atualizar(silencioso=True)

    def _ao_escolher_atalho(self):
        atalho = self.atalho.valor()
        if atalho != PERSONALIZADO:
            inicio, fim = periodo_do_atalho(atalho)
            self.inicio.definir(formatar_data(inicio))
            self.fim.definir(formatar_data(fim))
            self.atualizar()

    def atualizar(self, silencioso=False):
        inicio, fim = self.inicio.data(), self.fim.data()
        situacao = self.situacao.valor() or RESERVAS_TODAS
        try:
            reservas = self.servicos.relatorio_reservas.listar(inicio, fim, situacao,
                                                              self.busca.valor())
            totais = self.servicos.relatorio_reservas.totais(reservas)
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Filtro inválido", str(erro))
            return
        self.marcar_emissao(inicio, fim)
        self.definir_filtros([("Situação", situacao), ("Busca", self.busca.valor())])
        self.cartoes["Reservas"].atualizar(totais["reservas"])
        self.cartoes["Valor reservado"].atualizar(formatar_moeda(totais["valor_reservado"]))
        self.cartoes["Noites reservadas"].atualizar(totais["noites"])
        self.cartoes["Valor pago"].atualizar(formatar_moeda(totais["valor_pago"]))
        self.cartoes["Canceladas"].atualizar(totais["canceladas"])
        self.cartoes["Não compareceram"].atualizar(totais["no_shows"])
        self.tabela.carregar(self.servicos.linhas_reservas_periodo(reservas))
