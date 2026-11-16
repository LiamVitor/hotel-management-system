import tkinter as tk

import customtkinter as ctk

from src.utils.formatacao import DIAS_SEMANA_CURTO
from ui.estilos import (AZUL, AZUL_CLARO, COR_BORDA, COR_CARTAO, COR_TEXTO, COR_TEXTO_SUAVE,
                        FONTE_FAMILIA)

ALTURA = 210


class GraficoBarras(ctk.CTkFrame):
    """Barras de percentual (0 a 100) por dia, com dia da semana e data embaixo de cada uma.

    `carregar([(dia, percentual), ...], destaque=dia)`: a barra do dia de destaque (hoje) sai
    em azul forte e as outras em azul claro.
    """

    def __init__(self, master, altura=ALTURA):
        super().__init__(master, fg_color="transparent")
        self._altura = altura
        self._barras = []
        self._destaque = None
        self.canvas = tk.Canvas(self, height=altura, bg=COR_CARTAO, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", lambda _e: self._desenhar())

    def carregar(self, barras, destaque=None):
        self._barras = list(barras)
        self._destaque = destaque
        self._desenhar()

    def _desenhar(self):
        c = self.canvas
        c.delete("all")
        largura = max(280, c.winfo_width())
        esquerda, direita, topo, base = 44, 8, 22, 40
        util = self._altura - topo - base
        fonte_eixo = (FONTE_FAMILIA, 9)

        for pct in (0, 50, 100):
            y = topo + util * (1 - pct / 100)
            c.create_line(esquerda, y, largura - direita, y, fill=COR_BORDA)
            c.create_text(esquerda - 6, y, text=f"{pct}%", anchor="e",
                          fill=COR_TEXTO_SUAVE, font=fonte_eixo)
        if not self._barras:
            return

        faixa = (largura - esquerda - direita) / len(self._barras)
        meia = min(22, faixa * 0.3)
        for i, (dia, pct) in enumerate(self._barras):
            centro = esquerda + faixa * i + faixa / 2
            y = topo + util * (1 - pct / 100)
            hoje = dia == self._destaque
            if pct > 0:
                c.create_rectangle(centro - meia, y, centro + meia, topo + util,
                                   fill=AZUL if hoje else AZUL_CLARO, outline="")
            c.create_text(centro, y - 9, text=f"{pct:.0f}%", fill=COR_TEXTO, font=fonte_eixo)
            rotulo = "hoje" if hoje else DIAS_SEMANA_CURTO[dia.weekday()]
            c.create_text(centro, topo + util + 12, text=rotulo, font=fonte_eixo,
                          fill=COR_TEXTO if hoje else COR_TEXTO_SUAVE)
            c.create_text(centro, topo + util + 26, text=dia.strftime("%d/%m"),
                          fill=COR_TEXTO_SUAVE, font=fonte_eixo)
