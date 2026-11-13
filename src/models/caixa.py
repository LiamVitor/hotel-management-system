from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class SaldoInicial:
    """Saldo que o caixa tinha no começo de data_referencia (uma configuração do histórico)."""
    valor: float
    data_referencia: date
    usuario_id: int
    id: Optional[int] = None
    definido_em: Optional[datetime] = None


@dataclass
class Movimentacao:
    """Uma entrada ou saída do caixa. O valor é sempre positivo; o tipo diz o sentido."""
    data_hora: datetime
    tipo: str                    # Entrada | Saída
    origem: str                  # Pagamento | Reembolso | Despesa
    origem_id: int
    valor: float
    descricao: str
    responsavel: Optional[str] = None
    reserva_id: Optional[int] = None
    saldo_apos: Optional[float] = None    # saldo do caixa logo depois desta movimentação


@dataclass
class ResumoCaixa:
    """Fechamento de um período do caixa."""
    inicio: date
    fim: date
    saldo_inicial: float         # saldo no começo do período
    entradas: float
    saidas: float
    saldo_final: float
    entradas_pagamentos: float
    saidas_reembolsos: float
    saidas_despesas: float
    antes_do_caixa: bool = False   # período inteiro anterior à data do saldo inicial
