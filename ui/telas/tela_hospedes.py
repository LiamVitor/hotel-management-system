from tkinter import messagebox

import customtkinter as ctk

from src.models.hospede import Hospede
from src.services.erros import ErroNegocio
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_BORDA_CAMPO, COR_TEXTO, fonte
from ui.telas.tela_base import TelaBase

COLUNAS = [("Nome", "nome", 250), ("CPF", "cpf", 140), ("Telefone", "telefone", 150),
           ("E-mail", "email", 240)]


class TelaHospedes(TelaBase):
    titulo = "Hóspedes"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self.editando = None   # id do hóspede em edição (None = cadastro novo)

        # ----- formulário -----
        form = Cartao(self.corpo, "Cadastro de hóspede")
        form.pack(fill="x")
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1), weight=1, uniform="campos")
        self.nome = CampoTexto(grade, "Nome completo", "Ex.: Maria Silva Santos")
        self.cpf = CampoTexto(grade, "CPF", "000.000.000-00")
        self.telefone = CampoTexto(grade, "Telefone", "(00) 00000-0000")
        self.email = CampoTexto(grade, "E-mail", "nome@email.com")
        self.nome.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self.cpf.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.telefone.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.email.grid(row=1, column=1, sticky="ew", padx=(10, 0))

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(anchor="w", padx=20, pady=(14, 18))
        botao_primario(botoes, "Salvar", self.salvar).pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)

        # ----- lista -----
        lista = Cartao(self.corpo, "Hóspedes cadastrados")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.busca = ctk.CTkEntry(lista, placeholder_text="Buscar por nome ou CPF", height=36,
                                  width=360, fg_color="white", border_color=COR_BORDA_CAMPO,
                                  text_color=COR_TEXTO, font=fonte(13))
        self.busca.pack(anchor="w", padx=20)
        self.busca.bind("<KeyRelease>", lambda _e: self.atualizar_tabela())

        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", anchor="w", padx=20, pady=(0, 16))
        botao_secundario(acoes, "Editar selecionado", self.editar, 160).pack(side="left")
        botao_perigo(acoes, "Excluir selecionado", self.excluir, 160).pack(side="left", padx=10)

        self.tabela = Tabela(lista, COLUNAS, altura=120)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(12, 8))

    # ----- ações -----
    def ao_exibir(self):
        self.atualizar_tabela()

    def atualizar_tabela(self):
        hospedes = self.servicos.hospedes.listar(self.busca.get())
        self.tabela.carregar([
            {"id": h.id, "nome": h.nome, "cpf": h.cpf,
             "telefone": h.telefone or "", "email": h.email or ""}
            for h in hospedes])

    def limpar(self):
        for campo in (self.nome, self.cpf, self.telefone, self.email):
            campo.limpar()
        self.editando = None

    def salvar(self):
        hospede = Hospede(id=self.editando, nome=self.nome.valor(), cpf=self.cpf.valor(),
                          telefone=self.telefone.valor(), email=self.email.valor())
        try:
            self.servicos.hospedes.salvar(hospede)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        self.limpar()
        self.atualizar_tabela()

    def editar(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Editar", "Selecione um hóspede na tabela.")
            return
        h = self.servicos.hospedes.buscar_por_id(linha["id"])
        if h is None:
            return
        self.limpar()
        self.nome.definir(h.nome)
        self.cpf.definir(h.cpf)
        self.telefone.definir(h.telefone or "")
        self.email.definir(h.email or "")
        self.editando = h.id

    def excluir(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Excluir", "Selecione um hóspede na tabela.")
            return
        if not messagebox.askyesno("Excluir hóspede", f"Excluir {linha['nome']}?"):
            return
        try:
            self.servicos.hospedes.excluir(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Não é possível excluir", str(erro))
            return
        self.limpar()
        self.atualizar_tabela()
