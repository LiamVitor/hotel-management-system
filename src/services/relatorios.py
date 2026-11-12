"""Cálculos dos relatórios (funções puras)."""
from datetime import time, timedelta

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


def _faixa_do_bloqueio(bloqueio, inicio, fim):
    """Posições (primeiro, último+1) dos dias do período que o bloqueio toca, ou None.

    Mesma regra de bloqueio_regras: o bloqueio toca a noite do dia D se começa antes do fim
    de D e termina depois do começo de D. Um bloqueio que termina às 00:00 não toca esse dia.
    """
    primeiro_dia = bloqueio.inicio.date()
    ultimo_dia = bloqueio.fim.date()
    if bloqueio.fim.time() == time.min:
        ultimo_dia -= timedelta(days=1)
    primeiro = (max(primeiro_dia, inicio) - inicio).days
    ultimo_mais_um = (min(ultimo_dia, fim) - inicio).days + 1
    return (primeiro, ultimo_mais_um) if primeiro < ultimo_mais_um else None


def _marcar(variacao, faixa):
    if faixa:
        variacao[faixa[0]] += 1
        variacao[faixa[1]] -= 1


def ocupacao_detalhada(reservas, quartos, bloqueios, inicio, fim):
    """Ocupação de cada quarto no período, considerando reservas e bloqueios.

    Cada quarto, em cada dia, está em uma de três situações: ocupado (tem reserva ativa),
    bloqueado (bloqueio no dia, sem reserva) ou disponível. Se o dia tem reserva e bloqueio
    ao mesmo tempo, conta como ocupado. Reservas e bloqueios vêm já filtrados para o período
    (ou não: o que estiver fora é recortado). Custo: reservas + bloqueios + quartos x dias.

    Devolve um dicionário:
      "quartos": uma linha por quarto (ordem de número) com numero, tipo, noites_ocupadas,
                 noites_bloqueadas, noites_disponiveis, percentual_ocupacao (ocupadas sobre
                 as noites não bloqueadas) e receita (valor da reserva dividido pelas noites
                 dela, vezes as noites dentro do período);
      "dias":    lista de (dia, quartos ocupados, quartos bloqueados);
      "totais":  somas, taxa_ocupacao e a média por dia de quartos ocupados/disponíveis/bloqueados.
    """
    total_dias = (fim - inicio).days + 1
    if total_dias <= 0:
        return {"quartos": [], "dias": [], "totais": _totais_vazios()}
    depois_do_fim = fim + timedelta(days=1)
    por_id = {q.id: q for q in quartos}
    reservas_q = {q.id: [0] * (total_dias + 1) for q in quartos}
    bloqueios_q = {q.id: [0] * (total_dias + 1) for q in quartos}
    receita = {q.id: 0.0 for q in quartos}

    for r in _ativas(reservas):
        if r.quarto_id not in por_id:
            continue
        primeiro = (max(r.data_entrada, inicio) - inicio).days
        ultimo_mais_um = (min(r.data_saida, depois_do_fim) - inicio).days
        if primeiro >= ultimo_mais_um:
            continue
        _marcar(reservas_q[r.quarto_id], (primeiro, ultimo_mais_um))
        noites_reserva = (r.data_saida - r.data_entrada).days
        if noites_reserva > 0:
            receita[r.quarto_id] += r.valor_total * (ultimo_mais_um - primeiro) / noites_reserva
    for b in bloqueios:
        if b.quarto_id in por_id:
            _marcar(bloqueios_q[b.quarto_id], _faixa_do_bloqueio(b, inicio, fim))

    ocupados_dia = [0] * total_dias
    bloqueados_dia = [0] * total_dias
    linhas = []
    for q in sorted(quartos, key=lambda q: q.numero):
        ocupadas = bloqueadas = 0
        com_reserva = com_bloqueio = 0
        for i in range(total_dias):
            com_reserva += reservas_q[q.id][i]
            com_bloqueio += bloqueios_q[q.id][i]
            if com_reserva > 0:
                ocupadas += 1
                ocupados_dia[i] += 1
            elif com_bloqueio > 0:
                bloqueadas += 1
                bloqueados_dia[i] += 1
        uteis = total_dias - bloqueadas
        linhas.append({
            "quarto_id": q.id, "numero": q.numero, "tipo": q.tipo,
            "noites_ocupadas": ocupadas, "noites_bloqueadas": bloqueadas,
            "noites_disponiveis": total_dias - ocupadas - bloqueadas,
            "percentual_ocupacao": ocupadas / uteis * 100 if uteis else 0.0,
            "receita": receita[q.id],
        })

    dias = [(inicio + timedelta(days=i), ocupados_dia[i], bloqueados_dia[i])
            for i in range(total_dias)]
    ocupadas = sum(l["noites_ocupadas"] for l in linhas)
    bloqueadas = sum(l["noites_bloqueadas"] for l in linhas)
    total_noites = len(linhas) * total_dias
    uteis = total_noites - bloqueadas
    totais = {
        "dias": total_dias,
        "noites_total": total_noites,
        "noites_ocupadas": ocupadas,
        "noites_bloqueadas": bloqueadas,
        "noites_disponiveis": total_noites - ocupadas - bloqueadas,
        "taxa_ocupacao": ocupadas / uteis * 100 if uteis else 0.0,
        "receita": sum(l["receita"] for l in linhas),
        "media_ocupados": ocupadas / total_dias,
        "media_disponiveis": (total_noites - ocupadas - bloqueadas) / total_dias,
        "media_bloqueados": bloqueadas / total_dias,
    }
    return {"quartos": linhas, "dias": dias, "totais": totais}


