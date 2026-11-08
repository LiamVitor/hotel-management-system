"""Regras de pagamento e reembolso (funções puras, fáceis de testar)."""
from dataclasses import dataclass

from src.utils.constantes import (PAGAMENTO_REEMBOLSO, PAGTO_CANCELADA, PAGTO_PAGO, PAGTO_PARCIAL,
                                  PAGTO_PENDENTE)


@dataclass(frozen=True)
class ResumoPagamento:
    valor_total: float
    total_pago: float          # pagamentos menos reembolsos (o que realmente ficou com o hotel)
    saldo: float
    situacao: str              # Pendente | Parcial | Pago | Cancelada
    total_reembolsado: float = 0.0


def arredondar(valor):
    """Dinheiro sempre com 2 casas, para somas de float não gerarem 0,0000001 de sobra."""
    return round(valor + 0.0, 2)


def total_pago(pagamentos):
    """Soma dos pagamentos, descontando os reembolsos."""
    return arredondar(sum(-p.valor if p.tipo == PAGAMENTO_REEMBOLSO else p.valor
                          for p in pagamentos))


def total_reembolsado(pagamentos):
    return arredondar(sum(p.valor for p in pagamentos if p.tipo == PAGAMENTO_REEMBOLSO))


def reembolsavel_por_pagamento(pagamentos):
    """{id do pagamento: quanto dele ainda pode ser reembolsado}.

    Considera só os reembolsos vinculados a cada pagamento (pagamento_origem_id).
    """
    restante = {p.id: p.valor for p in pagamentos if p.tipo != PAGAMENTO_REEMBOLSO}
    for p in pagamentos:
        if p.tipo == PAGAMENTO_REEMBOLSO and p.pagamento_origem_id in restante:
            restante[p.pagamento_origem_id] -= p.valor
    return {pagamento_id: arredondar(valor) for pagamento_id, valor in restante.items()}


def saldo_pendente(valor_total, pago):
    return max(arredondar(valor_total - pago), 0.0)


def situacao_pagamento(valor_total, pago):
    if pago <= 0:
        return PAGTO_PENDENTE
    if saldo_pendente(valor_total, pago) <= 0:
        return PAGTO_PAGO
    return PAGTO_PARCIAL


def resumir(valor_total, pagamentos, cancelada=False):
    """Resumo financeiro da reserva.

    Numa reserva cancelada não há nada a cobrar: o saldo é zero e o que consta em
    total_pago é o valor que ainda está com o hotel (e pode ser reembolsado).
    """
    pago = total_pago(pagamentos)
    reembolsado = total_reembolsado(pagamentos)
    if cancelada:
        return ResumoPagamento(arredondar(valor_total), pago, 0.0, PAGTO_CANCELADA, reembolsado)
    return ResumoPagamento(
        valor_total=arredondar(valor_total),
        total_pago=pago,
        saldo=saldo_pendente(valor_total, pago),
        situacao=situacao_pagamento(valor_total, pago),
        total_reembolsado=reembolsado,
    )
