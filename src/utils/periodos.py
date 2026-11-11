"""Períodos prontos para filtros ('Este mês', 'Mês anterior'...)."""
import calendar
from datetime import date, timedelta

PERSONALIZADO = "Personalizado"
TODO_PERIODO = "Todo o período"
ESTE_MES = "Este mês"
MES_ANTERIOR = "Mês anterior"
ULTIMOS_30_DIAS = "Últimos 30 dias"
ESTE_TRIMESTRE = "Este trimestre"
TRIMESTRE_ANTERIOR = "Trimestre anterior"
ESTE_ANO = "Este ano"
ANO_ANTERIOR = "Ano anterior"

ATALHOS = [PERSONALIZADO, TODO_PERIODO, ESTE_MES, MES_ANTERIOR, ULTIMOS_30_DIAS,
           ESTE_TRIMESTRE, TRIMESTRE_ANTERIOR, ESTE_ANO, ANO_ANTERIOR]
# Relatórios precisam de datas definidas, então "Todo o período" não se aplica a eles
ATALHOS_RELATORIO = [a for a in ATALHOS if a != TODO_PERIODO]


def _inicio_do_trimestre(dia):
    return dia.replace(month=(dia.month - 1) // 3 * 3 + 1, day=1)


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
    if atalho == ESTE_TRIMESTRE:
        return _inicio_do_trimestre(hoje), hoje
    if atalho == TRIMESTRE_ANTERIOR:
        fim = _inicio_do_trimestre(hoje) - timedelta(days=1)
        return _inicio_do_trimestre(fim), fim
    if atalho == ESTE_ANO:
        return hoje.replace(month=1, day=1), hoje
    if atalho == ANO_ANTERIOR:
        return date(hoje.year - 1, 1, 1), date(hoje.year - 1, 12, 31)
    if atalho == TODO_PERIODO:
        return None, None
    raise ValueError(f"Período desconhecido: {atalho}")
