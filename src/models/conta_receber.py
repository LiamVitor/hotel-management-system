from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class ContaReceber:
    """Situação financeira de uma reserva: quanto custa, quanto foi pago e o que falta."""
    reserva_id: int
    hospede_id: int
    hospede: str
    cpf: str
    quarto: str
    data_entrada: date
    data_saida: date
    situacao_reserva: str        # Confirmada | Hospedada | Finalizada
    valor_total: float
    valor_pago: float            # pagamentos menos reembolsos
    data_vencimento: date
    # calculados pelo service
    saldo: float = 0.0
    situacao: Optional[str] = None       # Quitada | A vencer | Vencida
    dias_em_atraso: int = 0
