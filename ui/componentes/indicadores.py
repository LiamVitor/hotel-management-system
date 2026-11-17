"""Fileira de indicadores (cartões de resumo) com o mesmo tamanho e espaçamento em todo relatório."""
import customtkinter as ctk

from ui.componentes.cartao import CartaoResumo
from ui.estilos import TAMANHO_INDICADOR

ESPACO = 6      # metade do espaço entre dois cartões


def criar_indicadores(pai, nomes):
    """Cria os cartões em `pai` (embaixo do que já estiver lá) e devolve {nome: CartaoResumo}.

    nomes: lista de nomes (uma fileira) ou lista de listas (uma fileira por lista).
    """
    fileiras = nomes if nomes and isinstance(nomes[0], (list, tuple)) else [nomes]
    quadro = ctk.CTkFrame(pai, fg_color="transparent")
    quadro.pack(fill="x", pady=(16, 0))
    colunas = max(len(f) for f in fileiras)
    for c in range(colunas):
        quadro.grid_columnconfigure(c, weight=1, uniform="indicador")
    cartoes = {}
    for linha, fileira in enumerate(fileiras):
        for coluna, nome in enumerate(fileira):
            cartao = CartaoResumo(quadro, nome, "—", tamanho_valor=TAMANHO_INDICADOR)
            cartao.grid(row=linha, column=coluna, sticky="ew",
                        padx=(0 if coluna == 0 else ESPACO, 0 if coluna == colunas - 1 else ESPACO),
                        pady=(0 if linha == 0 else 12, 0))
            cartoes[nome] = cartao
    return cartoes
