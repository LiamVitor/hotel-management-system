from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class ReservaDoPeriodo:
    """Uma linha do relatório de reservas por período (reserva + hóspede + quarto + pago)."""
    reserva_id: int
    hospede: str
    cpf: str
    quarto: str
    tipo_quarto: str
    data_entrada: date            # prevista
    data_saida: date              # prevista
    situacao: str                 # Confirmada | Hospedada | Finalizada | Cancelada | Não compareceu
    valor_total: float
    valor_pago: float             # pagamentos menos reembolsos
    criada_em: Optional[datetime] = None

    @property
    def noites(self):
        return (self.data_saida - self.data_entrada).days


@dataclass
class MovimentoHospedagem:
    """Um check-in ou um check-out que realmente aconteceu (com data e hora reais)."""
    reserva_id: int
    hospede: str
    cpf: str
    quarto: str
    tipo: str                     # 'Check-in' | 'Check-out'
    data_hora: datetime           # quando aconteceu de verdade
    data_prevista: date           # entrada prevista (check-in) ou saída prevista (check-out)
    responsavel: str = "—"        # quem registrou (nome do usuário)
