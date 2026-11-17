from tkinter import messagebox

import customtkinter as ctk

from src.models.hospede import Hospede
from src.services.erros import ErroNegocio
from src.utils.formatacao import formatar_cpf, formatar_telefone
from src.utils.sessao import Sessao
from src.utils.validacao import email_valido
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.janela_confirmacao import confirmar_alteracoes
from ui.componentes.tabela import Tabela
from ui.estilos import COR_BORDA_CAMPO, COR_TEXTO, COR_TEXTO_SUAVE, fonte
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
        self.cpf = CampoTexto(grade, "CPF", "000.000.000-00", mascara=formatar_cpf)
        self.telefone = CampoTexto(grade, "Telefone", "(00) 00000-0000",
                                   mascara=formatar_telefone)
        self.email = CampoTexto(grade, "E-mail", "nome@email.com",
                                ao_mudar=self._validar_email_digitado)
        self.nome.grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self.cpf.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=(0, 10))
        self.telefone.grid(row=1, column=0, sticky="ew", padx=(0, 10))
        self.email.grid(row=1, column=1, sticky="ew", padx=(10, 0))

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(anchor="w", padx=20, pady=(14, 18))
        self.btn_salvar = botao_primario(botoes, "Salvar", self.salvar, 170)
        self.btn_salvar.pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)

        # ----- lista -----
        lista = Cartao(self.corpo, "Hóspedes cadastrados")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        barra = ctk.CTkFrame(lista, fg_color="transparent")
        barra.pack(fill="x", padx=20)
        self.busca = ctk.CTkEntry(barra, placeholder_text="Buscar por nome, CPF, telefone ou e-mail",
                                  height=36, width=420, fg_color="white",
                                  border_color=COR_BORDA_CAMPO, text_color=COR_TEXTO,
                                  font=fonte(13))
        self.busca.pack(side="left")
        self.busca.bind("<KeyRelease>", lambda _e: self.atualizar_tabela())
        self.lbl_total = ctk.CTkLabel(barra, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_total.pack(side="left", padx=14)

        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", anchor="w", padx=20, pady=(0, 16))
        botao_secundario(acoes, "Editar selecionado", self.editar, 160).pack(side="left")
        if Sessao.pode("hospedes.excluir"):
            botao_perigo(acoes, "Excluir selecionado", self.excluir, 160).pack(side="left", padx=10)

        self.tabela = Tabela(lista, COLUNAS, altura=120)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(12, 8))

    # ----- ações -----
    def ao_exibir(self):
        self.atualizar_tabela()

    def atualizar_tabela(self):
        hospedes = self.servicos.hospedes.listar(self.busca.get())
        self.lbl_total.configure(text=f"{len(hospedes)} hóspede(s)")
        self.tabela.carregar([
            {"id": h.id, "nome": h.nome, "cpf": formatar_cpf(h.cpf),
             "telefone": formatar_telefone(h.telefone), "email": h.email or ""}
            for h in hospedes])

    def _validar_email_digitado(self):
        """Borda vermelha enquanto o e-mail digitado ainda não está num formato válido."""
        texto = self.email.valor()
        self.email.marcar_erro(bool(texto) and not email_valido(texto))

    def limpar(self):
        for campo in (self.nome, self.cpf, self.telefone, self.email):
            campo.limpar()
        self.email.marcar_erro(False)
        self.editando = None
        self.btn_salvar.configure(text="Salvar")

    def salvar(self):
        editando = self.editando is not None
        hospede = Hospede(id=self.editando, nome=self.nome.valor(), cpf=self.cpf.valor(),
                          telefone=self.telefone.valor(), email=self.email.valor())
        try:
            self.servicos.hospedes.validar(hospede)
            mudancas = self.servicos.hospedes.diferencas(hospede) if editando else []
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        if editando:
            if not mudancas:
                messagebox.showinfo("Nada para salvar", "Nenhuma informação foi alterada.")
                return
            if not confirmar_alteracoes(
                    self, "Confirmar alteração do hóspede",
                    f"Revise o que será modificado no cadastro de {hospede.nome}:", mudancas):
                return
        try:
            self.servicos.hospedes.salvar(hospede)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        acao = "atualizado" if editando else "cadastrado"
        messagebox.showinfo(f"Hóspede {acao}",
                            f"O hóspede {hospede.nome} foi {acao} com sucesso.")
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
        self.btn_salvar.configure(text="Salvar alterações")

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
