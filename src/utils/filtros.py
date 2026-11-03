"""Apoio para pesquisas: texto sem acento e filtros numéricos como '>500 e <570'."""
import re
import unicodedata

MENSAGEM_FILTRO_NUMERICO = ("Filtro inválido. Use um número (2), uma comparação (>2, <=4), "
                            "uma faixa (2-4) ou duas condições (>500 e <570).")

_NUMERO = r"\d+(?:[.,]\d+)?"
_CONDICAO = re.compile(rf"(>=|<=|>|<|=)?\s*({_NUMERO})")
_FAIXA = re.compile(rf"({_NUMERO})\s*-\s*({_NUMERO})")

_COMPARACOES = {
    ">": lambda valor, limite: valor > limite,
    ">=": lambda valor, limite: valor >= limite,
    "<": lambda valor, limite: valor < limite,
    "<=": lambda valor, limite: valor <= limite,
    "=": lambda valor, limite: valor == limite,
}


def normalizar_texto(texto):
    """Minúsculas e sem acento, para a busca achar 'João' ao digitar 'joao'."""
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def _numero(texto):
    return float(texto.replace(",", "."))


def criar_filtro_numerico(texto):
    """Converte o texto digitado em uma função valor -> bool.

    Aceita: '2' (igual), '>2', '>=2', '<570', '2-4' (faixa) e '>500 e <570'.
    Devolve None se o texto estiver vazio e levanta ValueError se for inválido.
    """
    texto = (texto or "").strip().lower()
    if not texto:
        return None

    faixa = _FAIXA.fullmatch(texto)
    if faixa:
        a, b = _numero(faixa.group(1)), _numero(faixa.group(2))
        minimo, maximo = min(a, b), max(a, b)
        return lambda valor: minimo <= valor <= maximo

    texto = re.sub(r"\s+e\s+", " ", texto)
    condicoes = [(op or "=", _numero(num)) for op, num in _CONDICAO.findall(texto)]
    sobra = _CONDICAO.sub("", texto).strip()
    if not condicoes or sobra:
        raise ValueError(MENSAGEM_FILTRO_NUMERICO)
    return lambda valor: all(_COMPARACOES[op](valor, limite) for op, limite in condicoes)


def parece_numerico(texto):
    """True se o texto só tem dígitos e símbolos de CPF/telefone (. - ( ) espaço)."""
    return re.fullmatch(r"[\d\s.\-()]+", texto or "") is not None
