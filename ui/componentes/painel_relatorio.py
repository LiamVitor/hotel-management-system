"""Base de todo painel de relatório: cabeçalho padrão no topo e montagem do documento padrão.

Ordem na tela (e no documento exportado): cabeçalho → filtros → indicadores → tabelas → nota.

Exportação: se o painel tem `CHAVE` (uma das constantes REL_* de utils/constantes.py), aparecem os
botões "Exportar PDF" e "Exportar Excel" (só para quem pode ver o relatório). O que sai nos
arquivos é `documento_para_exportar()`, que parte do que está na tela.
"""
import customtkinter as ctk

from src.services import relatorio_padrao as padrao
from ui.componentes.barra_exportacao import BarraExportacao
from ui.componentes.cabecalho_relatorio import CabecalhoPadrao
from ui.componentes.indicadores import criar_indicadores


class PainelRelatorio(ctk.CTkFrame):
    TITULO = ""
    ROTULO_PERIODO = padrao.ROTULO_PERIODO     # 'Período', 'Vencimento'...
    CHAVE = None                               # qual relatório é (decide a permissão de exportar)
    TITULO_EXPORTACAO = None                   # título nos arquivos, se diferente do da tela

    def __init__(self, master, servicos, chave=None):
        super().__init__(master, fg_color="transparent")
        self.servicos = servicos
        self._titulo = self.TITULO
        self._periodo = (None, None)
        self._indicadores = {}       # nome -> CartaoResumo, na ordem da tela
        self._tabelas = []           # (título, Tabela)
        self._notas = []             # rótulos de texto explicativo
        self._filtros = []           # [(rótulo, valor)] dos filtros da última geração
        self.titulo_exportacao = self.TITULO_EXPORTACAO
        self.cabecalho = CabecalhoPadrao(self)
        self.cabecalho.pack(fill="x", pady=(0, 12))
        self.chave = chave or self.CHAVE
        if self.chave:
            self.barra_exportacao = BarraExportacao(self, servicos, self.chave,
                                                    self.documento_para_exportar)
            if self.barra_exportacao.pode:
                self.barra_exportacao.pack(fill="x", pady=(0, 12))
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

    def definir_filtros(self, filtros):
        """Guarda os filtros que valeram na última geração, [(rótulo, valor)], para o documento.

        Chame a cada geração bem-sucedida (junto com `marcar_emissao`): o documento mostra o que
        gerou os números da tela, não o que está digitado e ainda não foi aplicado.
        """
        self._filtros = [(r, v) for r, v in filtros if str(v or "").strip()]

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
            [rotulo.cget("text") for rotulo in self._notas],
            self._filtros)

    def documento_para_exportar(self):
        """O documento que vai para o PDF/Excel: o da tela, com o título de exportação (se o
        painel tiver um). Painéis que mostram só parte dos dados na tela sobrescrevem este método
        para exportar tudo."""
        documento = self.documento()
        if self.titulo_exportacao:
            documento.cabecalho.titulo = self.titulo_exportacao
        return documento
