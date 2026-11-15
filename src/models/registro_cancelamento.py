from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class RegistroCancelamento:
    """Uma reserva cancelada ou de no-show, com o que foi pago, retido e devolvido."""
    reserva_id: int
    hospede_id: int
    hospede: str
    cpf: str
    quarto: str
    situacao: str                        # Cancelada | Não compareceu
    criada_em: Optional[datetime]
    data_entrada: date                   # data prevista de entrada
    evento_em: Optional[datetime]        # quando foi cancelada ou marcada como no-show
    motivo: Optional[str]                # motivo do cancelamento (no-show não tem)
    responsavel: Optional[str]           # quem cancelou ou marcou o no-show
    valor_total: float
    pago_bruto: float                    # soma dos pagamentos
    reembolsado: float                   # soma dos reembolsos já feitos
    retencao_percentual: Optional[float] = None    # None = retenção não registrada (registro antigo)
    valor_retido: Optional[float] = None
    # calculados pelo service
    pago_liquido: float = 0.0            # pago_bruto - reembolsado (o que o hotel tem em mãos)
    a_reembolsar: Optional[float] = None # o que ainda deve ao hóspede: pago_liquido - valor_retido
