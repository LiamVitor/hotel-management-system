"""Regras de retenção em cancelamento e no-show (funções puras)."""
from dataclasses import dataclass
from typing import Optional

from src.services.pagamento_regras import arredondar
from src.utils.constantes import RESERVA_CANCELADA, RESERVA_NO_SHOW


@dataclass(frozen=True)
class Retencao:
    """O que a regra manda fazer com o valor que o hóspede já pagou."""
    percentual: float            # % do valor da reserva que a regra manda reter
    valor_retido: float          # o que fica com o hotel (nunca mais que o pago)
    a_devolver: float            # pago - retido
    pago: float                  # o que o hotel tem em mãos (pagamentos - reembolsos)
    politica_id: Optional[int] = None


def antecedencia_dias(data_entrada, data_evento):
    """Quantos dias antes da entrada o cancelamento foi feito (negativo = depois da entrada)."""
    return (data_entrada - data_evento).days


def percentual_aplicavel(politica, situacao, antecedencia):
    """% do valor da reserva que a regra manda reter (0 se não há regra definida)."""
    if politica is None:
        return 0.0
    if situacao == RESERVA_NO_SHOW:
        return politica.percentual_no_show
    if situacao == RESERVA_CANCELADA:
        if antecedencia >= politica.dias_antecedencia:
            return 0.0
        return politica.percentual_cancelamento_tardio
    raise ValueError("A retenção só existe em cancelamento e no-show.")


def calcular(politica, situacao, valor_total, pago, antecedencia=0):
    """Retenção de uma reserva cancelada (situacao Cancelada) ou de no-show.

    O valor retido é o percentual da reserva, limitado ao que foi pago: quem não pagou nada
    não fica devendo, e o hotel nunca retém mais do que recebeu.
    """
    percentual = percentual_aplicavel(politica, situacao, antecedencia)
    pago = max(arredondar(pago), 0.0)
    retido = arredondar(min(valor_total * percentual / 100, pago))
    return Retencao(percentual=percentual, valor_retido=retido,
                    a_devolver=arredondar(pago - retido), pago=pago,
                    politica_id=politica.id if politica else None)
