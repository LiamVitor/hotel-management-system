"""Períodos prontos para filtros ('Este mês', 'Mês anterior'...)."""
import calendar
from datetime import date, timedelta

PERSONALIZADO = "Personalizado"
TODO_PERIODO = "Todo o período"
ESTE_MES = "Este mês"
MES_ANTERIOR = "Mês anterior"
ULTIMOS_30_DIAS = "Últimos 30 dias"
ESTE_ANO = "Este ano"

ATALHOS = [PERSONALIZADO, TODO_PERIODO, ESTE_MES, MES_ANTERIOR, ULTIMOS_30_DIAS, ESTE_ANO]


def periodo_do_atalho(atalho, hoje=None):
    """(data inicial, data final) do atalho; (None, None) = sem limite.

    Os períodos que ainda estão em andamento terminam hoje.
    """
    hoje = hoje or date.today()
    if atalho == ESTE_MES:
        return hoje.replace(day=1), hoje
    if atalho == MES_ANTERIOR:
        fim = hoje.replace(day=1) - timedelta(days=1)
        return fim.replace(day=1), fim
    if atalho == ULTIMOS_30_DIAS:
        return hoje - timedelta(days=29), hoje
    if atalho == ESTE_ANO:
        return hoje.replace(month=1, day=1), hoje
    if atalho == TODO_PERIODO:
        return None, None
    raise ValueError(f"Período desconhecido: {atalho}")
