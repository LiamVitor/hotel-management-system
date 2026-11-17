from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class BloqueioQuarto:
    """Período em que um quarto fica indisponível (manutenção, reforma...)."""
    quarto_id: int
    inicio: datetime        # data e hora em que o bloqueio começa
    fim: datetime           # data e hora em que o bloqueio termina
    motivo: str
    usuario_id: int         # quem registrou o bloqueio
    id: Optional[int] = None
    criado_em: Optional[datetime] = None   # quando foi registrado (o repository preenche)
