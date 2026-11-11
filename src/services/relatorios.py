"""Cálculos dos relatórios (funções puras)."""
from datetime import timedelta

from src.services.erros import ErroNegocio
from src.utils.constantes import (GRANULARIDADE_DIA, GRANULARIDADE_MES, GRANULARIDADE_SEMANA,
                                  MAX_ANOS_RELATORIO, MAX_DIAS_RELATORIO, QUARTO_MANUTENCAO,
                                  RESERVA_CANCELADA, RESERVA_NO_SHOW)

# Até quantos dias cada barra do gráfico é um dia / uma semana; acima disso, um mês.
# Mantém o gráfico legível: no máximo ~31 barras por dia, ~18 por semana, 60 por mês.
LIMITE_DIARIO = 31
LIMITE_SEMANAL = 126


def _ativas(reservas):
    """Reservas que ocupam ou ocuparam o quarto (cancelamentos e no-shows ficam de fora)."""
    return [r for r in reservas if r.situacao not in (RESERVA_CANCELADA, RESERVA_NO_SHOW)]


def _total_quartos(quartos):
    disponiveis = [q for q in quartos if q.situacao != QUARTO_MANUTENCAO]
    return max(len(disponiveis), 1)


def validar_periodo(inicio, fim):
    """Levanta ErroNegocio se o período não pode ser consultado."""
    if fim < inicio:
        raise ErroNegocio("A data final não pode ser anterior à data inicial.")
    if (fim - inicio).days + 1 > MAX_DIAS_RELATORIO:
        raise ErroNegocio(f"Escolha um período de até {MAX_ANOS_RELATORIO} anos.")


def ocupacao_por_dia(reservas, quartos, inicio, fim):
    """Lista de (dia, percentual de ocupação) de inicio até fim, inclusive.

    Uma reserva ocupa o quarto de data_entrada até o dia anterior a data_saida. Em vez de
    comparar cada dia com cada reserva, marca onde cada reserva começa e termina dentro do
    período e soma em uma só passada: custo proporcional a reservas + dias.
    """
    total_dias = (fim - inicio).days + 1
    if total_dias <= 0:
        return []
    total_quartos = _total_quartos(quartos)
    variacao = [0] * (total_dias + 1)          # +1 quando uma reserva começa, -1 quando termina
    depois_do_fim = fim + timedelta(days=1)
    for r in _ativas(reservas):
        primeiro = (max(r.data_entrada, inicio) - inicio).days
        ultimo_mais_um = (min(r.data_saida, depois_do_fim) - inicio).days
        if primeiro < ultimo_mais_um:
            variacao[primeiro] += 1
            variacao[ultimo_mais_um] -= 1

    dias, ocupados = [], 0
    for i in range(total_dias):
        ocupados += variacao[i]
        dias.append((inicio + timedelta(days=i), min(100.0, ocupados / total_quartos * 100)))
    return dias


def escolher_granularidade(total_dias):
    """Como o gráfico agrupa o período: por dia, por semana ou por mês."""
    if total_dias <= LIMITE_DIARIO:
        return GRANULARIDADE_DIA
    if total_dias <= LIMITE_SEMANAL:
        return GRANULARIDADE_SEMANA
    return GRANULARIDADE_MES


def agrupar_ocupacao(dias, granularidade):
    """Agrupa a ocupação diária em barras: lista de (primeiro dia do grupo, média do grupo).

    Semana = 7 dias seguidos a partir do início do período; mês = mês do calendário (o
    primeiro e o último podem ser parciais, e então a média vale só para os dias consultados).
    """
    if granularidade == GRANULARIDADE_DIA:
        return list(dias)
    grupos = {}
    for posicao, (dia, pct) in enumerate(dias):
        chave = posicao // 7 if granularidade == GRANULARIDADE_SEMANA else (dia.year, dia.month)
        grupos.setdefault(chave, []).append((dia, pct))
    return [(itens[0][0], sum(p for _, p in itens) / len(itens)) for itens in grupos.values()]


def _resumir(dias, reservas, inicio, fim):
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


def resumo_periodo(reservas, quartos, inicio, fim):
    return _resumir(ocupacao_por_dia(reservas, quartos, inicio, fim), reservas, inicio, fim)


def relatorio_periodo(reservas, quartos, inicio, fim):
    """Tudo que a tela de relatórios mostra, calculado de uma vez.

    Valida o período e devolve o resumo (taxa_ocupacao, faturamento, reservas, ticket_medio)
    mais "granularidade" e "barras" para o gráfico. A ocupação diária é calculada uma só vez.
    """
    validar_periodo(inicio, fim)
    dias = ocupacao_por_dia(reservas, quartos, inicio, fim)
    granularidade = escolher_granularidade(len(dias))
    resumo = _resumir(dias, reservas, inicio, fim)
    resumo["granularidade"] = granularidade
    resumo["barras"] = agrupar_ocupacao(dias, granularidade)
    return resumo
