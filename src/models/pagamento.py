from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.utils.constantes import PAGAMENTO_NORMAL


@dataclass
class Pagamento:
    reserva_id: int
    valor: float
    forma: str
    usuario_id: int            # quem lançou
    data_hora: datetime        # quando foi lançado
    tipo: str = PAGAMENTO_NORMAL   # Pagamento | Reembolso
    id: Optional[int] = None
    motivo: Optional[str] = None               # obrigatório nos reembolsos
    pagamento_origem_id: Optional[int] = None  # reembolso: qual pagamento está sendo devolvido
