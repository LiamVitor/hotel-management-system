from tkinter import messagebox

import customtkinter as ctk

from src.models.quarto import Quarto
from src.services.erros import ErroNegocio
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.telas.tela_base import TelaBase
from src.utils.constantes import QUARTO_DISPONIVEL, SITUACOES_QUARTO, TIPOS_QUARTO
from src.utils.formatacao import formatar_moeda

COLUNAS = [("Número", "numero", 100), ("Tipo", "tipo", 150), ("Capacidade", "capacidade", 130),
           ("Diária", "diaria", 150), ("Status", "situacao", 160)]


class TelaQuartos(TelaBase):
    titulo = "Quartos"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self.editando = None

        form = Cartao(self.corpo, "Cadastro de quarto")
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
        botao_primario(botoes, "Salvar", self.salvar).pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)

        lista = Cartao(self.corpo, "Quartos cadastrados")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", anchor="w", padx=20, pady=(0, 16))
        botao_secundario(acoes, "Editar selecionado", self.editar, 160).pack(side="left")
        botao_perigo(acoes, "Excluir selecionado", self.excluir, 160).pack(side="left", padx=10)
        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.limpar()

    def ao_exibir(self):
        self.atualizar_tabela()

    def atualizar_tabela(self):
        self.tabela.carregar([
            {"id": q.id, "numero": q.numero, "tipo": q.tipo, "capacidade": q.capacidade,
             "diaria": formatar_moeda(q.preco_diaria), "situacao": q.situacao}
            for q in self.servicos.quartos.listar()])

    def limpar(self):
        self.numero.limpar()
        self.capacidade.limpar()
        self.diaria.limpar()
        self.tipo.definir(TIPOS_QUARTO[0])
        self.status.definir(QUARTO_DISPONIVEL)
        self.editando = None

    def salvar(self):
        try:
            capacidade = int(self.capacidade.valor())
            diaria = float(self.diaria.valor().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Valores inválidos",
                                   "A capacidade deve ser um número inteiro e a diária, um valor numérico.")
            return
        quarto = Quarto(id=self.editando, numero=self.numero.valor(), tipo=self.tipo.valor(),
                        capacidade=capacidade, preco_diaria=diaria, situacao=self.status.valor())
        try:
            self.servicos.quartos.salvar(quarto)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return
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
