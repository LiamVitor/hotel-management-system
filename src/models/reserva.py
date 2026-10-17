from dataclasses import dataclass
from datetime import date
from typing import Optional

from src.utils.constantes import RESERVA_CONFIRMADA


@dataclass
class Reserva:
    hospede_id: int
    quarto_id: int
    data_entrada: date
    data_saida: date
    valor_diaria: float
    valor_total: float
    situacao: str = RESERVA_CONFIRMADA   # Confirmada | Hospedada | Finalizada | Cancelada
    id: Optional[int] = None
