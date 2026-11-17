from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class MovimentoDoDia:
    """Um check-in ou check-out que já foi feito hoje."""
    tipo: str                      # MOVIMENTO_CHECKIN | MOVIMENTO_CHECKOUT
    reserva: object                # Reserva
    quando: datetime
    responsavel: Optional[str] = None


@dataclass
class PainelCheckin:
    """O que a tela de check-in / check-out mostra.

    As contagens são do dia inteiro; só as listas respeitam o texto pesquisado.
    """
    hoje: date
    chegadas: list = field(default_factory=list)       # [Reserva] confirmadas com entrada até hoje
    hospedados: list = field(default_factory=list)     # [Reserva] hospedadas, a que sai antes primeiro
    movimentos: list = field(default_factory=list)     # [MovimentoDoDia], o mais recente primeiro
    chegadas_hoje: int = 0
    chegadas_atrasadas: int = 0
    saidas_hoje: int = 0
    saidas_atrasadas: int = 0
    total_hospedados: int = 0
