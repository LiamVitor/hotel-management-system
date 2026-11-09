from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class CategoriaDespesa:
    nome: str
    ativa: bool = True
    id: Optional[int] = None


@dataclass
class DadosDespesa:
    """O que a pessoa preenche no formulário (sem responsável nem datas de auditoria)."""
    data: date
    descricao: str
    valor: float
    categoria_id: int


@dataclass
class Despesa:
    data: date                 # dia da despesa
    descricao: str
    valor: float
    categoria_id: int
    usuario_id: int            # quem lançou
    criada_em: datetime        # quando foi lançada
    id: Optional[int] = None
    atualizada_em: Optional[datetime] = None
    atualizada_por: Optional[int] = None
    excluida_em: Optional[datetime] = None
    excluida_por: Optional[int] = None
