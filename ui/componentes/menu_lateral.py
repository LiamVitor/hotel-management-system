import customtkinter as ctk

from ui.estilos import AZUL, COR_MENU, COR_MENU_HOVER, fonte

ITENS_MENU = ["Início", "Hóspedes", "Quartos", "Reservas", "Check-in / Check-out", "Relatórios"]


class MenuLateral(ctk.CTkFrame):
    def __init__(self, master, ao_navegar):
        super().__init__(master, width=240, fg_color=COR_MENU, corner_radius=0)
        self.pack_propagate(False)
        ctk.CTkLabel(self, text="Pousada", font=fonte(22, True), text_color="white"
                     ).pack(anchor="w", padx=24, pady=(28, 24))

        self._botoes = {}
        for nome in ITENS_MENU:
            botao = ctk.CTkButton(self, text=nome, anchor="w", height=42, corner_radius=8,
                                  fg_color="transparent", hover_color=COR_MENU_HOVER,
                                  text_color="#E5E7EB", font=fonte(14),
                                  command=lambda n=nome: ao_navegar(n))
            botao.pack(fill="x", padx=12, pady=2)
            self._botoes[nome] = botao

    def destacar(self, ativo):
        for nome, botao in self._botoes.items():
            if nome == ativo:
                botao.configure(fg_color=AZUL, hover_color=AZUL)
            else:
                botao.configure(fg_color="transparent", hover_color=COR_MENU_HOVER)
