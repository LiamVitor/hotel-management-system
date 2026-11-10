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
    # Confirmada | Hospedada | Finalizada | Cancelada | Não compareceu
    situacao: str = RESERVA_CONFIRMADA
    id: Optional[int] = None
    criada_em: Optional[datetime] = None   # quando a reserva foi lançada (o repository preenche)
    # O que realmente aconteceu (None enquanto não aconteceu, ou em reservas anteriores ao registro)
    checkin_em: Optional[datetime] = None
    checkin_por: Optional[int] = None  # id do usuário que fez o check-in
    checkout_em: Optional[datetime] = None
    checkout_por: Optional[int] = None
    # Cancelamento: quando, quem (id do usuário) e o motivo informado
    cancelada_em: Optional[datetime] = None
    cancelada_por: Optional[int] = None
    cancelamento_motivo: Optional[str] = None
    # No-show: quando foi marcado e por quem (id do usuário)
    noshow_em: Optional[datetime] = None
    noshow_por: Optional[int] = None
