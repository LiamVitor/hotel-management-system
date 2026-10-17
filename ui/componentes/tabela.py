import customtkinter as ctk

from ui.estilos import (AZUL, AZUL_HOVER, COR_BORDA, COR_CABECALHO, COR_CARTAO,
                            COR_LINHA_ALT, COR_SELECAO, COR_TEXTO, COR_TEXTO_SUAVE, fonte)

LARGURA_ACAO = 140


class Tabela(ctk.CTkFrame):
    """Tabela com cabeçalho cinza, linhas alternadas e seleção por clique.

    colunas: lista de (titulo, chave, largura_em_pixels)
    acao:    opcional, (texto_do_botao, funcao(linha)) — um botão em cada linha
    Cada linha é um dicionário; as chaves das colunas são buscadas nele.
    """

    def __init__(self, master, colunas, altura=200, acao=None, ao_selecionar=None):
        super().__init__(master, fg_color=COR_CARTAO, border_width=1,
                         border_color=COR_BORDA, corner_radius=8)
        self.colunas = colunas
        self.acao = acao
        self.ao_selecionar = ao_selecionar
        self._linhas = []
        self._itens = []
        self._indice = None

        cabecalho = ctk.CTkFrame(self, fg_color=COR_CABECALHO, corner_radius=0, height=36)
        cabecalho.pack(fill="x", padx=1, pady=(1, 0))
        cabecalho.pack_propagate(False)
        for titulo, _chave, largura in colunas:
            ctk.CTkLabel(cabecalho, text=titulo, width=largura, anchor="w",
                         font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                         ).pack(side="left", padx=(12, 0))
        if acao:
            ctk.CTkLabel(cabecalho, text="Ação", width=LARGURA_ACAO, anchor="w",
                         font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                         ).pack(side="left", padx=(12, 0))

        self.lista = ctk.CTkScrollableFrame(self, fg_color=COR_CARTAO, corner_radius=0,
                                            height=altura)
        self.lista.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    def carregar(self, linhas):
        for filho in self.lista.winfo_children():
            filho.destroy()
        self._linhas = list(linhas)
        self._itens = []
        self._indice = None

        for i, linha in enumerate(self._linhas):
            fundo = COR_CARTAO if i % 2 == 0 else COR_LINHA_ALT
            item = ctk.CTkFrame(self.lista, fg_color=fundo, corner_radius=0, height=40)
            item.pack(fill="x")
            item.pack_propagate(False)
            item.bind("<Button-1>", lambda _e, n=i: self._selecionar(n))

            for _titulo, chave, largura in self.colunas:
                rotulo = ctk.CTkLabel(item, text=str(linha.get(chave, "")), width=largura,
                                      anchor="w", font=fonte(12), text_color=COR_TEXTO)
                rotulo.pack(side="left", padx=(12, 0))
                rotulo.bind("<Button-1>", lambda _e, n=i: self._selecionar(n))

            if self.acao:
                texto, funcao = self.acao
                ctk.CTkButton(item, text=texto, width=LARGURA_ACAO - 10, height=28,
                              corner_radius=6, fg_color=AZUL, hover_color=AZUL_HOVER,
                              font=fonte(12, True),
                              command=lambda l=linha, f=funcao: f(l)
                              ).pack(side="left", padx=(12, 0))

            self._itens.append((item, fundo))

    def _selecionar(self, indice):
        if self._indice is not None and self._indice < len(self._itens):
            item, fundo = self._itens[self._indice]
            item.configure(fg_color=fundo)
        self._indice = indice
        self._itens[indice][0].configure(fg_color=COR_SELECAO)
        if self.ao_selecionar:
            self.ao_selecionar(self._linhas[indice])

    def selecionado(self):
        """Retorna o dicionário da linha selecionada ou None."""
        if self._indice is None or self._indice >= len(self._linhas):
            return None
        return self._linhas[self._indice]
