"""Funções de formatação e leitura de valores no padrão brasileiro."""
from datetime import datetime


def formatar_moeda(valor):
    texto = f"{valor:,.2f}"
    return "R$ " + texto.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_percentual(valor):
    return f"{valor:.1f}%".replace(".", ",")


def formatar_data(data):
    return data.strftime("%d/%m/%Y")


def ler_data(texto):
    """Converte 'dd/mm/aaaa' em date. Levanta ValueError se for inválida."""
    try:
        return datetime.strptime(texto.strip(), "%d/%m/%Y").date()
    except ValueError:
        raise ValueError("Informe a data no formato dd/mm/aaaa.")
