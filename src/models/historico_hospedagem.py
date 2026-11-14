from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

from src.models.hospede import Hospede


@dataclass
class ItemHistorico:
    """Uma reserva do hóspede, com o quarto e o que já foi pago."""
    reserva_id: int
    quarto_id: int
    quarto: str                    # número do quarto
    tipo_quarto: str
    data_entrada: date             # datas PREVISTAS da reserva
    data_saida: date
    noites: int
    valor_total: float
    valor_pago: float              # pagamentos menos reembolsos
    situacao: str                  # Confirmada | Hospedada | Finalizada | Cancelada | Não compareceu
    hospedagem: bool               # True se o hóspede chegou a se hospedar (Hospedada ou Finalizada)
    checkin_em: Optional[datetime] = None
    checkout_em: Optional[datetime] = None


@dataclass
class HistoricoHospedagem:
    hospede: Hospede
    itens: List[ItemHistorico] = field(default_factory=list)   # mais recente primeiro
    resumo: dict = field(default_factory=dict)                 # veja historico_regras.resumir
