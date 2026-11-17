"""Painel do relatório de check-ins e check-outs (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import FILTROS_MOVIMENTOS, MOVIMENTO_TODOS, REL_CHECKINS_CHECKOUTS
from src.utils.formatacao import formatar_data
from src.utils.periodos import ATALHOS_RELATORIO, ESTE_MES, PERSONALIZADO, periodo_do_atalho
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.painel_relatorio import PainelRelatorio
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, fonte

COLUNAS = [("Data/hora", "data_hora", 120), ("Tipo", "tipo", 75), ("Reserva", "reserva", 60),
           ("Hóspede", "hospede", 140), ("Quarto", "quarto", 60), ("Data prevista", "prevista", 90),
           ("Em relação ao previsto", "horario", 140), ("Responsável", "responsavel", 100)]
CARTOES = ["Check-ins", "Check-outs", "Check-ins fora da data prevista",
           "Check-outs fora da data prevista"]


class PainelCheckinsCheckouts(PainelRelatorio):
    TITULO = "Check-ins e check-outs"
    ROTULO_PERIODO = "Ocorridos"
    CHAVE = REL_CHECKINS_CHECKOUTS

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self, "Filtros")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="filtro")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Ocorridos de", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Ocorridos até", self._ao_digitar_periodo)
        self.tipo = CampoSelecao(linha, "Tipo", FILTROS_MOVIMENTOS, self.atualizar)
        self.busca = CampoTexto(linha, "Buscar", "Hóspede, CPF, quarto ou código",
                                ao_mudar=self._ao_digitar)
        for coluna, campo in enumerate((self.atalho, self.inicio, self.fim, self.tipo,
                                        self.busca)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 6, 0 if coluna == 4 else 6))

        self.cartoes = self.criar_indicadores(CARTOES)

        lista = Cartao(self)
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_info = ctk.CTkLabel(
            lista, anchor="w", justify="left", font=fonte(12), text_color=COR_TEXTO_SUAVE,
            wraplength=880,
            text="Data e hora reais registradas no check-in e no check-out. A data prevista é a "
                 "entrada (check-in) ou a saída (check-out) da reserva; 'fora da data prevista' "
                 "compara só o dia. Duplo clique em uma linha abre os detalhes da reserva.")
        self.lbl_info.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.registrar_nota(self.lbl_info)
        self.tabela = Tabela(lista, COLUNAS, altura=150,
                             ao_duplo_clique=lambda l: abrir_detalhes(self, self.servicos, l["id"]))
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(16, 8))
        self.registrar_tabela("Check-ins e check-outs", self.tabela)

        self.atalho.definir(ESTE_MES)
        self.tipo.definir(MOVIMENTO_TODOS)
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
        tipo = self.tipo.valor() or MOVIMENTO_TODOS
        try:
            movimentos = self.servicos.relatorio_movimentos.listar(inicio, fim, tipo,
                                                                   self.busca.valor())
            totais = self.servicos.relatorio_movimentos.totais(movimentos)
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Filtro inválido", str(erro))
            return
        self.marcar_emissao(inicio, fim)
        self.definir_filtros([("Tipo", tipo), ("Busca", self.busca.valor())])
        self.cartoes["Check-ins"].atualizar(totais["checkins"])
        self.cartoes["Check-outs"].atualizar(totais["checkouts"])
        self.cartoes["Check-ins fora da data prevista"].atualizar(totais["checkins_fora_da_data"])
        self.cartoes["Check-outs fora da data prevista"].atualizar(
            totais["checkouts_fora_da_data"])
        self.tabela.carregar(self.servicos.linhas_movimentos(movimentos))
