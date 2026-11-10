from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from src.utils.constantes import RESERVA_CONFIRMADA


@dataclass
class Reserva:
    hospede_id: int
    quarto_id: int
    data_entrada: date                 # data PREVISTA de entrada
    data_saida: date                   # data PREVISTA de saída
    valor_diaria: float
    valor_total: float
    situacao: str = RESERVA_CONFIRMADA   # Confirmada | Hospedada | Finalizada | Cancelada
    id: Optional[int] = None
    # O que realmente aconteceu (None enquanto não aconteceu, ou em reservas anteriores ao registro)
    checkin_em: Optional[datetime] = None
    checkin_por: Optional[int] = None  # id do usuário que fez o check-in
    checkout_em: Optional[datetime] = None
    checkout_por: Optional[int] = None
