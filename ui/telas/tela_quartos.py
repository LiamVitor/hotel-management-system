from tkinter import messagebox

import customtkinter as ctk

from src.models.quarto import Quarto
from src.services.erros import ErroNegocio
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, VERMELHO, fonte
from ui.telas.tela_base import TelaBase
from src.utils.constantes import QUARTO_DISPONIVEL, SITUACOES_QUARTO, TIPOS_QUARTO
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao

COLUNAS = [("Número", "numero", 100), ("Tipo", "tipo", 150), ("Capacidade", "capacidade", 130),
           ("Diária", "diaria", 150), ("Status", "situacao", 160)]

TODOS = "Todos"


class TelaQuartos(TelaBase):
    titulo = "Quartos"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self.editando = None

        pode_alterar = Sessao.pode("quartos.salvar")
        form = Cartao(self.corpo, "Cadastro de quarto")
        if pode_alterar:   # sem permissão, o formulário nem aparece (a tela vira só consulta)
            form.pack(fill="x")
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1, 2), weight=1, uniform="campos")
        self.numero = CampoTexto(grade, "Número", "Ex.: 101")
        self.tipo = CampoSelecao(grade, "Tipo", TIPOS_QUARTO)
        self.capacidade = CampoTexto(grade, "Capacidade", "Ex.: 2")
        self.diaria = CampoTexto(grade, "Diária (R$)", "Ex.: 180,00")
        self.status = CampoSelecao(grade, "Status", SITUACOES_QUARTO)
        self.numero.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        self.tipo.grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 10))
        self.capacidade.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=(0, 10))
        self.diaria.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.status.grid(row=1, column=1, sticky="ew", padx=8)

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(anchor="w", padx=20, pady=(14, 18))
        self.btn_salvar = botao_primario(botoes, "Salvar", self.salvar, 170)
        self.btn_salvar.pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)

        lista = Cartao(self.corpo, "Quartos cadastrados")
        lista.pack(fill="both", expand=True, pady=(16, 0) if pode_alterar else 0)
        self._montar_filtros(lista)

        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", padx=20, pady=(0, 16))
        if pode_alterar:
            botao_secundario(acoes, "Editar selecionado", self.editar, 160).pack(side="left")
        if Sessao.pode("quartos.excluir"):
            botao_perigo(acoes, "Excluir selecionado", self.excluir, 160).pack(side="left", padx=10)
        self.lbl_filtro = ctk.CTkLabel(acoes, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_filtro.pack(side="left", padx=10)

        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.limpar()

    def _montar_filtros(self, lista):
        filtros = ctk.CTkFrame(lista, fg_color="transparent")
        filtros.pack(fill="x", padx=20, pady=(0, 10))
        filtros.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="filtro")

        self.f_numero = CampoTexto(filtros, "Pesquisar número", "Ex.: 101", self.atualizar_tabela)
        self.f_tipo = CampoSelecao(filtros, "Tipo", [TODOS, *TIPOS_QUARTO], self.atualizar_tabela)
        self.f_status = CampoSelecao(filtros, "Status", [TODOS, *SITUACOES_QUARTO],
                                     self.atualizar_tabela)
        self.f_capacidade = CampoTexto(filtros, "Capacidade", "Ex.: 2, >2 ou 2-4",
                                       self.atualizar_tabela)
        self.f_diaria = CampoTexto(filtros, "Diária (R$)", "Ex.: >500 e <570",
                                   self.atualizar_tabela)
        self.f_tipo.definir(TODOS)
        self.f_status.definir(TODOS)
        for coluna, campo in enumerate((self.f_numero, self.f_tipo, self.f_status,
                                        self.f_capacidade, self.f_diaria)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 6, 0 if coluna == 4 else 6))
        botao_secundario(filtros, "Limpar filtros", self.limpar_filtros, 120
                         ).grid(row=0, column=5, sticky="s", padx=(12, 0))

    def ao_exibir(self):
        self.atualizar_tabela()

    @staticmethod
    def _valor_filtro(campo):
        valor = campo.valor()
        return "" if valor in ("", TODOS) else valor

    def atualizar_tabela(self):
        try:
            quartos = self.servicos.quartos.pesquisar(
                numero=self.f_numero.valor(),
                tipo=self._valor_filtro(self.f_tipo),
                situacao=self._valor_filtro(self.f_status),
                capacidade=self.f_capacidade.valor(),
                diaria=self.f_diaria.valor())
        except ErroNegocio as erro:
            # filtro numérico ainda incompleto (ex.: '>'): avisa e mantém a tabela como está
            self.lbl_filtro.configure(text=str(erro), text_color=VERMELHO)
            return
        self.lbl_filtro.configure(text=f"{len(quartos)} quarto(s) encontrado(s)",
                                  text_color=COR_TEXTO_SUAVE)
        self.tabela.carregar([
            {"id": q.id, "numero": q.numero, "tipo": q.tipo, "capacidade": q.capacidade,
             "diaria": formatar_moeda(q.preco_diaria), "situacao": q.situacao}
            for q in quartos])

    def limpar_filtros(self):
        self.f_numero.limpar()
        self.f_capacidade.limpar()
        self.f_diaria.limpar()
        self.f_tipo.definir(TODOS)
        self.f_status.definir(TODOS)
        self.atualizar_tabela()

    def limpar(self):
        self.numero.limpar()
        self.capacidade.limpar()
        self.diaria.limpar()
        self.tipo.definir(TIPOS_QUARTO[0])
        self.status.definir(QUARTO_DISPONIVEL)
        self.editando = None
        self.btn_salvar.configure(text="Salvar")

    def salvar(self):
        try:
            capacidade = int(self.capacidade.valor())
            diaria = float(self.diaria.valor().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Valores inválidos",
                                   "A capacidade deve ser um número inteiro e a diária, um valor numérico.")
            return
        editando = self.editando is not None
        quarto = Quarto(id=self.editando, numero=self.numero.valor(), tipo=self.tipo.valor(),
                        capacidade=capacidade, preco_diaria=diaria, situacao=self.status.valor())
        try:
            self.servicos.quartos.salvar(quarto)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
        acao = "atualizado" if editando else "cadastrado"
        messagebox.showinfo(f"Quarto {acao}", f"O quarto {quarto.numero} foi {acao} com sucesso.")
        self.limpar()
        self.atualizar_tabela()

    def editar(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Editar", "Selecione um quarto na tabela.")
            return
        q = self.servicos.quartos.buscar_por_id(linha["id"])
        if q is None:
            return
        self.limpar()
        self.numero.definir(q.numero)
        self.tipo.definir(q.tipo)
        self.capacidade.definir(q.capacidade)
        self.diaria.definir(f"{q.preco_diaria:.2f}".replace(".", ","))
        self.status.definir(q.situacao)
        self.editando = q.id
        self.btn_salvar.configure(text="Salvar alterações")

    def excluir(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Excluir", "Selecione um quarto na tabela.")
            return
        if not messagebox.askyesno("Excluir quarto", f"Excluir o quarto {linha['numero']}?"):
            return
        try:
            self.servicos.quartos.excluir(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Não é possível excluir", str(erro))
            return
        self.limpar()
        self.atualizar_tabela()
