"""Base de todo painel de relatório: cabeçalho padrão no topo e montagem do documento padrão.

Ordem na tela (e no documento exportado): cabeçalho → filtros → indicadores → tabelas → nota.
"""
import customtkinter as ctk

from src.services import relatorio_padrao as padrao
from ui.componentes.cabecalho_relatorio import CabecalhoPadrao
from ui.componentes.indicadores import criar_indicadores


class PainelRelatorio(ctk.CTkFrame):
    TITULO = ""
    ROTULO_PERIODO = padrao.ROTULO_PERIODO     # 'Período', 'Vencimento'...

    def __init__(self, master, servicos):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos
        self._titulo = self.TITULO
        self._periodo = (None, None)
        self._indicadores = {}       # nome -> CartaoResumo, na ordem da tela
        self._tabelas = []           # (título, Tabela)
        self._notas = []             # rótulos de texto explicativo
        self.cabecalho = CabecalhoPadrao(self)
        self.cabecalho.pack(fill="x", pady=(0, 12))
        self.marcar_emissao()

    # ---------- montagem da tela ----------
    def criar_indicadores(self, nomes):
        """Cria os cartões de resumo do relatório (mesmo tamanho em todos) e os registra."""
        cartoes = criar_indicadores(self, nomes)
        self._indicadores.update(cartoes)
        return cartoes

    def registrar_tabela(self, titulo, tabela):
        """Inclui a tabela no documento do relatório (a tela continua mostrando como antes)."""
        self._tabelas.append((titulo, tabela))

    def registrar_nota(self, rotulo):
        """Inclui o texto explicativo (o rótulo da tela) nas observações do documento."""
        self._notas.append(rotulo)

    # ---------- cabeçalho ----------
    def marcar_emissao(self, inicio=None, fim=None, titulo=None):
        """Atualiza o cabeçalho: período consultado e a data/hora em que o relatório foi gerado."""
        if titulo is not None:
            self._titulo = titulo
        self._periodo = (inicio, fim)
        self.cabecalho.atualizar(self._montar_cabecalho())

    def definir_titulo(self, titulo):
        """Troca só o título (para painéis que mostram mais de um relatório)."""
        self.marcar_emissao(*self._periodo, titulo=titulo)

    def _montar_cabecalho(self, agora=None):
        return padrao.montar_cabecalho(self._titulo, *self._periodo, self.ROTULO_PERIODO, agora)

    # ---------- documento ----------
    def documento(self):
        """O que está na tela, no formato padrão (cabeçalho com a hora de agora, indicadores,
        tabelas e observações). É a entrada comum das exportações."""
        return padrao.montar_relatorio(
            self._montar_cabecalho(),
            [(nome, cartao.texto()) for nome, cartao in self._indicadores.items()],
            [padrao.montar_tabela(titulo, tabela.colunas, tabela.linhas_carregadas())
             for titulo, tabela in self._tabelas],
            [rotulo.cget("text") for rotulo in self._notas])
