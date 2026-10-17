from dataclasses import dataclass
from typing import Optional

from src.utils.constantes import (QUARTO_DISPONIVEL, QUARTO_MANUTENCAO, QUARTO_OCUPADO,
                                  QUARTO_RESERVADO, SITUACOES_QUARTO)

# Mantidos com os nomes antigos para não quebrar imports existentes
DISPONIVEL = QUARTO_DISPONIVEL
OCUPADO = QUARTO_OCUPADO
RESERVADO = QUARTO_RESERVADO
MANUTENCAO = QUARTO_MANUTENCAO
SITUACOES = tuple(SITUACOES_QUARTO)


@dataclass
class Quarto:
    numero: str
    tipo: str
    capacidade: int
    preco_diaria: float
    situacao: str = DISPONIVEL
    id: Optional[int] = None