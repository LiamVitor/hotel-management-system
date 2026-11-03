"""Funções de formatação e leitura de valores no padrão brasileiro."""
import re
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


def apenas_digitos(texto):
    """Remove tudo que não for número: '(86) 99912-3456' -> '86999123456'."""
    return re.sub(r"\D", "", texto or "")


# As funções abaixo servem tanto para formatar um valor já salvo quanto para a máscara
# aplicada enquanto a pessoa digita: o separador só aparece quando há dígito depois dele.

def formatar_cpf(texto):
    d = apenas_digitos(texto)[:11]
    saida = d[:3]
    if len(d) > 3:
        saida += "." + d[3:6]
    if len(d) > 6:
        saida += "." + d[6:9]
    if len(d) > 9:
        saida += "-" + d[9:11]
    return saida


def formatar_telefone(texto):
    d = apenas_digitos(texto)[:11]
    if not d:
        return ""
    if len(d) <= 2:
        return f"({d}"
    ddd, resto = d[:2], d[2:]
    if len(d) <= 6:
        return f"({ddd}) {resto}"
    if len(d) <= 10:                                  # fixo: (86) 3222-1234
        return f"({ddd}) {resto[:4]}-{resto[4:]}"
    return f"({ddd}) {resto[:5]}-{resto[5:]}"         # celular: (86) 99912-3456


def mascara_data(texto):
    """'25122026' -> '25/12/2026' (aplicada enquanto a pessoa digita)."""
    d = apenas_digitos(texto)[:8]
    saida = d[:2]
    if len(d) > 2:
        saida += "/" + d[2:4]
    if len(d) > 4:
        saida += "/" + d[4:8]
    return saida
