"""Regras de despesas (funções puras, fáceis de testar)."""
from dataclasses import dataclass


@dataclass(frozen=True)
class LinhaCategoria:
    categoria_id: int
    categoria: str
    total: float
    quantidade: int
    percentual: float          # fatia do total geral, de 0 a 100


@dataclass(frozen=True)
class ResumoDespesas:
    total: float
    quantidade: int
    por_categoria: tuple       # de LinhaCategoria, da que mais gastou para a que menos gastou


def arredondar(valor):
    """Dinheiro sempre com 2 casas, para somas de float não gerarem sobras."""
    return round(valor + 0.0, 2)


def resumir(despesas, nomes_categorias):
    """Total, quantidade e a divisão por categoria de uma lista de despesas.

    nomes_categorias: {categoria_id: nome}
    """
    totais, quantidades = {}, {}
    for d in despesas:
        totais[d.categoria_id] = totais.get(d.categoria_id, 0.0) + d.valor
        quantidades[d.categoria_id] = quantidades.get(d.categoria_id, 0) + 1
    total = arredondar(sum(totais.values()))
    linhas = [
        LinhaCategoria(
            categoria_id=categoria_id,
            categoria=nomes_categorias.get(categoria_id, "—"),
            total=arredondar(valor),
            quantidade=quantidades[categoria_id],
            percentual=round(valor / total * 100, 1) if total else 0.0,
        )
        for categoria_id, valor in totais.items()
    ]
    linhas.sort(key=lambda linha: (-linha.total, linha.categoria))
    return ResumoDespesas(total=total, quantidade=len(despesas), por_categoria=tuple(linhas))
