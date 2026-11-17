from dataclasses import dataclass
from typing import Optional


@dataclass
class Hospede:
    nome: str
    cpf: str
    telefone: Optional[str] = None
    email: Optional[str] = None
    id: Optional[int] = None   # só existe depois de salvar no banco