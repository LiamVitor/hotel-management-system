"""Apoio para pesquisas: texto sem acento e faixas de valores (mínimo e máximo)."""
import re
import unicodedata

MENSAGEM_FAIXA_INVALIDA = "Use apenas números nos campos de mínimo e máximo (ex.: 2 ou 180,50)."
MENSAGEM_FAIXA_INVERTIDA = "O valor mínimo não pode ser maior que o máximo."

_NUMERO = re.compile(r"\d+(?:[.,]\d*)?")


def normalizar_texto(texto):
    """Minúsculas e sem acento, para a busca achar 'João' ao digitar 'joao'."""
    base = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in base if unicodedata.category(c) != "Mn")


def _numero_ou_none(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    if not _NUMERO.fullmatch(texto):
        raise ValueError(MENSAGEM_FAIXA_INVALIDA)
    return float(texto.replace(",", "."))


def criar_filtro_faixa(minimo, maximo):
    """Converte os textos de mínimo e máximo em uma função valor -> bool.

    Os dois limites entram na faixa (mínimo 2 e máximo 4 aceita 2, 3 e 4). Qualquer um
    dos lados pode ficar vazio, e então aquele lado fica sem limite. Devolve None se
    os dois estiverem vazios e levanta ValueError se algum não for número ou se
    o mínimo for maior que o máximo.
    """
    menor, maior = _numero_ou_none(minimo), _numero_ou_none(maximo)
    if menor is None and maior is None:
        return None
    if menor is not None and maior is not None and menor > maior:
        raise ValueError(MENSAGEM_FAIXA_INVERTIDA)
    return lambda valor: ((menor is None or valor >= menor)
                          and (maior is None or valor <= maior))


def parece_numerico(texto):
    """True se o texto só tem dígitos e símbolos de CPF/telefone (. - ( ) espaço)."""
    return re.fullmatch(r"[\d\s.\-()]+", texto or "") is not None
