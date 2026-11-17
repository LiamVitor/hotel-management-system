from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class ResumoReceitas:
    """Reservado x recebido de um período.

    reservado: valor total das reservas ativas (sem cancelamento/no-show) que ENTRAM no período.
    recebido_*: dinheiro que de fato passou pelo caixa no período (pela data do pagamento).
    a_receber: o que ainda falta pagar das reservas do período (nunca negativo por reserva).
    """
    reservado: float = 0.0
    qtd_reservas: int = 0
    recebido_bruto: float = 0.0      # pagamentos
    reembolsado: float = 0.0         # reembolsos
    a_receber: float = 0.0

    @property
    def recebido(self):
        """Receita efetivamente recebida: pagamentos − reembolsos."""
        return round(self.recebido_bruto - self.reembolsado, 2)


@dataclass
class LinhaForma:
    forma: str
    qtd_pagamentos: int
    recebido_bruto: float
    reembolsado: float
    recebido: float              # líquido
    percentual: float            # parte do recebido líquido total


@dataclass
class LinhaQuarto:
    quarto_id: int
    numero: str
    tipo: str
    qtd_reservas: int
    reservado: float
    recebido_bruto: float
    reembolsado: float
    recebido: float
    a_receber: float


@dataclass
class LinhaPeriodo:
    """Um dia ou um mês (o primeiro e o último mês podem ser parciais)."""
    inicio: date
    fim: date
    reservado: float
    recebido_bruto: float
    reembolsado: float
    recebido: float


@dataclass
class Comparacao:
    indicador: str
    atual: float
    anterior: float
    variacao: float
    percentual: Optional[float]      # None quando o período anterior é zero
    monetario: bool = True


@dataclass
class DemonstrativoReceitas:
    inicio: date
    fim: date
    anterior_inicio: date
    anterior_fim: date
    resumo: ResumoReceitas
    anterior: ResumoReceitas
    comparacao: List[Comparacao] = field(default_factory=list)
    por_forma: List[LinhaForma] = field(default_factory=list)
    por_quarto: List[LinhaQuarto] = field(default_factory=list)
    por_dia: List[LinhaPeriodo] = field(default_factory=list)
    por_mes: List[LinhaPeriodo] = field(default_factory=list)
