"""Exportação de um `RelatorioPadrao` para planilha Excel (.xlsx). Sem dependência de tela.

Organização da pasta de trabalho:
- aba "Resumo": identidade da pousada, título, período, geração, responsável, filtros aplicados,
  indicadores e observações (nessa ordem, como na tela);
- uma aba por tabela do relatório, com a linha de títulos na primeira linha (congelada), filtro
  automático nos títulos (permite ordenar e filtrar) e valores como número/data de verdade, com
  formato de moeda, percentual e data. A linha "Total", quando existe, fica abaixo dos dados e
  fora do filtro, para não ser ordenada junto com eles.
"""
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.drawing.image import Image as ImagemPlanilha
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from src.models.relatorio_padrao import ALINHA_DIREITA
from src.services import exportacao_regras as regras
from src.services.relatorio_padrao import texto_emissor, texto_geracao

COR_PRINCIPAL = "1F2937"        # mesmo tom do menu lateral
COR_DESTAQUE = "2563EB"
COR_LINHA_ALT = "F3F4F6"
COR_BORDA = "D1D5DB"
COR_SUAVE = "6B7280"

LARGURA_MINIMA = 10
LARGURA_MAXIMA = 48
LADO_LOGO = 44                   # pixels

_BORDA = Side(style="thin", color=COR_BORDA)
_BORDA_CELULA = Border(left=_BORDA, right=_BORDA, top=_BORDA, bottom=_BORDA)
_ESTILO_TITULO = Font(name="Calibri", size=11, bold=True, color="FFFFFF")


def _escrever(celula, valor):
    """Grava na célula. Texto fica sempre como texto: um nome ou motivo que comece com '=' (ou
    '+', '-', '@') nunca é interpretado como fórmula."""
    celula.value = valor
    if isinstance(valor, str):
        celula.data_type = "s"


def _escrever_celula(celula, interpretado, alinhamento):
    if interpretado.tipo == regras.TEXTO:
        if interpretado.original != "":          # célula vazia continua vazia
            _escrever(celula, interpretado.original)
    else:
        celula.value = interpretado.valor
        celula.number_format = interpretado.formato
    celula.alignment = Alignment(
        horizontal="right" if (alinhamento == ALINHA_DIREITA or interpretado.tipo != regras.TEXTO)
        else "left", vertical="top", wrap_text=interpretado.tipo == regras.TEXTO)


def _largura(titulo, textos):
    maior = max([len(titulo) + 3] + [len(t) for t in textos]) if textos else len(titulo) + 3
    return max(LARGURA_MINIMA, min(LARGURA_MAXIMA, maior + 2))


