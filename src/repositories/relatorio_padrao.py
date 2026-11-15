"""Estrutura padrão de um relatório: o que a tela mostra e o que as exportações vão imprimir."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

ALINHA_ESQUERDA = "esquerda"
ALINHA_DIREITA = "direita"


@dataclass
class CabecalhoRelatorio:
    """Cabeçalho padrão: pousada (nome e logotipo), título, período, geração e responsável."""
    nome_pousada: str
    arquivo_logo: Optional[str]      # caminho do logotipo; None = sem logotipo (usa o monograma)
    titulo: str
    periodo: str                     # texto pronto, ex.: 'Período: 01/11/2026 a 15/11/2026'
    gerado_em: datetime
    emitido_por: str                 # 'Nome (Perfil)'


@dataclass
class Indicador:
    rotulo: str
    valor: str                       # já formatado (moeda, percentual...)


@dataclass
class ColunaRelatorio:
    titulo: str
    chave: str
    largura: int                     # largura relativa (na tela, em pixels)
    alinhamento: str = ALINHA_ESQUERDA


@dataclass
class TabelaRelatorio:
    titulo: str
    colunas: List[ColunaRelatorio]
    linhas: List[dict]


@dataclass
class RelatorioPadrao:
    """Cabeçalho, indicadores, tabelas e observações, nesta ordem."""
    cabecalho: CabecalhoRelatorio
    indicadores: List[Indicador] = field(default_factory=list)
    tabelas: List[TabelaRelatorio] = field(default_factory=list)
    observacoes: List[str] = field(default_factory=list)


@dataclass
class RodapePagina:
    esquerda: str                    # pousada e título
    centro: str                      # quem emitiu e quando
    direita: str                     # 'Página 2 de 5'


@dataclass
class BlocoPagina:
    """Pedaço de uma tabela que cabe em uma página (continuacao = veio da página anterior)."""
    tabela: TabelaRelatorio
    linhas: List[dict]
    continuacao: bool = False


@dataclass
class Pagina:
    numero: int
    total: int
    com_cabecalho: bool              # só a primeira página leva cabeçalho e indicadores
    blocos: List[BlocoPagina] = field(default_factory=list)
    rodape: Optional[RodapePagina] = None
