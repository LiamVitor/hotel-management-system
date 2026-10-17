import customtkinter as ctk

from ui.estilos import COR_BORDA, COR_CARTAO, COR_TEXTO, COR_TEXTO_SUAVE, fonte


class Cartao(ctk.CTkFrame):
    """Cartão branco com borda fina e cantos arredondados."""

    def __init__(self, master, titulo=None, **kwargs):
        super().__init__(master, fg_color=COR_CARTAO, border_width=1,
                         border_color=COR_BORDA, corner_radius=12, **kwargs)
        if titulo:
            ctk.CTkLabel(self, text=titulo, font=fonte(15, True), text_color=COR_TEXTO
                         ).pack(anchor="w", padx=20, pady=(16, 10))


class CartaoResumo(Cartao):
    """Cartão com um título pequeno e um número grande."""

    def __init__(self, master, titulo, valor="0", cor_valor=COR_TEXTO):
        super().__init__(master)
        ctk.CTkLabel(self, text=titulo, font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w", padx=20, pady=(16, 0))
        self._valor = ctk.CTkLabel(self, text=valor, font=fonte(28, True), text_color=cor_valor)
        self._valor.pack(anchor="w", padx=20, pady=(2, 16))

    def atualizar(self, valor):
        self._valor.configure(text=str(valor))
