from tkinter import messagebox

import customtkinter as ctk

from ui.agendamentos import cancelar_agendamentos
from ui.componentes import cabecalho_relatorio, icones_menu
from ui.componentes.janela_senha import JanelaAlterarSenha
from ui.componentes.menu_lateral import MenuLateral, itens_permitidos
from ui.servicos import Servicos
from ui.estilos import COR_FUNDO, configurar_tema
from ui.telas.tela_caixa import TelaCaixa
from ui.telas.tela_checkin_checkout import TelaCheckinCheckout
from ui.telas.tela_despesas import TelaDespesas
from ui.telas.tela_historico_hospedagem import TelaHistoricoHospedagem
from ui.telas.tela_hospedes import TelaHospedes
from ui.telas.tela_inicio import TelaInicio
from ui.telas.tela_quartos import TelaQuartos
from ui.telas.tela_relatorios import TelaRelatorios
from ui.telas.tela_reservas import TelaReservas
from ui.telas.tela_usuarios import TelaUsuarios

CLASSES_DAS_TELAS = {
    "Início": TelaInicio,
    "Hóspedes": TelaHospedes,
    "Histórico de hospedagem": TelaHistoricoHospedagem,
    "Quartos": TelaQuartos,
    "Reservas": TelaReservas,
    "Check-in / Check-out": TelaCheckinCheckout,
    "Despesas": TelaDespesas,
    "Caixa": TelaCaixa,
    "Relatórios": TelaRelatorios,
    "Usuários": TelaUsuarios,
}


class App(ctk.CTk):
    def __init__(self):
        configurar_tema()
        super().__init__()
        # Imagens guardadas por uma sessão anterior pertencem à janela que já foi fechada;
        # sem isso, sair da conta e entrar de novo dava "image pyimageN does not exist".
        icones_menu.limpar_cache()
        cabecalho_relatorio.limpar_cache()
        self.title("Pousada — Gestão de Hotel")
        # Usa a área útil do monitor sem impor um tamanho maior que a tela.
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        largura = min(1280, max(960, largura_tela - 80))
        altura = min(800, max(620, altura_tela - 80))
        self.geometry(f"{largura}x{altura}")
        self.minsize(min(960, largura_tela), min(620, altura_tela))
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
        # a tela inicial tem atalhos para as outras telas
        self.telas["Início"].definir_navegacao(self.navegar)

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

    def destroy(self):
        cancelar_agendamentos(self)     # evita "invalid command name" ao fechar
        super().destroy()

    def run(self):
        self.mainloop()
