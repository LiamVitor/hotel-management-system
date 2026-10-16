from dataclasses import dataclass
from typing import Optional

# Valores válidos de situação (iguais ao CHECK do schema.sql)
DISPONIVEL = "disponivel"
OCUPADO = "ocupado"
MANUTENCAO = "manutencao"
SITUACOES = (DISPONIVEL, OCUPADO, MANUTENCAO)


@dataclass
class Quarto:
    numero: str
    tipo: str
    capacidade: int
    preco_diaria: float
    situacao: str = DISPONIVEL
    id: Optional[int] = None