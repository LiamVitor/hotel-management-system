import customtkinter as ctk

from ui.estilos import COR_FUNDO, COR_TEXTO, fonte


class TelaBase(ctk.CTkFrame):
    """Estrutura comum: título da tela e uma área de conteúdo (self.corpo)."""

    titulo = ""

    def __init__(self, master, servicos):
        super().__init__(master, fg_color=COR_FUNDO, corner_radius=0)
        self.servicos = servicos
        ctk.CTkLabel(self, text=self.titulo, font=fonte(24, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=32, pady=(28, 16))
        self.corpo = ctk.CTkFrame(self, fg_color="transparent")
        self.corpo.pack(fill="both", expand=True, padx=32, pady=(0, 24))

    def ao_exibir(self):
        """Chamado toda vez que a tela aparece. As telas sobrescrevem para recarregar dados."""
