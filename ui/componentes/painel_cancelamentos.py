"""Painel do relatório de cancelamentos e no-show (usado na tela de Relatórios)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import FILTROS_CANCELAMENTOS, RELATORIO_CANC_TODOS
from src.utils.formatacao import formatar_moeda, formatar_percentual
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.janela_politica_retencao import abrir_politica_retencao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, fonte

COLUNAS = [("Reserva", "reserva", 60), ("Hóspede", "hospede", 125), ("Tipo", "tipo", 80),
           ("Criada em", "criada_em", 80), ("Entrada", "entrada", 80),
           ("Cancel./No-show em", "evento_em", 110), ("Motivo", "motivo", 130),
           ("Retido", "retido", 85), ("Reembolsado", "reembolsado", 90),
           ("A reembolsar", "a_reembolsar", 90)]
CARTOES = ["Cancelamentos", "No-shows", "Total retido", "Total reembolsado", "A reembolsar"]


class PainelCancelamentos(ctk.CTkFrame):
    def __init__(self, master, servicos):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos

        filtro = Cartao(self, "Cancelamentos e no-show")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="filtro")
        self.tipo = CampoSelecao(linha, "Tipo", FILTROS_CANCELAMENTOS, self.atualizar)
        self.de = CampoData(linha, "Ocorrido de", self._ao_digitar)
        self.ate = CampoData(linha, "Ocorrido até", self._ao_digitar)
        self.busca = CampoTexto(linha, "Buscar", "Hóspede, CPF, quarto ou código",
                                ao_mudar=self._ao_digitar)
        for coluna, campo in enumerate((self.tipo, self.de, self.ate, self.busca)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 8, 0 if coluna == 3 else 8))

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
        rodape = ctk.CTkFrame(lista, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=20, pady=(0, 14))
        self.lbl_regra = ctk.CTkLabel(rodape, anchor="w", justify="left", font=fonte(12),
                                      text_color=COR_TEXTO_SUAVE, wraplength=620)
        self.lbl_regra.pack(side="left")
        if Sessao.pode("retencao.configurar"):
            botao_secundario(rodape, "Regra de retenção...", self._abrir_regra, 170
                             ).pack(side="right")
        self.tabela = Tabela(lista, COLUNAS, altura=150, ao_duplo_clique=self._detalhes)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        self.tipo.definir(RELATORIO_CANC_TODOS)

    def _ao_digitar(self):
        self.atualizar(silencioso=True)

    @staticmethod
    def _ler(campo):
        if not campo.valor():
            return None
        data = campo.data()
        if data is None:
            raise ErroNegocio("Informe as datas no formato dd/mm/aaaa.")
        return data

    def _texto_regra(self):
        p = self.servicos.politica_retencao.vigente()
        if p is None:
            return ("Nenhuma regra de retenção definida pela administração: nada é retido. "
                    "Duplo clique em uma linha abre os detalhes da reserva.")
        return (f"Regra vigente: cancelamento com menos de {p.dias_antecedencia} dia(s) de "
                f"antecedência retém {formatar_percentual(p.percentual_cancelamento_tardio)} "
                f"do valor da reserva; no-show retém "
                f"{formatar_percentual(p.percentual_no_show)}. A retenção nunca passa do que foi "
                f"pago e fica registrada no momento do cancelamento.")

    def atualizar(self, silencioso=False):
        try:
            registros = self.servicos.relatorio_cancelamentos.listar(
                self.tipo.valor() or RELATORIO_CANC_TODOS,
                self._ler(self.de), self._ler(self.ate), self.busca.valor())
            totais = self.servicos.relatorio_cancelamentos.totais(registros)
        except ErroNegocio as erro:
            if not silencioso:
                messagebox.showwarning("Filtro inválido", str(erro))
            return
        self.cartoes["Cancelamentos"].atualizar(totais["cancelamentos"])
        self.cartoes["No-shows"].atualizar(totais["no_shows"])
        self.cartoes["Total retido"].atualizar(formatar_moeda(totais["total_retido"]))
        self.cartoes["Total reembolsado"].atualizar(formatar_moeda(totais["total_reembolsado"]))
        self.cartoes["A reembolsar"].atualizar(formatar_moeda(totais["total_a_reembolsar"]))
        self.lbl_regra.configure(text=self._texto_regra())
        self.tabela.carregar(self.servicos.linhas_cancelamentos(registros))

    def _detalhes(self, linha):
        abrir_detalhes(self, self.servicos, linha["id"])

    def _abrir_regra(self):
        abrir_politica_retencao(self, self.servicos, ao_atualizar=self.atualizar)
