"""Regras de pagamento (funções puras, fáceis de testar)."""
from dataclasses import dataclass

from src.utils.constantes import (PAGAMENTO_REEMBOLSO, PAGTO_PAGO, PAGTO_PARCIAL,
                                  PAGTO_PENDENTE)


@dataclass(frozen=True)
class ResumoPagamento:
    valor_total: float
    total_pago: float
    saldo: float
    situacao: str        # Pendente | Parcial | Pago


def arredondar(valor):
    """Dinheiro sempre com 2 casas, para somas de float não gerarem 0,0000001 de sobra."""
    return round(valor + 0.0, 2)


def total_pago(pagamentos):
    """Soma dos pagamentos, descontando eventuais reembolsos."""
    return arredondar(sum(-p.valor if p.tipo == PAGAMENTO_REEMBOLSO else p.valor
                          for p in pagamentos))


def saldo_pendente(valor_total, pago):
    return max(arredondar(valor_total - pago), 0.0)


def situacao_pagamento(valor_total, pago):
    if pago <= 0:
        return PAGTO_PENDENTE
    if saldo_pendente(valor_total, pago) <= 0:
        return PAGTO_PAGO
    return PAGTO_PARCIAL


def resumir(valor_total, pagamentos):
    pago = total_pago(pagamentos)
    return ResumoPagamento(
        valor_total=arredondar(valor_total),
        total_pago=pago,
        saldo=saldo_pendente(valor_total, pago),
        situacao=situacao_pagamento(valor_total, pago),
    )
