"""Cálculos dos relatórios (funções puras)."""
from datetime import timedelta

from src.utils.constantes import QUARTO_MANUTENCAO, RESERVA_CANCELADA


def _ativas(reservas):
    return [r for r in reservas if r.situacao != RESERVA_CANCELADA]


def _total_quartos(quartos):
    disponiveis = [q for q in quartos if q.situacao != QUARTO_MANUTENCAO]
    return max(len(disponiveis), 1)


def ocupacao_por_dia(reservas, quartos, inicio, fim):
    """Lista de (dia, percentual de ocupação) de inicio até fim, inclusive."""
    ativas = _ativas(reservas)
    total = _total_quartos(quartos)
    dias = []
    dia = inicio
    while dia <= fim:
        ocupados = sum(1 for r in ativas if r.data_entrada <= dia < r.data_saida)
        dias.append((dia, min(100.0, ocupados / total * 100)))
        dia += timedelta(days=1)
    return dias


def resumo_periodo(reservas, quartos, inicio, fim):
    dias = ocupacao_por_dia(reservas, quartos, inicio, fim)
    taxa = sum(p for _, p in dias) / len(dias) if dias else 0.0
    no_periodo = [r for r in _ativas(reservas) if inicio <= r.data_entrada <= fim]
    faturamento = sum(r.valor_total for r in no_periodo)
    quantidade = len(no_periodo)
    ticket = faturamento / quantidade if quantidade else 0.0
    return {
        "taxa_ocupacao": taxa,
        "faturamento": faturamento,
        "reservas": quantidade,
        "ticket_medio": ticket,
    }
