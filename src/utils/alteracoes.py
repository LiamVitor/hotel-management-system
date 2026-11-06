"""Compara o que está salvo com o que foi digitado, para a tela de confirmação de edição."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Alteracao:
    campo: str
    antes: str = ""
    depois: str = ""
    oculto: bool = False   # dado sensível (senha): só avisa que muda, sem mostrar os valores


def calcular_alteracoes(campos):
    """Recebe (rótulo, valor_atual, valor_novo) e devolve só os campos que mudaram."""
    mudancas = []
    for rotulo, antes, depois in campos:
        antes = "" if antes is None else str(antes)
        depois = "" if depois is None else str(depois)
        if antes != depois:
            mudancas.append(Alteracao(rotulo, antes, depois))
    return mudancas
