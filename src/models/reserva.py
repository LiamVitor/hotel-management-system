from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Reserva:
    hospede_id: int
    quarto_id: int
    data_entrada: date
    data_saida: date
    valor_diaria: float
    valor_total: float
    situacao: str = "ativa"        # ativa | cancelada | finalizada
    id: Optional[int] = None