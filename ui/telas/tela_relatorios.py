import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox

import customtkinter as ctk

from src.services.relatorios import ocupacao_por_dia, resumo_periodo
from ui.componentes.botoes import botao_primario
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.estilos import AZUL, COR_BORDA, COR_CARTAO, COR_TEXTO, COR_TEXTO_SUAVE, FONTE_FAMILIA
from ui.telas.tela_base import TelaBase
from src.utils.formatacao import formatar_data, formatar_moeda, formatar_percentual, ler_data

LARGURA_GRAFICO = 900
ALTURA_GRAFICO = 290
MAX_DIAS = 31


class TelaRelatorios(TelaBase):
    titulo = "Relatórios"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self.corpo, "Período")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1), weight=1, uniform="datas")
        self.inicio = CampoTexto(linha, "Data inicial", "dd/mm/aaaa")
        self.fim = CampoTexto(linha, "Data final", "dd/mm/aaaa")
        self.inicio.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.fim.grid(row=0, column=1, sticky="ew", padx=10)
        botao_primario(linha, "Gerar relatório", self.gerar, 160).grid(
            row=0, column=2, sticky="s", padx=(10, 0))

        cartoes = ctk.CTkFrame(self.corpo, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        for i, nome in enumerate(["Taxa de ocupação", "Faturamento",
                                  "Reservas no período", "Ticket médio"]):
            cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(cartoes, nome, "—")
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 8, 0 if i == 3 else 8))
            self.cartoes[nome] = cartao

        grafico = Cartao(self.corpo, "Ocupação por dia")
        grafico.pack(fill="both", expand=True, pady=(16, 0))
        self.canvas = tk.Canvas(grafico, width=LARGURA_GRAFICO, height=ALTURA_GRAFICO,
                                bg=COR_CARTAO, highlightthickness=0)
        self.canvas.pack(padx=20, pady=(0, 16))

        hoje = date.today()
        self.inicio.definir(formatar_data(hoje - timedelta(days=6)))
        self.fim.definir(formatar_data(hoje))

    def ao_exibir(self):
        self.gerar(silencioso=True)

    def gerar(self, silencioso=False):
        try:
            inicio, fim = ler_data(self.inicio.valor()), ler_data(self.fim.valor())
        except ValueError as erro:
            if not silencioso:
                messagebox.showwarning("Período inválido", str(erro))
            return
        if fim < inicio:
            if not silencioso:
                messagebox.showwarning("Período inválido",
                                       "A data final não pode ser anterior à data inicial.")
            return
        if (fim - inicio).days + 1 > MAX_DIAS:
            if not silencioso:
                messagebox.showwarning("Período muito longo",
                                       f"Escolha um período de até {MAX_DIAS} dias.")
            return

        reservas = self.servicos.reservas.listar()
        quartos = self.servicos.quartos.listar()
        resumo = resumo_periodo(reservas, quartos, inicio, fim)
        self.cartoes["Taxa de ocupação"].atualizar(formatar_percentual(resumo["taxa_ocupacao"]))
        self.cartoes["Faturamento"].atualizar(formatar_moeda(resumo["faturamento"]))
        self.cartoes["Reservas no período"].atualizar(resumo["reservas"])
        self.cartoes["Ticket médio"].atualizar(formatar_moeda(resumo["ticket_medio"]))
        self._desenhar(ocupacao_por_dia(reservas, quartos, inicio, fim))

    def _desenhar(self, dias):
        c = self.canvas
        c.delete("all")
        esquerda, base, topo = 44, 28, 12
        altura_util = ALTURA_GRAFICO - base - topo
        fonte_eixo = (FONTE_FAMILIA, 9)

        for pct in (0, 25, 50, 75, 100):
            y = topo + altura_util * (1 - pct / 100)
            c.create_line(esquerda, y, LARGURA_GRAFICO, y, fill=COR_BORDA)
            c.create_text(esquerda - 8, y, text=f"{pct}%", anchor="e",
                          fill=COR_TEXTO_SUAVE, font=fonte_eixo)

        n = len(dias)
        if n == 0:
            return
        faixa = (LARGURA_GRAFICO - esquerda - 10) / n
        largura_barra = min(44, faixa * 0.6)
        passo_rotulo = 1 if n <= 16 else 2 if n <= 24 else 3

        for i, (dia, pct) in enumerate(dias):
            centro = esquerda + faixa * i + faixa / 2
            y = topo + altura_util * (1 - pct / 100)
            if pct > 0:
                c.create_rectangle(centro - largura_barra / 2, y, centro + largura_barra / 2,
                                   topo + altura_util, fill=AZUL, outline="")
                if n <= 16:
                    c.create_text(centro, y - 8, text=f"{pct:.0f}%", fill=COR_TEXTO, font=fonte_eixo)
            if i % passo_rotulo == 0:
                c.create_text(centro, ALTURA_GRAFICO - base / 2 + 2, text=dia.strftime("%d/%m"),
                              fill=COR_TEXTO_SUAVE, font=fonte_eixo)
