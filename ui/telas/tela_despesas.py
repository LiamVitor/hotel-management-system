from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from src.models.despesa import DadosDespesa
from src.services.erros import ErroNegocio
from src.utils.formatacao import formatar_data, formatar_moeda, ler_valor
from src.utils.periodos import PERSONALIZADO, TODO_PERIODO, ATALHOS, periodo_do_atalho
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao, CampoTexto, somente_numero
from ui.componentes.cartao import Cartao
from ui.componentes.janela_categorias import abrir_categorias
from ui.componentes.janela_confirmacao import confirmar_alteracoes
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, fonte
from ui.telas.tela_base import TelaBase

COLUNAS = [("Data", "data", 95), ("Categoria", "categoria", 140), ("Descrição", "descricao", 290),
           ("Valor", "valor", 105), ("Lançada por", "responsavel", 130)]
COLUNAS_RESUMO = [("Categoria", "categoria", 130), ("Total", "total", 95), ("%", "percentual", 55)]

TODAS = "Todas"
SUFIXO_INATIVA = " (desativada)"


class TelaDespesas(TelaBase):
    titulo = "Despesas"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self.editando = None                 # id da despesa em edição (None = lançamento novo)
        self._ids_form = {}                  # rótulo da categoria no formulário -> id
        self._ids_filtro = {}                # rótulo da categoria no filtro -> id

        topo = ctk.CTkFrame(self.corpo, fg_color="transparent")
        topo.pack(fill="x")
        topo.grid_columnconfigure(0, weight=3, uniform="topo")
        topo.grid_columnconfigure(1, weight=2, uniform="topo")
        self._montar_formulario(topo)
        self._montar_resumo(topo)
        self._montar_lista()
        self.limpar()

    # ---------- montagem ----------
    def _montar_formulario(self, topo):
        form = Cartao(topo, "Lançar despesa")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1, 2), weight=1, uniform="campos")
        self.data = CampoData(grade, "Data da despesa")
        self.categoria = CampoSelecao(grade, "Categoria", [])
        self.valor = CampoTexto(grade, "Valor (R$)", "0,00", mascara=somente_numero)
        self.descricao = CampoTexto(grade, "Descrição", "Ex.: Troca de lâmpadas dos corredores")
        self.data.grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        self.categoria.grid(row=0, column=1, sticky="ew", padx=8, pady=(0, 10))
        self.valor.grid(row=0, column=2, sticky="ew", padx=(8, 0), pady=(0, 10))
        self.descricao.grid(row=1, column=0, columnspan=3, sticky="ew")

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(14, 18))
        self.btn_salvar = botao_primario(botoes, "Salvar", self.salvar, 170)
        self.btn_salvar.pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)
        botao_secundario(botoes, "Gerenciar categorias...", self.gerenciar_categorias, 200
                         ).pack(side="right")

    def _montar_resumo(self, topo):
        resumo = Cartao(topo, "Resumo do período consultado")
        resumo.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.lbl_total = ctk.CTkLabel(resumo, text="R$ 0,00", font=fonte(28, True),
                                      text_color=COR_TEXTO)
        self.lbl_total.pack(anchor="w", padx=20)
        self.lbl_quantidade = ctk.CTkLabel(resumo, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_quantidade.pack(anchor="w", padx=20)
        # a tabela ignora a altura pedida e cresceria o cartão inteiro: uma caixa de altura
        # fixa mantém o topo da tela compacto e deixa espaço para a lista de despesas
        caixa = ctk.CTkFrame(resumo, fg_color="transparent", height=160)
        caixa.pack(fill="x", padx=20, pady=(8, 16))
        caixa.pack_propagate(False)
        self.tabela_resumo = Tabela(caixa, COLUNAS_RESUMO)
        self.tabela_resumo.pack(fill="both", expand=True)

    def _montar_lista(self):
        lista = Cartao(self.corpo, "Despesas lançadas")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self._montar_filtros(lista)

        # a barra de ações é empacotada antes da tabela, embaixo, para nunca ser espremida
        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", padx=20, pady=(0, 16))
        botao_secundario(acoes, "Editar selecionada", self.editar, 160).pack(side="left")
        botao_perigo(acoes, "Excluir selecionada", self.excluir, 160).pack(side="left", padx=10)
        self.lbl_filtro = ctk.CTkLabel(acoes, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_filtro.pack(side="left", padx=10)

        self.tabela = Tabela(lista, COLUNAS, altura=110, ao_duplo_clique=self.editar)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

    def _montar_filtros(self, lista):
        filtros = ctk.CTkFrame(lista, fg_color="transparent")
        filtros.pack(fill="x", padx=20, pady=(0, 10))
        filtros.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="filtro")

        self.f_de = CampoData(filtros, "De", self._ao_digitar_periodo)
        self.f_ate = CampoData(filtros, "Até", self._ao_digitar_periodo)
        self.f_atalho = CampoSelecao(filtros, "Período rápido", ATALHOS, self._ao_escolher_atalho)
        self.f_categoria = CampoSelecao(filtros, "Categoria", [TODAS], self.atualizar_tabela)
        self.f_busca = CampoTexto(filtros, "Buscar na descrição", "Ex.: lâmpadas", self.atualizar_tabela)
        self.f_atalho.definir(TODO_PERIODO)
        self.f_categoria.definir(TODAS)
        for coluna, campo in enumerate((self.f_de, self.f_ate, self.f_atalho,
                                        self.f_categoria, self.f_busca)):
            campo.grid(row=0, column=coluna, sticky="ew",
                       padx=(0 if coluna == 0 else 5, 0 if coluna == 4 else 5))
        botao_secundario(filtros, "Limpar filtros", self.limpar_filtros, 120
                         ).grid(row=0, column=5, sticky="s", padx=(10, 0))

    # ---------- categorias (formulário e filtro) ----------
    def _carregar_categorias(self, incluir_id=None):
        """Recarrega as listas de categoria mantendo o que estava escolhido.

        O formulário só oferece categorias ativas (mais a da despesa em edição, se for
        uma desativada); o filtro lista todas.
        """
        escolhida_form = self._ids_form.get(self.categoria.valor())
        escolhida_filtro = self._ids_filtro.get(self.f_categoria.valor())
        todas = self.servicos.despesas.listar_categorias()

        self._ids_form = {}
        for c in todas:
            if c.ativa or c.id == incluir_id:
                self._ids_form[c.nome + ("" if c.ativa else SUFIXO_INATIVA)] = c.id
        self.categoria.definir_opcoes(list(self._ids_form))
        self.categoria.definir(self._rotulo(self._ids_form, escolhida_form) or "")

        self._ids_filtro = {TODAS: None}
        for c in todas:
            self._ids_filtro[c.nome + ("" if c.ativa else SUFIXO_INATIVA)] = c.id
        self.f_categoria.definir_opcoes(list(self._ids_filtro))
        self.f_categoria.definir(self._rotulo(self._ids_filtro, escolhida_filtro) or TODAS)

    @staticmethod
    def _rotulo(mapa, categoria_id):
        for rotulo, id_ in mapa.items():
            if id_ is not None and id_ == categoria_id:
                return rotulo
        return None

    def gerenciar_categorias(self):
        abrir_categorias(self, self.servicos, ao_atualizar=self._apos_mudar_categorias)

    def _apos_mudar_categorias(self):
        self._carregar_categorias(incluir_id=self._categoria_em_edicao())
        self.atualizar_tabela()

    def _categoria_em_edicao(self):
        if self.editando is None:
            return None
        despesa = self.servicos.despesas.buscar_por_id(self.editando)
        return despesa.categoria_id if despesa else None

    # ---------- consulta ----------
    def ao_exibir(self):
        self._carregar_categorias(incluir_id=self._categoria_em_edicao())
        self.atualizar_tabela()

    def _ler_filtro_data(self, campo, nome):
        """Data do filtro, ou None enquanto estiver vazia ou incompleta."""
        texto = campo.valor()
        if len(texto) < 10:
            return None
        data = campo.data()
        if data is None:
            raise ErroNegocio(f"A data {nome} é inválida.")
        return data

    def atualizar_tabela(self):
        try:
            despesas = self.servicos.despesas.listar(
                data_de=self._ler_filtro_data(self.f_de, "inicial"),
                data_ate=self._ler_filtro_data(self.f_ate, "final"),
                categoria_id=self._ids_filtro.get(self.f_categoria.valor()),
                termo=self.f_busca.valor())
        except ErroNegocio as erro:
            self.lbl_filtro.configure(text=str(erro), text_color=VERMELHO)
            return
        resumo = self.servicos.despesas.resumir(despesas)
        self.tabela.carregar(self.servicos.linhas_despesas(despesas))
        self.lbl_filtro.configure(text=f"{len(despesas)} despesa(s) encontrada(s)",
                                  text_color=COR_TEXTO_SUAVE)
        self.lbl_total.configure(text=formatar_moeda(resumo.total))
        self.lbl_quantidade.configure(text=f"em {resumo.quantidade} despesa(s) no período consultado")
        self.tabela_resumo.carregar([
            {"id": linha.categoria_id, "categoria": linha.categoria,
             "total": formatar_moeda(linha.total),
             "percentual": f"{linha.percentual:.1f}%".replace(".", ",")}
            for linha in resumo.por_categoria])

    def _ao_digitar_periodo(self):
        self.f_atalho.definir(PERSONALIZADO)
        self.atualizar_tabela()

    def _ao_escolher_atalho(self):
        atalho = self.f_atalho.valor()
        if atalho != PERSONALIZADO:
            de, ate = periodo_do_atalho(atalho)
            self.f_de.definir(formatar_data(de) if de else "")
            self.f_ate.definir(formatar_data(ate) if ate else "")
        self.atualizar_tabela()

    def limpar_filtros(self):
        self.f_de.limpar()
        self.f_ate.limpar()
        self.f_busca.limpar()
        self.f_atalho.definir(TODO_PERIODO)
        self.f_categoria.definir(TODAS)
        self.atualizar_tabela()

    # ---------- formulário ----------
    def limpar(self):
        self.data.definir(formatar_data(date.today()))
        self.valor.limpar()
        self.descricao.limpar()
        self.editando = None
        self._carregar_categorias()
        self.categoria.definir("")
        self.btn_salvar.configure(text="Salvar")

    def _ler_formulario(self):
        """Dados preenchidos; levanta ErroNegocio/ValueError com a mensagem para a pessoa."""
        data = self.data.data()
        if data is None:
            raise ErroNegocio("Informe uma data válida (dd/mm/aaaa).")
        return DadosDespesa(data=data, descricao=self.descricao.valor(),
                            valor=ler_valor(self.valor.valor()),
                            categoria_id=self._ids_form.get(self.categoria.valor()))

    def salvar(self):
        editando = self.editando is not None
        try:
            dados = self.servicos.despesas.validar(self._ler_formulario(), self.editando)
            mudancas = self.servicos.despesas.diferencas(self.editando, dados) if editando else []
        except (ErroNegocio, ValueError) as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return

        if editando:
            if not mudancas:
                messagebox.showinfo("Nada para salvar", "Nenhuma informação foi alterada.")
                return
            if not confirmar_alteracoes(
                    self, "Confirmar alteração da despesa",
                    f"Revise o que será modificado na despesa \"{dados.descricao}\":", mudancas):
                return
        try:
            if editando:
                despesa = self.servicos.despesas.atualizar(self.editando, dados)
            else:
                despesa = self.servicos.despesas.registrar(dados)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível salvar", str(erro))
            return

        acao = "atualizada" if editando else "registrada"
        mensagem = (f"A despesa \"{despesa.descricao}\" ({formatar_moeda(despesa.valor)}) "
                    f"foi {acao} com sucesso.")
        self.limpar()
        self.atualizar_tabela()
        if despesa.id not in [linha["id"] for linha in self.tabela._linhas]:
            mensagem += "\n\nEla não aparece na lista porque está fora dos filtros atuais."
        messagebox.showinfo(f"Despesa {acao}", mensagem)

    def editar(self, _linha=None):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Editar", "Selecione uma despesa na tabela.")
            return
        despesa = self.servicos.despesas.buscar_por_id(linha["id"])
        if despesa is None:
            return
        self.limpar()
        self._carregar_categorias(incluir_id=despesa.categoria_id)
        self.data.definir(formatar_data(despesa.data))
        self.categoria.definir(self._rotulo(self._ids_form, despesa.categoria_id) or "")
        self.valor.definir(f"{despesa.valor:.2f}".replace(".", ","))
        self.descricao.definir(despesa.descricao)
        self.editando = despesa.id
        self.btn_salvar.configure(text="Salvar alterações")

    def excluir(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Excluir", "Selecione uma despesa na tabela.")
            return
        if not messagebox.askyesno(
                "Excluir despesa",
                f"Excluir a despesa \"{linha['descricao']}\" de {linha['valor']}?\n\n"
                "Ela deixará de aparecer nas consultas e nos totais."):
            return
        try:
            self.servicos.despesas.excluir(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Não é possível excluir", str(erro))
            return
        if self.editando == linha["id"]:
            self.limpar()
        self.atualizar_tabela()
