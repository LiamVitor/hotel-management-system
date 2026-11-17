"""Regras da exportação de relatórios (funções puras, sem PDF/Excel e sem tela).

A exportação parte do `RelatorioPadrao` (o mesmo que a tela mostra), então os textos já vêm
formatados ('R$ 1.234,56', '12,5%', '01/11/2026'). Para a planilha ter números e datas de
verdade (e assim ordenar e filtrar direito), `interpretar_valor` lê de volta o que a tela mostrou:
o valor exportado é sempre o mesmo valor apresentado.
"""
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import Any, List, Optional

from src.utils.constantes import (FORMATO_EXCEL, FORMATO_PDF, REL_CANCELAMENTOS,
                                  REL_CHECKINS_CHECKOUTS, REL_CONTAS_RECEBER, REL_DEMONSTRATIVO,
                                  REL_HISTORICO_HOSPEDAGEM, REL_OCUPACAO, REL_RECEITAS,
                                  REL_RESERVAS)

EXTENSAO = {FORMATO_PDF: ".pdf", FORMATO_EXCEL: ".xlsx"}
NOME_DO_FORMATO = {FORMATO_PDF: "PDF", FORMATO_EXCEL: "Excel"}

# Quem pode exportar um relatório é quem pode vê-lo: a exportação nunca abre mais dados do que a
# tela. O service confere isto de novo (a tela só esconde os botões).
PERMISSAO_DO_RELATORIO = {
    REL_OCUPACAO: "relatorios.ver",
    REL_RESERVAS: "relatorios.ver",
    REL_CHECKINS_CHECKOUTS: "relatorios.ver",
    REL_RECEITAS: "relatorios.ver",
    REL_DEMONSTRATIVO: "relatorios.ver",
    REL_CONTAS_RECEBER: "relatorios.ver",
    REL_HISTORICO_HOSPEDAGEM: "hospedes.ver",
    REL_CANCELAMENTOS: "relatorios.ver",
}

ROTULO_TOTAL = "Total"
SEM_VALOR = "—"

# ---------- tipos de célula ----------
TEXTO = "texto"
INTEIRO = "inteiro"
DECIMAL = "decimal"
MOEDA = "moeda"
PERCENTUAL = "percentual"
DATA = "data"
DATA_HORA = "data_hora"

# formatos de número do Excel
FORMATO_MOEDA = '"R$" #,##0.00;-"R$" #,##0.00'
FORMATO_INTEIRO = "0;-0"
FORMATO_DATA = "dd/mm/yyyy"
FORMATO_DATA_HORA = "dd/mm/yyyy hh:mm"

_SINAIS = {"+": 1, "-": -1, "−": -1}      # o hífen e o sinal de menos (U+2212) que a tela usa
_SINAL = r"[+\-−]"
_NUM_BR = r"(?:\d{1,3}(?:\.\d{3})+|\d+)"
_RE_MOEDA = re.compile(rf"^(?P<s1>{_SINAL})?\s*R\$\s*(?P<s2>{_SINAL})?\s*(?P<n>{_NUM_BR},\d{{2}})$")
_RE_PERCENTUAL = re.compile(rf"^(?P<s>{_SINAL})?\s*(?P<n>\d+(?:,\d+)?)\s*%$")
_RE_INTEIRO = re.compile(rf"^(?P<s>{_SINAL})?\s*(?P<n>\d+)$")
_RE_DECIMAL = re.compile(rf"^(?P<s>{_SINAL})?\s*(?P<n>\d+[.,]\d{{1,2}})$")
_RE_DATA = re.compile(r"^\d{2}/\d{2}/\d{4}$")
_RE_DATA_HORA = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$")


@dataclass
class ValorCelula:
    tipo: str
    valor: Any                       # str, int, float (percentual como fração), date ou datetime
    formato: Optional[str] = None    # formato de número do Excel
    original: str = ""               # o texto que a tela mostrou


def _sinal(*simbolos):
    for s in simbolos:
        if s:
            return _SINAIS[s]
    return 1


def _numero(texto):
    """'1.234,56' -> 1234.56."""
    return float(texto.replace(".", "").replace(",", "."))


