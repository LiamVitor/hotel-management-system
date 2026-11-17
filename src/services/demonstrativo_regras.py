"""Regras do demonstrativo financeiro e do fluxo de caixa (funções puras)."""
from datetime import timedelta

from src.models.demonstrativo import FluxoPeriodo
from src.services.pagamento_regras import arredondar
from src.utils.constantes import (GRANULARIDADE_DIA, GRANULARIDADE_MES, GRANULARIDADE_SEMANA,
                                  ORIGEM_DESPESA, ORIGEM_PAGAMENTO, ORIGEM_REEMBOLSO)


def chave_do_grupo(dia, inicio, granularidade):
    """Em que grupo do fluxo o dia cai: o próprio dia, bloco de 7 dias ou mês do calendário."""
    if granularidade == GRANULARIDADE_DIA:
        return dia
    if granularidade == GRANULARIDADE_SEMANA:
        return (dia - inicio).days // 7
    return (dia.year, dia.month)


def agrupar_fluxo(movimentacoes, inicio, fim, saldo_inicial, granularidade):
    """Fluxo de caixa de inicio a fim: uma linha por grupo, inclusive os sem movimento.

    movimentacoes: as do período (qualquer ordem). Cada grupo traz entradas (pagamentos),
    despesas e reembolsos e o saldo do caixa no fim dele, partindo de saldo_inicial. Semana =
    7 dias seguidos a partir do início; mês = mês do calendário (o primeiro e o último podem
    ser parciais). Custo: movimentações + dias.
    """
    por_chave = {}
    for m in movimentacoes:
        totais = por_chave.setdefault(chave_do_grupo(m.data_hora.date(), inicio, granularidade),
                                      {ORIGEM_PAGAMENTO: 0.0, ORIGEM_DESPESA: 0.0,
                                       ORIGEM_REEMBOLSO: 0.0})
        totais[m.origem] += m.valor

    grupos = []                       # [chave, primeiro dia, último dia]
    dia = inicio
    while dia <= fim:
        chave = chave_do_grupo(dia, inicio, granularidade)
        if grupos and grupos[-1][0] == chave:
            grupos[-1][2] = dia
        else:
            grupos.append([chave, dia, dia])
        dia += timedelta(days=1)

    fluxo, saldo = [], saldo_inicial
    for chave, primeiro, ultimo in grupos:
        t = por_chave.get(chave, {})
        entradas = arredondar(t.get(ORIGEM_PAGAMENTO, 0.0))
        despesas = arredondar(t.get(ORIGEM_DESPESA, 0.0))
        reembolsos = arredondar(t.get(ORIGEM_REEMBOLSO, 0.0))
        saldo = arredondar(saldo + entradas - despesas - reembolsos)
        fluxo.append(FluxoPeriodo(primeiro, ultimo, entradas, despesas, reembolsos, saldo))
    return fluxo
