import customtkinter as ctk

from ui.estilos import (AZUL, AZUL_HOVER, COR_BORDA, COR_CABECALHO, COR_CARTAO,
                            COR_LINHA_ALT, COR_SELECAO, COR_TEXTO, COR_TEXTO_SUAVE, fonte)

LARGURA_ACAO = 140


class Tabela(ctk.CTkFrame):
    """Tabela com cabeçalho cinza, linhas alternadas e seleção por clique.

    colunas: lista de (titulo, chave, peso_de_largura)
    acao:    opcional, (texto_do_botao, funcao(linha)) — um botão em cada linha
    ao_duplo_clique: opcional, funcao(linha) chamada ao clicar duas vezes numa linha
    badges: opcional, {chave_coluna: mapa_de_valores_ou_resolver_de_estilo}
    Cada linha é um dicionário; as chaves das colunas são buscadas nele.
    """

    def __init__(self, master, colunas, altura=200, acao=None, ao_selecionar=None,
                 ao_duplo_clique=None, badges=None):
        super().__init__(master, fg_color=COR_CARTAO, border_width=1,
                         border_color=COR_BORDA, corner_radius=8)
        self.colunas = colunas
        self.acao = acao
        self.ao_selecionar = ao_selecionar
        self.ao_duplo_clique = ao_duplo_clique
        # Mapeia a chave da coluna para um resolver de estilo ou mapa de valores.
        # Ex.: {"situacao": {"Confirmada": ("#DBEAFE", "#1D4ED8")}}
        self.badges = badges or {}
        self._linhas = []
        self._itens = []
        self._indice = None

        cabecalho = ctk.CTkFrame(self, fg_color=COR_CABECALHO, corner_radius=0, height=36)
        cabecalho.pack(fill="x", padx=1, pady=(1, 0))
        cabecalho.pack_propagate(False)
        self._configurar_colunas(cabecalho, incluir_acao=bool(acao))
        for indice, (titulo, _chave, _largura) in enumerate(colunas):
            ctk.CTkLabel(cabecalho, text=titulo, anchor="w",
                         font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                         ).grid(row=0, column=indice, sticky="ew", padx=(10, 4))
        if acao:
            ctk.CTkLabel(cabecalho, text="Ação", anchor="w",
                         font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                         ).grid(row=0, column=len(colunas), sticky="ew", padx=(10, 4))

        self.lista = ctk.CTkScrollableFrame(self, fg_color=COR_CARTAO, corner_radius=0,
                                            height=altura)
        self.lista.pack(fill="both", expand=True, padx=1, pady=(0, 1))

    def _configurar_colunas(self, container, incluir_acao=False):
        """Distribui a largura proporcionalmente; os valores originais viram pesos."""
        for indice, (_titulo, _chave, proporcao) in enumerate(self.colunas):
            container.grid_columnconfigure(
                indice, weight=max(1, int(proporcao)), minsize=58, uniform="colunas")
        if incluir_acao:
            container.grid_columnconfigure(
                len(self.colunas), weight=max(1, LARGURA_ACAO), minsize=92)

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
            if self.ao_duplo_clique:
                item.bind("<Double-Button-1>", lambda _e, n=i: self._duplo_clique(n))

            self._configurar_colunas(item, incluir_acao=bool(self.acao))
            for indice, (_titulo, chave, _largura) in enumerate(self.colunas):
                valor = str(linha.get(chave, ""))
                estilo = self._estilo_badge(chave, valor)
                if estilo:
                    rotulo = ctk.CTkLabel(
                        item, text=valor, anchor="center", font=fonte(11, True),
                        text_color=estilo[1], fg_color=estilo[0],
                        corner_radius=8, height=24)
                    rotulo.grid(row=0, column=indice, sticky="w", padx=(10, 4))
                else:
                    rotulo = ctk.CTkLabel(item, text=valor, anchor="w",
                                          font=fonte(12), text_color=COR_TEXTO)
                    rotulo.grid(row=0, column=indice, sticky="ew", padx=(10, 4))
                rotulo.bind("<Button-1>", lambda _e, n=i: self._selecionar(n))
                if self.ao_duplo_clique:
                    rotulo.bind("<Double-Button-1>", lambda _e, n=i: self._duplo_clique(n))

            if self.acao:
                texto, funcao = self.acao
                ctk.CTkButton(item, text=texto, width=LARGURA_ACAO - 10, height=28,
                              corner_radius=6, fg_color=AZUL, hover_color=AZUL_HOVER,
                              font=fonte(12, True),
                              command=lambda l=linha, f=funcao: f(l)
                              ).grid(row=0, column=len(self.colunas), sticky="ew",
                                     padx=(8, 4), pady=4)

            self._itens.append((item, fundo))

    def _estilo_badge(self, chave, valor):
        """Resolve o estilo visual configurado para uma célula; None mantém texto comum."""
        configuracao = self.badges.get(chave)
        if configuracao is None:
            return None
        estilo = configuracao(valor) if callable(configuracao) else configuracao.get(valor)
        if not estilo:
            return None
        if isinstance(estilo, dict):
            fundo = estilo.get("fg_color")
            texto = estilo.get("text_color")
            return (fundo, texto) if fundo and texto else None
        return estilo if isinstance(estilo, (tuple, list)) and len(estilo) == 2 else None

    def _selecionar(self, indice):
        if self._indice is not None and self._indice < len(self._itens):
            item, fundo = self._itens[self._indice]
            item.configure(fg_color=fundo)
        self._indice = indice
        self._itens[indice][0].configure(fg_color=COR_SELECAO)
        if self.ao_selecionar:
            self.ao_selecionar(self._linhas[indice])

    def _duplo_clique(self, indice):
        self._selecionar(indice)
        self.ao_duplo_clique(self._linhas[indice])

    def linhas_carregadas(self):
        """Cópia das linhas que a tabela está mostrando (usada para montar o documento)."""
        return list(self._linhas)

    def selecionado(self):
        """Retorna o dicionário da linha selecionada ou None."""
        if self._indice is None or self._indice >= len(self._linhas):
            return None
        return self._linhas[self._indice]


class TabelaDados:
    """Dados de uma tabela que entram no documento do relatório sem aparecer como tabela na tela
    (ex.: os valores por trás de um gráfico). Tem a mesma interface que `PainelRelatorio` usa."""

    def __init__(self, colunas=()):
        self.colunas = list(colunas)
        self._linhas = []

    def carregar(self, linhas, colunas=None):
        if colunas is not None:
            self.colunas = list(colunas)
        self._linhas = list(linhas)

    def linhas_carregadas(self):
        return list(self._linhas)