def interpretar_valor(texto) -> ValorCelula:
    """Lê de volta um texto formatado pela tela: moeda, percentual, data, data e hora ou número.

    O que não for reconhecido com certeza continua texto (códigos como '0001', nomes, motivos...).
    """
    original = "" if texto is None else str(texto)
    t = original.strip()
    if not t or t == SEM_VALOR:
        return ValorCelula(TEXTO, original, None, original)

    m = _RE_MOEDA.match(t)
    if m:
        valor = round(_sinal(m["s1"], m["s2"]) * _numero(m["n"]), 2)
        return ValorCelula(MOEDA, valor, FORMATO_MOEDA, original)

    m = _RE_PERCENTUAL.match(t)
    if m:
        casas = len(m["n"].split(",")[1]) if "," in m["n"] else 0
        valor = _sinal(m["s"]) * _numero(m["n"]) / 100
        formato = "0." + "0" * casas + "%" if casas else "0%"
        return ValorCelula(PERCENTUAL, round(valor, casas + 2), formato, original)

    if _RE_DATA_HORA.match(t):
        try:
            return ValorCelula(DATA_HORA, datetime.strptime(t, "%d/%m/%Y %H:%M"),
                               FORMATO_DATA_HORA, original)
        except ValueError:
            return ValorCelula(TEXTO, original, None, original)
    if _RE_DATA.match(t):
        try:
            return ValorCelula(DATA, datetime.strptime(t, "%d/%m/%Y").date(), FORMATO_DATA, original)
        except ValueError:
            return ValorCelula(TEXTO, original, None, original)

    m = _RE_INTEIRO.match(t)
    if m:
        digitos = m["n"]
        if len(digitos) > 1 and digitos.startswith("0"):       # '0001': código, não número
            return ValorCelula(TEXTO, original, None, original)
        return ValorCelula(INTEIRO, _sinal(m["s"]) * int(digitos), FORMATO_INTEIRO, original)

    m = _RE_DECIMAL.match(t)
    if m:
        numero = m["n"].replace(",", ".")
        casas = len(numero.split(".")[1])
        return ValorCelula(DECIMAL, _sinal(m["s"]) * float(numero),
                           "0." + "0" * casas, original)
    return ValorCelula(TEXTO, original, None, original)


def interpretar_coluna(valores) -> List[ValorCelula]:
    """Interpreta uma coluna inteira. Moeda, percentual e data valem célula a célula; já os
    números simples só viram número se a coluna toda for numérica (a coluna 'Quarto' com '101' e
    'A1' continua texto, para não misturar tipos na ordenação)."""
    celulas = [interpretar_valor(v) for v in valores]
    tem_texto = any(c.tipo == TEXTO and c.original.strip() not in ("", SEM_VALOR) for c in celulas)
    if tem_texto:
        celulas = [ValorCelula(TEXTO, c.original, None, c.original)
                   if c.tipo in (INTEIRO, DECIMAL) and c.original.strip()[:1] not in "+-−" else c
                   for c in celulas]
    return celulas


def separar_total(tabela):
    """(linhas, linha_total): a linha 'Total' no fim da tabela sai da lista, para não ser
    ordenada nem filtrada junto com os dados na planilha. Sem linha de total: (linhas, None)."""
    linhas = list(tabela.linhas)
    if len(linhas) > 1 and tabela.colunas:
        primeira = str(linhas[-1].get(tabela.colunas[0].chave, "")).strip()
        if primeira.lower() == ROTULO_TOTAL.lower():
            return linhas[:-1], linhas[-1]
    return linhas, None


# ---------- nomes ----------
def _sem_acentos(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _slug(texto):
    texto = re.sub(r"[^a-z0-9]+", "-", _sem_acentos(texto).lower())
    return texto.strip("-") or "relatorio"


def nome_do_arquivo(relatorio, formato):
    """'relatorio-contas-a-receber_2026-11-01_a_2026-11-15.pdf'. Sem datas no período, usa o dia
    em que foi gerado."""
    cab = relatorio.cabecalho
    datas = re.findall(r"\d{2}/\d{2}/\d{4}", cab.periodo or "")
    iso = []
    for texto in datas:
        try:
            iso.append(datetime.strptime(texto, "%d/%m/%Y").date().isoformat())
        except ValueError:
            pass
    if len(iso) >= 2:
        sufixo = f"{iso[0]}_a_{iso[1]}"
    elif len(iso) == 1:
        sufixo = iso[0]
    else:
        sufixo = cab.gerado_em.date().isoformat()
    return f"relatorio-{_slug(cab.titulo)}_{sufixo}{EXTENSAO[formato]}"


_PROIBIDOS_NA_ABA = re.compile(r"[\[\]:*?/\\]")


def nome_da_aba(titulo, usados):
    """Nome de aba válido no Excel (até 31 caracteres, sem []:*?/\\) e único na pasta de trabalho."""
    base = _PROIBIDOS_NA_ABA.sub(" ", titulo or "").strip().strip("'") or "Dados"
    base = base[:31].rstrip()
    nome, n = base, 2
    existentes = {u.lower() for u in usados}
    while nome.lower() in existentes:
        sufixo = f" ({n})"
        nome = base[:31 - len(sufixo)].rstrip() + sufixo
        n += 1
    return nome


def linha_de_total(linha, colunas):
    """True se a linha é a de totais (primeira coluna 'Total')."""
    return bool(colunas) and str(linha.get(colunas[0].chave, "")).strip().lower() == ROTULO_TOTAL.lower()
