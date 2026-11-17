"""Janela para criar, renomear e ativar/desativar as categorias de despesa."""
import customtkinter as ctk

from src.services.erros import ErroNegocio
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COLUNAS = [("Categoria", "nome", 250), ("Situação", "situacao", 110), ("Despesas", "despesas", 100)]


def abrir_categorias(master, servicos, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada.

    ao_atualizar: funcao() chamada a cada mudança, para a tela de trás recarregar as listas.
    """
    janela = JanelaCategorias(master, servicos, ao_atualizar)
    master.wait_window(janela)


class JanelaCategorias(ctk.CTkToplevel):
    LARGURA, ALTURA = 620, 650

    def __init__(self, master, servicos, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self._ao_atualizar = ao_atualizar

        self.title("Categorias de despesa")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar()
        self._carregar()

        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    # ---------- montagem ----------
    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    def _montar(self):
        ctk.CTkLabel(self, text="Categorias de despesa", font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Uma categoria desativada não aparece ao lançar uma despesa nova, "
                                "mas continua nas despesas antigas.", font=fonte(12),
                     text_color=COR_TEXTO_SUAVE, wraplength=self.LARGURA - 48, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")

        form = Cartao(self, "Nova categoria ou renomear")
        form.pack(side="bottom", fill="x", padx=24, pady=(12, 0))
        self.nome = CampoTexto(form, "Nome da categoria", "Ex.: Material de escritório")
        self.nome.pack(fill="x", padx=20)
        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(12, 0))
        botao_primario(botoes, "Adicionar nova", self._adicionar, 150).pack(side="left")
        botao_secundario(botoes, "Renomear selecionada", self._renomear, 170).pack(side="left", padx=8)
        botao_secundario(botoes, "Ativar / Desativar", self._alternar, 150).pack(side="left")
        self.lbl_aviso = ctk.CTkLabel(form, text="Clique em uma categoria para renomear ou desativar.",
                                      font=fonte(12, True), text_color=COR_TEXTO_SUAVE, anchor="w",
                                      justify="left", wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

        lista = Cartao(self, "Categorias cadastradas")
        lista.pack(fill="both", expand=True, padx=24)
        self.tabela = Tabela(lista, COLUNAS, altura=150, ao_selecionar=self._ao_selecionar)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    # ---------- dados ----------
    def _carregar(self):
        contagem = self.servicos.despesas.contagem_por_categoria()
        self.tabela.carregar([
            {"id": c.id, "nome": c.nome, "ativa": c.ativa,
             "situacao": "Ativa" if c.ativa else "Desativada",
             "despesas": contagem.get(c.id, 0)}
            for c in self.servicos.despesas.listar_categorias()])

    def _ao_selecionar(self, linha):
        self.nome.definir(linha["nome"])

    def _aviso(self, texto, erro=False):
        self.lbl_aviso.configure(text=texto, text_color=VERMELHO if erro else VERDE)

    def _concluir(self, mensagem):
        self.nome.limpar()
        self._carregar()
        self._aviso(mensagem)
        if self._ao_atualizar:
            self._ao_atualizar()

    def _selecionada(self):
        linha = self.tabela.selecionado()
        if linha is None:
            self._aviso("Selecione uma categoria na tabela.", erro=True)
        return linha

    # ---------- ações ----------
    def _adicionar(self):
        try:
            categoria = self.servicos.despesas.criar_categoria(self.nome.valor())
        except ErroNegocio as erro:
            self._aviso(str(erro), erro=True)
            return
        self._concluir(f"Categoria \"{categoria.nome}\" criada.")

    def _renomear(self):
        linha = self._selecionada()
        if linha is None:
            return
        try:
            categoria = self.servicos.despesas.renomear_categoria(linha["id"], self.nome.valor())
        except ErroNegocio as erro:
            self._aviso(str(erro), erro=True)
            return
        self._concluir(f"Categoria renomeada para \"{categoria.nome}\".")

    def _alternar(self):
        linha = self._selecionada()
        if linha is None:
            return
        try:
            categoria = self.servicos.despesas.definir_categoria_ativa(linha["id"], not linha["ativa"])
        except ErroNegocio as erro:
            self._aviso(str(erro), erro=True)
            return
        self._concluir(f"Categoria \"{categoria.nome}\" "
                       f"{'ativada' if categoria.ativa else 'desativada'}.")

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
