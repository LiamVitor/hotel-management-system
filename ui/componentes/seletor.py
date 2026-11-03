"""Seletor com janela de busca: no lugar de uma lista suspensa gigante, a pessoa clica no
campo, pesquisa numa janela com tabela e escolhe a linha (clique duplo ou botão Selecionar)."""
from tkinter import messagebox

import customtkinter as ctk

from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.tabela import Tabela
from ui.estilos import (COR_BORDA_CAMPO, COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, fonte)

LIMITE_LINHAS = 50   # muitas linhas deixam a janela lenta; a busca serve para refinar


class JanelaSelecao(ctk.CTkToplevel):
    """Janela modal com busca e tabela.

    colunas:    lista de (titulo, chave, largura), igual à da Tabela
    buscar:     funcao(termo, opcao_marcada) -> lista de dicionários (cada um com "id")
    ao_escolher: funcao(linha) chamada com a linha escolhida
    opcao:      opcional, (texto, marcada_no_inicio) — uma caixa que também filtra a busca
    informacao: texto fixo mostrado abaixo da busca
    """

    def __init__(self, master, titulo, colunas, buscar, ao_escolher, placeholder="Buscar...",
                 opcao=None, informacao="", largura=820, altura=560):
        super().__init__(master, fg_color=COR_FUNDO)
        self._buscar = buscar
        self._ao_escolher = ao_escolher
        self.title(titulo)
        self.resizable(False, False)
        self._centralizar(master, largura, altura)
        self.transient(master.winfo_toplevel())

        ctk.CTkLabel(self, text=titulo, font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=24, pady=(20, 10))

        self.busca = ctk.CTkEntry(self, placeholder_text=placeholder, height=38,
                                  fg_color="white", border_color=COR_BORDA_CAMPO,
                                  text_color=COR_TEXTO, font=fonte(13))
        self.busca.pack(fill="x", padx=24)
        self.busca.bind("<KeyRelease>", lambda _e: self._pesquisar())

        self._opcao = None
        if opcao:
            texto, marcada = opcao
            self._opcao = ctk.BooleanVar(value=marcada)
            ctk.CTkCheckBox(self, text=texto, variable=self._opcao, font=fonte(12),
                            text_color=COR_TEXTO, command=self._pesquisar
                            ).pack(anchor="w", padx=24, pady=(10, 0))
        if informacao:
            ctk.CTkLabel(self, text=informacao, font=fonte(12), text_color=COR_TEXTO_SUAVE,
                         wraplength=largura - 48, justify="left"
                         ).pack(anchor="w", padx=24, pady=(8, 0))

        self.lbl_total = ctk.CTkLabel(self, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_total.pack(anchor="w", padx=24, pady=(8, 4))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_primario(rodape, "Selecionar", self._escolher, 140).pack(side="right")
        botao_secundario(rodape, "Cancelar", self.destroy, 120).pack(side="right", padx=(0, 10))

        self.tabela = Tabela(self, colunas, altura=300, ao_duplo_clique=lambda _l: self._escolher())
        self.tabela.pack(fill="both", expand=True, padx=24, pady=(0, 4))

        self.bind("<Return>", lambda _e: self._escolher())
        self.bind("<Escape>", lambda _e: self.destroy())
        self._pesquisar()
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    def _centralizar(self, master, largura, altura):
        topo = master.winfo_toplevel()
        x = topo.winfo_rootx() + max((topo.winfo_width() - largura) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
        self.busca.focus()

    def _pesquisar(self):
        marcada = self._opcao.get() if self._opcao is not None else False
        linhas = self._buscar(self.busca.get(), marcada)
        total = len(linhas)
        self.tabela.carregar(linhas[:LIMITE_LINHAS])
        if total == 0:
            self.lbl_total.configure(text="Nenhum resultado. Tente outro termo de busca.")
        elif total > LIMITE_LINHAS:
            self.lbl_total.configure(
                text=f"Mostrando {LIMITE_LINHAS} de {total} resultados. Digite mais para refinar.")
        else:
            self.lbl_total.configure(text=f"{total} resultado(s)")

    def _escolher(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Selecionar", "Clique em uma linha da tabela para escolher.",
                                parent=self)
            return
        self._ao_escolher(linha)
        self.destroy()


class CampoSeletor(ctk.CTkFrame):
    """Rótulo + campo que abre uma janela de busca para escolher um registro.

    abrir_janela: funcao(escolher) que abre a JanelaSelecao; deve chamar
                  escolher(id, texto) com o registro escolhido.
    """

    def __init__(self, master, rotulo, texto_vazio, abrir_janela, ao_mudar=None):
        super().__init__(master, fg_color="transparent")
        self._texto_vazio = texto_vazio
        self._abrir_janela = abrir_janela
        self._ao_mudar = ao_mudar
        self._id = None

        ctk.CTkLabel(self, text=rotulo, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w")
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", pady=(4, 0))
        self._botao = ctk.CTkButton(linha, text=texto_vazio, anchor="w", height=36,
                                    corner_radius=6, fg_color="white", hover_color="#F9FAFB",
                                    border_width=1, border_color=COR_BORDA_CAMPO,
                                    text_color="#9CA3AF", font=fonte(13),
                                    command=lambda: self._abrir_janela(self.definir))
        self._botao.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(linha, text="×", width=36, height=36, corner_radius=6,
                      fg_color="white", hover_color="#F9FAFB", border_width=1,
                      border_color=COR_BORDA_CAMPO, text_color=COR_TEXTO_SUAVE,
                      font=fonte(16, True), command=self.limpar
                      ).pack(side="left", padx=(6, 0))

    def valor(self):
        """Id do registro escolhido (ou None)."""
        return self._id

    def definir(self, registro_id, texto, notificar=True):
        self._id = registro_id
        self._botao.configure(text=texto, text_color=COR_TEXTO)
        if notificar and self._ao_mudar:
            self._ao_mudar()

    def limpar(self, notificar=True):
        self._id = None
        self._botao.configure(text=self._texto_vazio, text_color="#9CA3AF")
        if notificar and self._ao_mudar:
            self._ao_mudar()
