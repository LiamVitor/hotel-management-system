from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class PoliticaRetencao:
    """Regra de retenção definida pela administração (uma definição do histórico).

    Cancelamento com dias_antecedencia dias ou mais antes da data de entrada: nada é retido.
    Com menos antecedência (ou depois da entrada): retém percentual_cancelamento_tardio % do
    valor da reserva. No-show: retém percentual_no_show % do valor da reserva. Em todos os
    casos, só se retém do que o hóspede já pagou (nunca se cobra a diferença).
    """
    dias_antecedencia: int
    percentual_cancelamento_tardio: float
    percentual_no_show: float
    usuario_id: int
    id: Optional[int] = None
    definido_em: Optional[datetime] = None
