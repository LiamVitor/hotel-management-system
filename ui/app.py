from tkinter import messagebox

import customtkinter as ctk

from ui.componentes.janela_senha import JanelaAlterarSenha
from ui.componentes.menu_lateral import MenuLateral, itens_permitidos
from ui.servicos import Servicos
from ui.estilos import COR_FUNDO, configurar_tema
from ui.telas.tela_checkin_checkout import TelaCheckinCheckout
from ui.telas.tela_despesas import TelaDespesas
from ui.telas.tela_hospedes import TelaHospedes
from ui.telas.tela_inicio import TelaInicio
from ui.telas.tela_quartos import TelaQuartos
from ui.telas.tela_relatorios import TelaRelatorios
from ui.telas.tela_reservas import TelaReservas
from ui.telas.tela_usuarios import TelaUsuarios

CLASSES_DAS_TELAS = {
    "Início": TelaInicio,
    "Hóspedes": TelaHospedes,
    "Quartos": TelaQuartos,
    "Reservas": TelaReservas,
    "Check-in / Check-out": TelaCheckinCheckout,
    "Despesas": TelaDespesas,
    "Relatórios": TelaRelatorios,
    "Usuários": TelaUsuarios,
}


class App(ctk.CTk):
    def __init__(self):
        configurar_tema()
        super().__init__()
        self.title("Pousada — Gestão de Hotel")
        self.geometry("1280x800")
        self.minsize(1280, 800)
        self.deslogou = False   # True quando a pessoa clicou em "Sair" (e não fechou a janela)

        self.servicos = Servicos()

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.menu = MenuLateral(self, self.navegar, self.alterar_senha, self.sair)
        self.menu.grid(row=0, column=0, sticky="ns")

        area = ctk.CTkFrame(self, fg_color=COR_FUNDO, corner_radius=0)
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(0, weight=1)

        # só cria as telas que o perfil do usuário logado pode abrir
        self.telas = {nome: CLASSES_DAS_TELAS[nome](area, self.servicos)
                      for nome in itens_permitidos()}
        for tela in self.telas.values():
            tela.grid(row=0, column=0, sticky="nsew")

        self.navegar("Início")

    def navegar(self, nome):
        tela = self.telas.get(nome)
        if tela is None:
            return
        tela.ao_exibir()
        tela.tkraise()
        self.menu.destacar(nome)

    def alterar_senha(self):
        JanelaAlterarSenha(self, self.servicos.usuarios)

    def sair(self):
        if messagebox.askyesno("Sair", "Deseja sair da sua conta?"):
            self.deslogou = True
            self.destroy()

    def run(self):
        self.mainloop()
