from dataclasses import dataclass, field
from datetime import date
from typing import List

from src.models.caixa import Movimentacao, ResumoCaixa


@dataclass
class FluxoPeriodo:
    """Uma linha do fluxo de caixa: o que entrou e saiu em um dia, semana ou mês."""
    inicio: date                 # primeiro dia do grupo (dentro do período consultado)
    fim: date                    # último dia do grupo (dentro do período consultado)
    entradas: float              # pagamentos
    despesas: float
    reembolsos: float
    saldo_final: float           # saldo do caixa no fim do grupo

    @property
    def variacao(self):
        return round(self.entradas - self.despesas - self.reembolsos, 2)


@dataclass
class Demonstrativo:
    """Demonstrativo financeiro de um período: fechamento, fluxo de caixa e movimentações."""
    resumo: ResumoCaixa
    variacao: float              # saldo final - saldo inicial
    granularidade: str           # dia | semana | mês (como o fluxo foi agrupado)
    fluxo: List[FluxoPeriodo] = field(default_factory=list)
    movimentacoes: List[Movimentacao] = field(default_factory=list)   # em ordem cronológica
