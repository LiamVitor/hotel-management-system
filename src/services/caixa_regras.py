"""Regras do caixa (funções puras, sem banco e sem interface)."""
from datetime import timedelta

from src.models.caixa import ResumoCaixa
from src.utils.constantes import (CAIXA_ENTRADA, ORIGEM_DESPESA, ORIGEM_PAGAMENTO,
                                  ORIGEM_REEMBOLSO)


def entradas_e_saidas(por_origem):
    """(entradas, saídas) de um {origem: total}: pagamentos entram; reembolsos e despesas saem."""
    entradas = por_origem.get(ORIGEM_PAGAMENTO, 0.0)
    saidas = por_origem.get(ORIGEM_REEMBOLSO, 0.0) + por_origem.get(ORIGEM_DESPESA, 0.0)
    return round(entradas, 2), round(saidas, 2)


def saldo_acumulado(movimentacoes, saldo_inicial):
    """Preenche saldo_apos em cada movimentação (em ordem cronológica) e devolve a lista."""
    saldo = saldo_inicial
    for m in movimentacoes:
        saldo = round(saldo + (m.valor if m.tipo == CAIXA_ENTRADA else -m.valor), 2)
        m.saldo_apos = saldo
    return movimentacoes


def dia_anterior(dia):
    return dia - timedelta(days=1)


def montar_resumo(inicio, fim, saldo_inicial, data_referencia, movimento_antes, movimento_periodo):
    """Fecha o período: saldo no começo, entradas, saídas e saldo final.

    saldo_inicial / data_referencia: configuração vigente (None se nunca foi definida; então o
    caixa começa em zero e conta todo o histórico). O caixa só existe a partir da data de
    referência: movimentos anteriores a ela ficam de fora, e um período inteiro anterior a ela
    não tem saldo (tudo zero, antes_do_caixa).
    movimento_antes: {origem: total} de data_referencia até o dia anterior a inicio.
    movimento_periodo: {origem: total} do período, já limitado ao que vale (a partir da data
    de referência).
    """
    base = saldo_inicial or 0.0
    if data_referencia is not None and fim < data_referencia:
        return ResumoCaixa(inicio, fim, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, antes_do_caixa=True)
    entradas_antes, saidas_antes = entradas_e_saidas(movimento_antes)
    abertura = round(base + entradas_antes - saidas_antes, 2)
    entradas, saidas = entradas_e_saidas(movimento_periodo)
    return ResumoCaixa(
        inicio=inicio, fim=fim, saldo_inicial=abertura, entradas=entradas, saidas=saidas,
        saldo_final=round(abertura + entradas - saidas, 2),
        entradas_pagamentos=movimento_periodo.get(ORIGEM_PAGAMENTO, 0.0),
        saidas_reembolsos=movimento_periodo.get(ORIGEM_REEMBOLSO, 0.0),
        saidas_despesas=movimento_periodo.get(ORIGEM_DESPESA, 0.0))
