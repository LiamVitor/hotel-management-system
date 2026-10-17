import customtkinter as ctk

from ui.componentes.menu_lateral import MenuLateral
from ui.servicos import Servicos
from ui.estilos import COR_FUNDO, configurar_tema
from ui.telas.tela_checkin_checkout import TelaCheckinCheckout
from ui.telas.tela_hospedes import TelaHospedes
from ui.telas.tela_inicio import TelaInicio
from ui.telas.tela_quartos import TelaQuartos
from ui.telas.tela_relatorios import TelaRelatorios
from ui.telas.tela_reservas import TelaReservas


class App(ctk.CTk):
    def __init__(self):
        configurar_tema()
        super().__init__()
        self.title("Pousada — Gestão de Hotel")
        self.geometry("1280x800")
        self.minsize(1280, 800)

        self.servicos = Servicos()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.menu = MenuLateral(self, self.navegar)
        self.menu.grid(row=0, column=0, sticky="ns")

        area = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(0, weight=1)

        self.telas = {
            "Início": TelaInicio(area, self.servicos),
            "Hóspedes": TelaHospedes(area, self.servicos),
            "Quartos": TelaQuartos(area, self.servicos),
            "Reservas": TelaReservas(area, self.servicos),
            "Check-in / Check-out": TelaCheckinCheckout(area, self.servicos),
            "Relatórios": TelaRelatorios(area, self.servicos),
        }
        for tela in self.telas.values():
            tela.grid(row=0, column=0, sticky="nsew")

        self.navegar("Início")

    def navegar(self, nome):
        tela = self.telas[nome]
        tela.ao_exibir()
        tela.tkraise()
        self.menu.destacar(nome)

    def run(self):
        self.mainloop()
