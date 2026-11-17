"""Regras do demonstrativo de receitas (funções puras sobre as linhas agregadas do banco)."""
from datetime import date, timedelta

from src.models.demonstrativo_receitas import (Comparacao, LinhaForma, LinhaPeriodo, LinhaQuarto,
                                               ResumoReceitas)
from src.services.pagamento_regras import arredondar
from src.utils.constantes import PAGAMENTO_REEMBOLSO

LIMITE_DIAS_COMPLETO = 62   # até aqui o detalhamento diário traz todos os dias; acima, só os com movimento


def periodo_anterior(inicio, fim):
    """Período imediatamente anterior, com o mesmo número de dias."""
    dias = (fim - inicio).days + 1
    ant_fim = inicio - timedelta(days=1)
    return ant_fim - timedelta(days=dias - 1), ant_fim


def _dia(texto):
    return texto if isinstance(texto, date) else date.fromisoformat(texto)


def _separar(recebimentos):
    """(pagamentos, reembolsos) entre as linhas de recebimento."""
    reembolsos = [l for l in recebimentos if l["tipo"] == PAGAMENTO_REEMBOLSO]
    pagamentos = [l for l in recebimentos if l["tipo"] != PAGAMENTO_REEMBOLSO]
    return pagamentos, reembolsos


def resumir(reservado, recebimentos):
    pagamentos, reembolsos = _separar(recebimentos)
    return ResumoReceitas(
        reservado=arredondar(sum(l["reservado"] for l in reservado)),
        qtd_reservas=sum(l["qtd"] for l in reservado),
        recebido_bruto=arredondar(sum(l["total"] for l in pagamentos)),
        reembolsado=arredondar(sum(l["total"] for l in reembolsos)),
        a_receber=arredondar(sum(l["a_receber"] for l in reservado)))


def por_forma(recebimentos):
    """Recebimentos agrupados por forma de pagamento, da maior para a menor receita líquida."""
    formas = {}
    for l in recebimentos:
        f = formas.setdefault(l["forma"], {"qtd": 0, "bruto": 0.0, "reemb": 0.0})
        if l["tipo"] == PAGAMENTO_REEMBOLSO:
            f["reemb"] += l["total"]
        else:
            f["bruto"] += l["total"]
            f["qtd"] += l["qtd"]
    total = sum(f["bruto"] - f["reemb"] for f in formas.values())
    linhas = [LinhaForma(
        forma=nome, qtd_pagamentos=f["qtd"], recebido_bruto=arredondar(f["bruto"]),
        reembolsado=arredondar(f["reemb"]), recebido=arredondar(f["bruto"] - f["reemb"]),
        percentual=round((f["bruto"] - f["reemb"]) / total * 100, 1) if total > 0 else 0.0)
        for nome, f in formas.items()]
    return sorted(linhas, key=lambda x: (-x.recebido, x.forma))


def por_quarto(reservado, recebimentos):
    """Reservado e recebido por quarto, em ordem de número (quartos sem movimento ficam de fora)."""
    quartos = {}

    def item(l, tipo):
        return quartos.setdefault(l["quarto_id"], {
            "numero": l["numero"], "tipo": l[tipo], "qtd": 0, "reservado": 0.0,
            "bruto": 0.0, "reemb": 0.0, "a_receber": 0.0})

    for l in reservado:
        q = item(l, "tipo")
        q["qtd"] += l["qtd"]
        q["reservado"] += l["reservado"]
        q["a_receber"] += l["a_receber"]
    for l in recebimentos:
        q = item(l, "tipo_quarto")
        q["reemb" if l["tipo"] == PAGAMENTO_REEMBOLSO else "bruto"] += l["total"]
    linhas = [LinhaQuarto(
        quarto_id=qid, numero=q["numero"], tipo=q["tipo"], qtd_reservas=q["qtd"],
        reservado=arredondar(q["reservado"]), recebido_bruto=arredondar(q["bruto"]),
        reembolsado=arredondar(q["reemb"]), recebido=arredondar(q["bruto"] - q["reemb"]),
        a_receber=arredondar(q["a_receber"])) for qid, q in quartos.items()]
    return sorted(linhas, key=lambda x: (len(x.numero), x.numero))


def _acumular(grupos, chave, primeiro, ultimo, reservado=0.0, bruto=0.0, reemb=0.0):
    g = grupos.setdefault(chave, [primeiro, ultimo, 0.0, 0.0, 0.0])
    g[2] += reservado
    g[3] += bruto
    g[4] += reemb


def _linhas(grupos):
    return [LinhaPeriodo(g[0], g[1], arredondar(g[2]), arredondar(g[3]), arredondar(g[4]),
                         arredondar(g[3] - g[4])) for _, g in sorted(grupos.items())]


def por_dia(reservado, recebimentos, inicio, fim):
    """Um item por dia: reservado (pela entrada) e recebido (pela data do pagamento).

    Períodos até LIMITE_DIAS_COMPLETO dias trazem todos os dias; acima, só os com movimento.
    """
    grupos = {}
    if (fim - inicio).days + 1 <= LIMITE_DIAS_COMPLETO:
        dia = inicio
        while dia <= fim:
            grupos[dia] = [dia, dia, 0.0, 0.0, 0.0]
            dia += timedelta(days=1)
    for l in reservado:
        d = _dia(l["dia"])
        _acumular(grupos, d, d, d, reservado=l["reservado"])
    for l in recebimentos:
        d = _dia(l["dia"])
        if l["tipo"] == PAGAMENTO_REEMBOLSO:
            _acumular(grupos, d, d, d, reemb=l["total"])
        else:
            _acumular(grupos, d, d, d, bruto=l["total"])
    return _linhas(grupos)


def por_mes(reservado, recebimentos, inicio, fim):
    """Um item por mês do calendário dentro do período (o primeiro e o último podem ser parciais)."""
    grupos = {}
    dia = inicio.replace(day=1)
    while dia <= fim:
        proximo = (dia.replace(day=28) + timedelta(days=4)).replace(day=1)
        grupos[(dia.year, dia.month)] = [max(dia, inicio), min(proximo - timedelta(days=1), fim),
                                         0.0, 0.0, 0.0]
        dia = proximo
    for l in reservado:
        d = _dia(l["dia"])
        _acumular(grupos, (d.year, d.month), d, d, reservado=l["reservado"])
    for l in recebimentos:
        d = _dia(l["dia"])
        if l["tipo"] == PAGAMENTO_REEMBOLSO:
            _acumular(grupos, (d.year, d.month), d, d, reemb=l["total"])
        else:
            _acumular(grupos, (d.year, d.month), d, d, bruto=l["total"])
    return _linhas(grupos)


def _variacao(indicador, atual, anterior, monetario=True):
    atual, anterior = arredondar(atual), arredondar(anterior)
    variacao = arredondar(atual - anterior)
    percentual = round(variacao / anterior * 100, 1) if anterior else None
    return Comparacao(indicador, atual, anterior, variacao, percentual, monetario)


def comparar(atual, anterior):
    """Indicadores do período lado a lado com os do período anterior."""
    return [
        _variacao("Valor reservado", atual.reservado, anterior.reservado),
        _variacao("Reservas", atual.qtd_reservas, anterior.qtd_reservas, monetario=False),
        _variacao("Recebido (pagamentos)", atual.recebido_bruto, anterior.recebido_bruto),
        _variacao("Reembolsos", atual.reembolsado, anterior.reembolsado),
        _variacao("Receita recebida (líquida)", atual.recebido, anterior.recebido),
        _variacao("A receber das reservas do período", atual.a_receber, anterior.a_receber),
    ]