def _totais_vazios():
    chaves = ("dias", "noites_total", "noites_ocupadas", "noites_bloqueadas", "noites_disponiveis",
              "taxa_ocupacao", "receita", "media_ocupados", "media_disponiveis", "media_bloqueados")
    return dict.fromkeys(chaves, 0)


def _ocupacao_dos_dias(dias, total_quartos):
    """[(dia, %)] a partir de (dia, ocupados, bloqueados): bloqueado sai do que pode ser ocupado."""
    resultado = []
    for dia, ocupados, bloqueados in dias:
        uteis = total_quartos - bloqueados
        resultado.append((dia, min(100.0, ocupados / uteis * 100) if uteis > 0 else 0.0))
    return resultado


def relatorio_periodo(reservas, quartos, inicio, fim, bloqueios=None):
    """Tudo que a tela de relatórios mostra, calculado de uma vez.

    Valida o período e devolve o resumo (taxa_ocupacao, faturamento, reservas, ticket_medio)
    mais "granularidade" e "barras" para o gráfico.

    Com a lista de bloqueios (pode ser vazia), a ocupação passa a considerar a disponibilidade
    histórica: quarto bloqueado no dia não entra na base do percentual, e o resultado traz
    também "quartos" (indicadores por quarto) e "totais". Sem ela (None), o cálculo é o antigo.
    """
    validar_periodo(inicio, fim)
    if bloqueios is None:
        dias = ocupacao_por_dia(reservas, quartos, inicio, fim)
        resumo = _resumir(dias, reservas, inicio, fim)
    else:
        detalhe = ocupacao_detalhada(reservas, quartos, bloqueios, inicio, fim)
        dias = _ocupacao_dos_dias(detalhe["dias"], len(quartos))
        resumo = _resumir(dias, reservas, inicio, fim)
        resumo["taxa_ocupacao"] = detalhe["totais"]["taxa_ocupacao"]
        resumo["quartos"] = detalhe["quartos"]
        resumo["totais"] = detalhe["totais"]
    granularidade = escolher_granularidade(len(dias))
    resumo["granularidade"] = granularidade
    resumo["barras"] = agrupar_ocupacao(dias, granularidade)
    return resumo
