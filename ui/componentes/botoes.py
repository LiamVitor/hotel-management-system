import customtkinter as ctk

from ui.estilos import (AZUL, AZUL_HOVER, COR_BORDA_CAMPO, COR_FUNDO, COR_TEXTO,
                            VERMELHO, VERMELHO_HOVER, fonte)


def botao_primario(master, texto, comando, largura=140):
    return ctk.CTkButton(master, text=texto, command=comando, width=largura, height=36,
                         corner_radius=8, fg_color=AZUL, hover_color=AZUL_HOVER,
                         text_color="white", font=fonte(13, True))


def botao_secundario(master, texto, comando, largura=140):
    return ctk.CTkButton(master, text=texto, command=comando, width=largura, height=36,
                         corner_radius=8, fg_color="transparent", hover_color=COR_FUNDO,
                         border_width=1, border_color=COR_BORDA_CAMPO,
                         text_color=COR_TEXTO, font=fonte(13, True))


def botao_perigo(master, texto, comando, largura=140):
    return ctk.CTkButton(master, text=texto, command=comando, width=largura, height=36,
                         corner_radius=8, fg_color=VERMELHO, hover_color=VERMELHO_HOVER,
                         text_color="white", font=fonte(13, True))
