from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from src.models.caixa import ResumoCaixa


@dataclass
class IndicadoresInicio:
    """Números do dia que a tela inicial mostra nos cartões."""
    total_quartos: int
    livres: int
    ocupados: int
    reservados: int
    em_manutencao: int
    taxa_ocupacao: float          # ocupados ÷ quartos fora de manutenção, em %
    chegadas_previstas: int       # reservas com entrada hoje (sem cancelamento/no-show)
    chegadas_feitas: int          # dessas, as que já fizeram check-in
    saidas_previstas: int         # hospedagens com saída hoje
    saidas_feitas: int            # dessas, as que já fizeram check-out


@dataclass
class Alerta:
    """Algo que merece atenção de quem está na recepção/gerência."""
    tipo: str                     # ALERTA_* (a tela decide para onde levar a pessoa)
    nivel: str                    # NIVEL_CRITICO | NIVEL_AVISO | NIVEL_INFO
    mensagem: str


@dataclass
class FinanceiroInicio:
    """Resumo financeiro (só para quem pode ver caixa e/ou relatórios; o resto fica None)."""
    caixa: Optional[ResumoCaixa] = None        # caixa do mês, do dia 1 até hoje
    totais_contas: Optional[dict] = None       # totais de contas a receber em aberto
    contas_abertas: list = field(default_factory=list)   # as primeiras, vencimento mais antigo


@dataclass
class ResumoInicio:
    hoje: date
    indicadores: IndicadoresInicio
    reservas_hoje: list                        # [Reserva] que movimentam o dia
    ocupacao_prevista: list                    # [(dia, % de ocupação)] dos próximos dias
    situacao_quartos: dict                     # {situação: quantidade}, na ordem de SITUACOES_QUARTO
    alertas: list                              # [Alerta], do mais urgente ao menos
    financeiro: Optional[FinanceiroInicio] = None