def _montar_resumo(planilha, relatorio, usados):
    cab = relatorio.cabecalho
    planilha.title = regras.nome_da_aba("Resumo", usados)
    usados.append(planilha.title)
    planilha.sheet_view.showGridLines = False
    planilha.column_dimensions["A"].width = 38
    planilha.column_dimensions["B"].width = 34
    linha = 1

    coluna_nome = "A"
    if cab.arquivo_logo and Path(cab.arquivo_logo).is_file():
        try:
            logo = ImagemPlanilha(cab.arquivo_logo)
            logo.width = logo.height = LADO_LOGO
            planilha.add_image(logo, "A1")
            planilha.column_dimensions["A"].width = 38
            planilha.row_dimensions[1].height = 24
            planilha.row_dimensions[2].height = 24
            coluna_nome = "B"
        except (OSError, ValueError):
            coluna_nome = "A"
    nome = planilha[f"{coluna_nome}1"]
    _escrever(nome, cab.nome_pousada)
    nome.font = Font(name="Calibri", size=16, bold=True, color=COR_PRINCIPAL)
    nome.alignment = Alignment(vertical="bottom")
    sub = planilha[f"{coluna_nome}2"]
    _escrever(sub, "Relatório gerencial")
    sub.font = Font(name="Calibri", size=10, color=COR_SUAVE)
    sub.alignment = Alignment(vertical="top")
    linha = 4

    titulo = planilha.cell(row=linha, column=1)
    _escrever(titulo, cab.titulo)
    titulo.font = Font(name="Calibri", size=14, bold=True, color=COR_DESTAQUE)
    linha += 1
    for texto in (cab.periodo, texto_geracao(cab), texto_emissor(cab)):
        celula = planilha.cell(row=linha, column=1)
        _escrever(celula, texto)
        celula.font = Font(name="Calibri", size=10, color=COR_SUAVE)
        linha += 1

    def secao(nome_secao, linha):
        linha += 1
        celula = planilha.cell(row=linha, column=1)
        _escrever(celula, nome_secao)
        celula.font = _ESTILO_TITULO
        celula.fill = PatternFill("solid", fgColor=COR_PRINCIPAL)
        planilha.cell(row=linha, column=2).fill = PatternFill("solid", fgColor=COR_PRINCIPAL)
        return linha + 1

    if relatorio.filtros:
        linha = secao("Filtros aplicados", linha)
        for filtro in relatorio.filtros:
            a, b = planilha.cell(row=linha, column=1), planilha.cell(row=linha, column=2)
            _escrever(a, filtro.rotulo)
            _escrever(b, filtro.valor)
            a.font = Font(name="Calibri", size=10, bold=True)
            a.border = b.border = _BORDA_CELULA
            b.alignment = Alignment(horizontal="left", wrap_text=True, vertical="top")
            linha += 1

    if relatorio.indicadores:
        linha = secao("Indicadores", linha)
        for indicador in relatorio.indicadores:
            a, b = planilha.cell(row=linha, column=1), planilha.cell(row=linha, column=2)
            _escrever(a, indicador.rotulo)
            a.font = Font(name="Calibri", size=10)
            interpretado = regras.interpretar_valor(indicador.valor)
            if interpretado.tipo == regras.TEXTO:
                _escrever(b, interpretado.original)
            else:
                b.value, b.number_format = interpretado.valor, interpretado.formato
            b.font = Font(name="Calibri", size=11, bold=True)
            b.alignment = Alignment(horizontal="right")
            a.border = b.border = _BORDA_CELULA
            linha += 1

    if relatorio.observacoes:
        linha = secao("Observações", linha)
        for obs in relatorio.observacoes:
            planilha.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=2)
            celula = planilha.cell(row=linha, column=1)
            _escrever(celula, obs)
            celula.font = Font(name="Calibri", size=10, color=COR_SUAVE)
            celula.alignment = Alignment(wrap_text=True, vertical="top")
            planilha.row_dimensions[linha].height = max(15, 15 * (len(obs) // 70 + 1))
            linha += 1

    planilha.page_setup.orientation = "portrait"
    planilha.page_setup.fitToWidth = 1
    planilha.page_setup.fitToHeight = 0
    planilha.sheet_properties.pageSetUpPr.fitToPage = True


def _montar_tabela(planilha, tabela, relatorio, usados):
    planilha.title = regras.nome_da_aba(tabela.titulo, usados)
    usados.append(planilha.title)
    colunas = tabela.colunas
    linhas, total = regras.separar_total(tabela)

    # títulos das colunas (linha 1: o que o filtro automático e a ordenação usam)
    for numero, coluna in enumerate(colunas, start=1):
        celula = planilha.cell(row=1, column=numero)
        _escrever(celula, coluna.titulo)
        celula.font = _ESTILO_TITULO
        celula.fill = PatternFill("solid", fgColor=COR_PRINCIPAL)
        celula.border = _BORDA_CELULA
        celula.alignment = Alignment(
            horizontal="right" if coluna.alinhamento == ALINHA_DIREITA else "left",
            vertical="center", wrap_text=True)
    planilha.row_dimensions[1].height = 30

    # dados, coluna a coluna (a tipagem de uma coluna olha a coluna inteira)
    interpretadas = []
    for coluna in colunas:
        valores = [l.get(coluna.chave, "") for l in linhas]
        if total is not None:
            valores.append(total.get(coluna.chave, ""))
        interpretadas.append(regras.interpretar_coluna(valores))

    for i, _ in enumerate(linhas):
        for numero, coluna in enumerate(colunas, start=1):
            celula = planilha.cell(row=2 + i, column=numero)
            _escrever_celula(celula, interpretadas[numero - 1][i], coluna.alinhamento)
            celula.border = _BORDA_CELULA
            if i % 2 == 1:
                celula.fill = PatternFill("solid", fgColor=COR_LINHA_ALT)

    ultima = 1 + len(linhas)
    if not linhas:
        vazio = planilha.cell(row=2, column=1)
        _escrever(vazio, "Nenhum registro para os filtros aplicados.")
        vazio.font = Font(name="Calibri", italic=True, color=COR_SUAVE)
        ultima = 1
    else:
        # filtro automático só sobre os dados (a linha de total fica de fora)
        planilha.auto_filter.ref = f"A1:{get_column_letter(len(colunas))}{ultima}"

    if total is not None:
        linha_total = ultima + 2          # uma linha em branco separa os dados do total
        for numero, coluna in enumerate(colunas, start=1):
            celula = planilha.cell(row=linha_total, column=numero)
            _escrever_celula(celula, interpretadas[numero - 1][len(linhas)], coluna.alinhamento)
            celula.font = Font(name="Calibri", bold=True)
            celula.fill = PatternFill("solid", fgColor="E5E7EB")
            celula.border = Border(top=Side(style="medium", color=COR_PRINCIPAL),
                                   bottom=_BORDA)

    for numero, coluna in enumerate(colunas, start=1):
        textos = [str(l.get(coluna.chave, "")) for l in linhas]
        if total is not None:
            textos.append(str(total.get(coluna.chave, "")))
        planilha.column_dimensions[get_column_letter(numero)].width = _largura(coluna.titulo, textos)

    planilha.freeze_panes = "A2"
    # impressão: paisagem, uma página de largura, títulos repetidos e rodapé numerado
    planilha.page_setup.orientation = "landscape" if len(colunas) > 5 else "portrait"
    planilha.page_setup.paperSize = planilha.PAPERSIZE_A4
    planilha.page_setup.fitToWidth = 1
    planilha.page_setup.fitToHeight = 0
    planilha.sheet_properties.pageSetUpPr.fitToPage = True
    planilha.print_title_rows = "1:1"
    cab = relatorio.cabecalho
    planilha.oddHeader.left.text = cab.nome_pousada
    planilha.oddHeader.center.text = f"{cab.titulo} — {tabela.titulo}"
    planilha.oddHeader.right.text = cab.periodo
    planilha.oddFooter.left.text = texto_emissor(cab)
    planilha.oddFooter.right.text = "Página &P de &N"


def gerar_excel(relatorio, destino):
    """Grava o relatório em `destino` (.xlsx). Devolve o caminho (Path)."""
    destino = Path(destino)
    cab = relatorio.cabecalho
    pasta = Workbook()
    usados = []
    _montar_resumo(pasta.active, relatorio, usados)
    for tabela in relatorio.tabelas:
        _montar_tabela(pasta.create_sheet(), tabela, relatorio, usados)

    pasta.properties.title = f"{cab.nome_pousada} — {cab.titulo}"
    pasta.properties.creator = cab.emitido_por
    pasta.properties.created = cab.gerado_em if isinstance(cab.gerado_em, datetime) else datetime.now()
    pasta.save(destino)
    return destino
