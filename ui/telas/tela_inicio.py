from datetime import date

import customtkinter as ctk

from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.tabela import Tabela
from ui.telas.tela_base import TelaBase
from src.utils.constantes import (QUARTO_DISPONIVEL, QUARTO_OCUPADO, RESERVA_CONFIRMADA,
                                  RESERVA_HOSPEDADA)

COLUNAS = [("Hóspede", "hospede", 260), ("Quarto", "quarto", 90), ("Entrada", "entrada", 120),
           ("Saída", "saida", 120), ("Status", "situacao", 140)]


class TelaInicio(TelaBase):
    titulo = "Início"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        linha = ctk.CTkFrame(self.corpo, fg_color="transparent")
        linha.pack(fill="x")
        self.cartoes = {}
        nomes = ["Quartos livres", "Quartos ocupados", "Check-ins hoje", "Check-outs hoje"]
        for i, nome in enumerate(nomes):
            linha.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(linha, nome)
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.cartoes[nome] = cartao

        quadro = Cartao(self.corpo, "Reservas de hoje")
        quadro.pack(fill="both", expand=True, pady=(20, 0))
        self.tabela = Tabela(quadro, COLUNAS, altura=300)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def ao_exibir(self):
        hoje = date.today()
        quartos = self.servicos.quartos.listar()
        reservas = self.servicos.reservas.listar()

        livres = sum(1 for q in quartos if q.situacao == QUARTO_DISPONIVEL)
        ocupados = sum(1 for q in quartos if q.situacao == QUARTO_OCUPADO)
        checkins = sum(1 for r in reservas
                       if r.situacao == RESERVA_CONFIRMADA and r.data_entrada == hoje)
        checkouts = sum(1 for r in reservas
                        if r.situacao == RESERVA_HOSPEDADA and r.data_saida == hoje)
        self.cartoes["Quartos livres"].atualizar(livres)
        self.cartoes["Quartos ocupados"].atualizar(ocupados)
        self.cartoes["Check-ins hoje"].atualizar(checkins)
        self.cartoes["Check-outs hoje"].atualizar(checkouts)

        de_hoje = [r for r in reservas
                   if r.situacao in (RESERVA_CONFIRMADA, RESERVA_HOSPEDADA)
                   and r.data_entrada <= hoje <= r.data_saida]
        self.tabela.carregar(self.servicos.linhas_reservas(de_hoje))
