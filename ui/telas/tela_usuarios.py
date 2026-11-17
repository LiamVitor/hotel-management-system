from tkinter import messagebox

import customtkinter as ctk

from src.models.usuario import Usuario
from src.services.erros import ErroNegocio
from src.utils.permissoes import PERFIS, ROTULOS_PERFIL
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.janela_confirmacao import confirmar_alteracoes
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, fonte
from ui.telas.tela_base import TelaBase

COLUNAS = [("Nome", "nome", 270), ("Usuário", "usuario", 200), ("Perfil", "perfil", 160),
           ("Situação", "situacao", 120)]

ATIVO, INATIVO = "Ativo", "Inativo"
PERFIL_POR_ROTULO = {rotulo: perfil for perfil, rotulo in ROTULOS_PERFIL.items()}


class TelaUsuarios(TelaBase):
    titulo = "Usuários"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self.editando = None   # id do usuário em edição (None = cadastro novo)

        form = Cartao(self.corpo, "Cadastro de usuário")
        form.pack(fill="x")
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1, 2), weight=1, uniform="campos")
        self.nome = CampoTexto(grade, "Nome completo", "Ex.: Marina Souza")
        self.usuario = CampoTexto(grade, "Usuário (login)", "Ex.: marina")
        self.perfil = CampoSelecao(grade, "Perfil de acesso",
                                   [ROTULOS_PERFIL[p] for p in PERFIS])
        self.senha = CampoTexto(grade, "Senha", "Mínimo de 6 caracteres", ocultar=True)
        self.confirmar = CampoTexto(grade, "Confirmar senha", "Repita a senha", ocultar=True)
        self.situacao = CampoSelecao(grade, "Situação", [ATIVO, INATIVO])
        self.nome.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        self.usuario.grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 10))
        self.perfil.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=(0, 10))
        self.senha.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.confirmar.grid(row=1, column=1, sticky="ew", padx=8)
        self.situacao.grid(row=1, column=2, sticky="ew", padx=(8, 0))

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(14, 18))
        self.btn_salvar = botao_primario(botoes, "Salvar", self.salvar, 170)
        self.btn_salvar.pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)
        ctk.CTkLabel(botoes, text="Ao editar, deixe a senha em branco para mantê-la.",
                     font=fonte(12), text_color=COR_TEXTO_SUAVE).pack(side="left", padx=10)

        lista = Cartao(self.corpo, "Usuários cadastrados")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", anchor="w", padx=20, pady=(0, 16))
        botao_secundario(acoes, "Editar selecionado", self.editar, 160).pack(side="left")
        botao_secundario(acoes, "Ativar / Desativar", self.alternar_situacao, 160
                         ).pack(side="left", padx=10)
        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.limpar()

    def ao_exibir(self):
        self.atualizar_tabela()

    def atualizar_tabela(self):
        logado = Sessao.usuario.id if Sessao.usuario else None
        self.tabela.carregar([
            {"id": u.id, "nome": u.nome,
             "usuario": f"{u.usuario} (você)" if u.id == logado else u.usuario,
             "perfil": ROTULOS_PERFIL.get(u.perfil, u.perfil),
             "situacao": ATIVO if u.ativo else INATIVO}
            for u in self.servicos.usuarios.listar()])

    def limpar(self):
        for campo in (self.nome, self.usuario, self.senha, self.confirmar):
            campo.limpar()
        self.perfil.definir(ROTULOS_PERFIL[PERFIS[-1]])   # novo usuário começa como recepcionista
        self.situacao.definir(ATIVO)
        self.editando = None
        self.btn_salvar.configure(text="Salvar")

    def salvar(self):
        senha, confirmacao = self.senha.valor_sem_cortar(), self.confirmar.valor_sem_cortar()
        if senha != confirmacao:
            messagebox.showwarning("Senhas diferentes", "A senha e a confirmação não conferem.")
            return
        editando = self.editando is not None
        usuario = Usuario(id=self.editando, nome=self.nome.valor(), usuario=self.usuario.valor(),
                          perfil=PERFIL_POR_ROTULO.get(self.perfil.valor(), ""),
                          ativo=self.situacao.valor() == ATIVO)
        try:
            self.servicos.usuarios.validar(usuario, senha or None)
            mudancas = (self.servicos.usuarios.diferencas(usuario, senha or None)
                        if editando else [])
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        if editando:
            if not mudancas:
                messagebox.showinfo("Nada para salvar", "Nenhuma informação foi alterada.")
                return
            if not confirmar_alteracoes(
                    self, "Confirmar alteração do usuário",
                    f"Revise o que será modificado no usuário {usuario.usuario}:", mudancas):
                return
        try:
            self.servicos.usuarios.salvar(usuario, senha or None)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        acao = "atualizado" if editando else "cadastrado"
        messagebox.showinfo(f"Usuário {acao}", f"O usuário {usuario.usuario} foi {acao} com sucesso.")
        self.limpar()
        self.atualizar_tabela()

    def editar(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Editar", "Selecione um usuário na tabela.")
            return
        u = self.servicos.usuarios.buscar_por_id(linha["id"])
        if u is None:
            return
        self.limpar()
        self.nome.definir(u.nome)
        self.usuario.definir(u.usuario)
        self.perfil.definir(ROTULOS_PERFIL.get(u.perfil, ""))
        self.situacao.definir(ATIVO if u.ativo else INATIVO)
        self.editando = u.id
        self.btn_salvar.configure(text="Salvar alterações")

    def alternar_situacao(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Ativar / Desativar", "Selecione um usuário na tabela.")
            return
        ativar = linha["situacao"] == INATIVO
        pergunta = (f"{'Ativar' if ativar else 'Desativar'} o usuário {linha['nome']}?"
                    + ("" if ativar else "\nEle não poderá mais entrar no sistema."))
        if not messagebox.askyesno("Ativar / Desativar", pergunta):
            return
        try:
            self.servicos.usuarios.definir_ativo(linha["id"], ativar)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível alterar", str(erro))
            return
        self.atualizar_tabela()
