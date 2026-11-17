import customtkinter as ctk

from ui.estilos import COR_BORDA, COR_TEXTO, COR_TEXTO_SUAVE, fonte


class BarraProporcional(ctk.CTkFrame):
    """Uma barra dividida em fatias proporcionais à quantidade, com legenda embaixo.

    `carregar([(rotulo, quantidade, cor), ...])`. Fatias com quantidade 0 não aparecem na
    barra, mas continuam na legenda.
    """

    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.barra = ctk.CTkFrame(self, fg_color=COR_BORDA, corner_radius=6, height=14)
        self.barra.pack(fill="x")
        self.barra.pack_propagate(False)
        self.legenda = ctk.CTkFrame(self, fg_color="transparent")
        self.legenda.pack(fill="x", pady=(12, 0))
        self.legenda.grid_columnconfigure(1, weight=1)

    def carregar(self, itens):
        for filho in self.barra.winfo_children() + self.legenda.winfo_children():
            filho.destroy()
        for coluna in range(len(itens)):
            self.barra.grid_columnconfigure(coluna, weight=0)

        visiveis = [(rotulo, qtd, cor) for rotulo, qtd, cor in itens if qtd > 0]
        for coluna, (_rotulo, qtd, cor) in enumerate(visiveis):
            self.barra.grid_columnconfigure(coluna, weight=qtd)
            ctk.CTkFrame(self.barra, width=1, height=14, corner_radius=0, fg_color=cor
                         ).grid(row=0, column=coluna, sticky="nsew", padx=(0, 2 if coluna < len(visiveis) - 1 else 0))
        self.barra.grid_rowconfigure(0, weight=1)

        for linha, (rotulo, qtd, cor) in enumerate(itens):
            ctk.CTkFrame(self.legenda, width=10, height=10, corner_radius=5, fg_color=cor
                         ).grid(row=linha, column=0, sticky="w", pady=3)
            ctk.CTkLabel(self.legenda, text=rotulo, font=fonte(13), text_color=COR_TEXTO,
                         anchor="w").grid(row=linha, column=1, sticky="w", padx=(8, 0))
            ctk.CTkLabel(self.legenda, text=str(qtd), font=fonte(13, True),
                         text_color=COR_TEXTO_SUAVE).grid(row=linha, column=2, sticky="e")
