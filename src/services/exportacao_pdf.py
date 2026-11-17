"""Exportação de um `RelatorioPadrao` para PDF. Sem dependência de tela.

Todo PDF tem a mesma identidade: cabeçalho com logotipo e nome da pousada, título, período,
data/hora de geração e responsável; depois filtros, indicadores, tabelas e observações (a ordem
padrão de `relatorio_padrao`). Cada página leva o rodapé padrão (`relatorio_padrao.rodape`):
"Pousada — Título", "Emitido por ... em ..." e "Página N de M". Tabelas longas continuam nas
páginas seguintes repetindo a linha de títulos.
"""
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas
from reportlab.platypus import (CondPageBreak, HRFlowable, Image, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from src.models.relatorio_padrao import ALINHA_DIREITA
from src.services import exportacao_regras as regras
from src.services.relatorio_padrao import (INDICADORES_POR_FILEIRA, rodape, texto_emissor,
                                           texto_geracao)

COR_PRINCIPAL = colors.HexColor("#1F2937")
COR_DESTAQUE = colors.HexColor("#2563EB")
COR_SUAVE = colors.HexColor("#6B7280")
COR_BORDA = colors.HexColor("#D1D5DB")
COR_LINHA_ALT = colors.HexColor("#F3F4F6")
COR_CARTAO = colors.HexColor("#F9FAFB")
COR_TOTAL = colors.HexColor("#E5E7EB")

MARGEM = 12 * mm
MARGEM_SUPERIOR = 12 * mm
MARGEM_INFERIOR = 16 * mm
LADO_LOGO = 12 * mm
LARGURA_MINIMA_COLUNA = 14 * mm
COLUNAS_PARA_PAISAGEM = 8        # tabela com 8 colunas ou mais pede página deitada
ESPACO_MINIMO_TABELA = 45 * mm     # abaixo disso, a tabela começa na próxima página
LARGURA_PARA_PAISAGEM = 900      # ou larga demais (soma das larguras relativas das colunas)

FONTE = "Helvetica"
FONTE_NEGRITO = "Helvetica-Bold"
FONTE_ITALICO = "Helvetica-Oblique"

# As fontes padrão do PDF cobrem o alfabeto latino (cp1252). O que ficar fora vira equivalente.
_SUBSTITUICOES = str.maketrans({"−": "-", "→": "->", "≥": ">=", "≤": "<=", "\u00a0": " ",
                                "\u200b": ""})


def seguro(texto):
    """Texto que as fontes padrão do PDF conseguem desenhar (o que não couber vira '?')."""
    texto = "" if texto is None else str(texto).translate(_SUBSTITUICOES)
    return texto.encode("cp1252", errors="replace").decode("cp1252")


def _p(texto):
    """Texto seguro para dentro de um Paragraph (escapa & < >)."""
    return escape(seguro(texto))


def _estilo(nome, **extra):
    base = dict(fontName=FONTE, fontSize=8, leading=10, textColor=COR_PRINCIPAL)
    base.update(extra)
    return ParagraphStyle(nome, **base)


ESTILOS = {
    "pousada": _estilo("pousada", fontName=FONTE_NEGRITO, fontSize=14, leading=17),
    "subtitulo": _estilo("subtitulo", fontSize=8, textColor=COR_SUAVE),
    "meta": _estilo("meta", fontSize=8, textColor=COR_SUAVE, alignment=TA_RIGHT),
    "titulo": _estilo("titulo", fontName=FONTE_NEGRITO, fontSize=17, leading=21,
                      textColor=COR_DESTAQUE, spaceBefore=6),
    "periodo": _estilo("periodo", fontSize=10, leading=13, textColor=COR_SUAVE),
    "filtros": _estilo("filtros", fontSize=8.5, leading=11, spaceBefore=3),
    "rotulo_indicador": _estilo("rotulo_indicador", fontSize=7.5, leading=9, textColor=COR_SUAVE),
    "valor_indicador": _estilo("valor_indicador", fontName=FONTE_NEGRITO, fontSize=13, leading=16),
    "titulo_tabela": _estilo("titulo_tabela", fontName=FONTE_NEGRITO, fontSize=11, leading=14,
                             spaceBefore=12, spaceAfter=5),
    "cabecalho_coluna": _estilo("cabecalho_coluna", fontName=FONTE_NEGRITO, fontSize=7.5,
                                leading=9, textColor=colors.white),
    "vazio": _estilo("vazio", fontName=FONTE_ITALICO, textColor=COR_SUAVE, spaceBefore=2),
    "obs_titulo": _estilo("obs_titulo", fontName=FONTE_NEGRITO, fontSize=9, leading=12,
                          spaceBefore=12, spaceAfter=3, keepWithNext=1),
    "obs": _estilo("obs", fontSize=7.5, leading=10, textColor=COR_SUAVE, spaceAfter=2),
}


def _estilo_celula(alinhamento, negrito=False):
    return _estilo(f"celula_{alinhamento}_{int(negrito)}", fontSize=7.5, leading=9,
                   fontName=FONTE_NEGRITO if negrito else FONTE,
                   alignment=TA_RIGHT if alinhamento == ALINHA_DIREITA else TA_LEFT)


# ---------- página ----------
def _usa_paisagem(relatorio):
    return any(len(t.colunas) >= COLUNAS_PARA_PAISAGEM
               or sum(c.largura for c in t.colunas) > LARGURA_PARA_PAISAGEM
               for t in relatorio.tabelas)


def _cortar(texto, fonte, tamanho, largura):
    """Encurta com reticências para caber na largura."""
    if stringWidth(texto, fonte, tamanho) <= largura:
        return texto
    while texto and stringWidth(texto + "...", fonte, tamanho) > largura:
        texto = texto[:-1]
    return texto.rstrip() + "..."


def _canvas_com_rodape(relatorio):
    """Canvas que desenha o rodapé padrão em toda página, sabendo o total de páginas."""
    cab = relatorio.cabecalho

    class CanvasComRodape(canvas.Canvas):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._paginas_guardadas = []

        def showPage(self):
            self._paginas_guardadas.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._paginas_guardadas)
            for numero, estado in enumerate(self._paginas_guardadas, start=1):
                self.__dict__.update(estado)
                self._desenhar_rodape(numero, total)
                super().showPage()
            super().save()

        def _desenhar_rodape(self, numero, total):
            largura_pagina = self._pagesize[0]
            util = largura_pagina - 2 * MARGEM
            r = rodape(cab, numero, total)
            tamanho, y = 6.8, MARGEM_INFERIOR - 8 * mm
            self.setStrokeColor(COR_BORDA)
            self.setLineWidth(0.5)
            self.line(MARGEM, y + 11, largura_pagina - MARGEM, y + 11)
            self.setFillColor(COR_SUAVE)
            zona_esq, zona_centro = util * 0.34, util * 0.42
            self.setFont(FONTE, tamanho)
            self.drawString(MARGEM, y, _cortar(seguro(r.esquerda), FONTE, tamanho, zona_esq - 6))
            self.drawCentredString(MARGEM + zona_esq + zona_centro / 2, y,
                                   _cortar(seguro(r.centro), FONTE, tamanho, zona_centro - 6))
            self.setFont(FONTE_NEGRITO, tamanho)
            self.drawRightString(largura_pagina - MARGEM, y, seguro(r.direita))

    return CanvasComRodape


# ---------- blocos ----------
def _bloco_cabecalho(relatorio, largura):
    cab = relatorio.cabecalho
    nome = [Paragraph(_p(cab.nome_pousada), ESTILOS["pousada"]),
            Paragraph("Relatório gerencial", ESTILOS["subtitulo"])]
    meta = [Paragraph(_p(texto_geracao(cab)), ESTILOS["meta"]),
            Paragraph(_p(texto_emissor(cab)), ESTILOS["meta"])]
    logo = ""
    if cab.arquivo_logo and Path(cab.arquivo_logo).is_file():
        try:
            logo = Image(cab.arquivo_logo, width=LADO_LOGO, height=LADO_LOGO, mask="auto")
        except (OSError, ValueError):
            logo = ""
    if logo != "":
        colunas, dados = [LADO_LOGO + 3 * mm, largura * 0.5, largura - LADO_LOGO - 3 * mm
                          - largura * 0.5], [[logo, nome, meta]]
    else:
        colunas, dados = [largura * 0.55, largura * 0.45], [[nome, meta]]
    topo = Table(dados, colWidths=colunas)
    topo.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0),
                              ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                              ("TOPPADDING", (0, 0), (-1, -1), 0),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    partes = [topo, Spacer(1, 3 * mm),
              HRFlowable(width="100%", thickness=1.2, color=COR_DESTAQUE, spaceAfter=2),
              Paragraph(_p(cab.titulo), ESTILOS["titulo"]),
              Paragraph(_p(cab.periodo), ESTILOS["periodo"])]
    if relatorio.filtros:
        texto = "  ·  ".join(f"<b>{_p(f.rotulo)}:</b> {_p(f.valor)}" for f in relatorio.filtros)
        partes.append(Paragraph(texto, ESTILOS["filtros"]))
    return partes


def _bloco_indicadores(relatorio, largura):
    """Cartões de indicadores, INDICADORES_POR_FILEIRA por fileira (como na tela)."""
    if not relatorio.indicadores:
        return []
    por_fileira = INDICADORES_POR_FILEIRA
    espaco = 3 * mm
    largura_cartao = (largura - espaco * (por_fileira - 1)) / por_fileira
    larguras = []
    for coluna in range(por_fileira):
        larguras.append(largura_cartao)
        if coluna < por_fileira - 1:
            larguras.append(espaco)                 # coluna estreita entre dois cartões

    cartoes = [[Paragraph(_p(i.rotulo), ESTILOS["rotulo_indicador"]),
                Paragraph(_p(i.valor), ESTILOS["valor_indicador"])] for i in relatorio.indicadores]
    estilo = [("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
              ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    linhas, alturas = [], []
    for inicio in range(0, len(cartoes), por_fileira):
        fileira = cartoes[inicio:inicio + por_fileira]
        if linhas:                                   # linha estreita entre duas fileiras
            linhas.append([""] * len(larguras))
            alturas.append(espaco)
        celulas = []
        for coluna in range(por_fileira):
            celulas.append(fileira[coluna] if coluna < len(fileira) else "")
            if coluna < por_fileira - 1:
                celulas.append("")
        for coluna in range(len(fileira)):           # só os cartões que existem levam borda
            c, l = 2 * coluna, len(linhas)
            estilo += [("BOX", (c, l), (c, l), 0.6, COR_BORDA),
                       ("BACKGROUND", (c, l), (c, l), COR_CARTAO)]
        linhas.append(celulas)
        alturas.append(None)
    for coluna in range(1, len(larguras), 2):        # as colunas de espaço não têm margem
        estilo += [("LEFTPADDING", (coluna, 0), (coluna, -1), 0),
                   ("RIGHTPADDING", (coluna, 0), (coluna, -1), 0)]
    for linha, altura in enumerate(alturas):         # nem as linhas de espaço
        if altura is not None:
            estilo += [("TOPPADDING", (0, linha), (-1, linha), 0),
                       ("BOTTOMPADDING", (0, linha), (-1, linha), 0)]
    grade = Table(linhas, colWidths=larguras, rowHeights=alturas)
    grade.setStyle(TableStyle(estilo))
    return [Spacer(1, 4 * mm), grade]


def _larguras(tabela, largura):
    pesos = [max(c.largura, 1) for c in tabela.colunas]
    total = sum(pesos)
    larguras = [largura * p / total for p in pesos]
    # coluna estreita demais ganha o mínimo, e as outras cedem o que for preciso
    for _ in range(3):
        curtas = [i for i, w in enumerate(larguras) if w < LARGURA_MINIMA_COLUNA]
        if not curtas:
            break
        falta = sum(LARGURA_MINIMA_COLUNA - larguras[i] for i in curtas)
        longas = [i for i, w in enumerate(larguras) if w >= LARGURA_MINIMA_COLUNA]
        sobra = sum(larguras[i] - LARGURA_MINIMA_COLUNA for i in longas)
        if sobra <= 0:
            break
        fator = min(1.0, falta / sobra)
        for i in curtas:
            larguras[i] = LARGURA_MINIMA_COLUNA
        for i in longas:
            larguras[i] -= (larguras[i] - LARGURA_MINIMA_COLUNA) * fator
    return larguras


def _bloco_tabela(tabela, largura):
    # título e primeiras linhas ficam juntos: sem espaço para isso, começa na página seguinte
    partes = [CondPageBreak(ESPACO_MINIMO_TABELA), Paragraph(_p(tabela.titulo), ESTILOS["titulo_tabela"])]
    if not tabela.linhas:
        partes.append(Paragraph("Nenhum registro para os filtros aplicados.", ESTILOS["vazio"]))
        return partes

    titulos = [Paragraph(_p(c.titulo), _estilo(f"th_{c.alinhamento}", fontName=FONTE_NEGRITO,
                                                fontSize=7.5, leading=9, textColor=colors.white,
                                                alignment=TA_RIGHT if c.alinhamento == ALINHA_DIREITA
                                                else TA_LEFT))
               for c in tabela.colunas]
    dados = [titulos]
    for linha in tabela.linhas:
        negrito = regras.linha_de_total(linha, tabela.colunas)
        dados.append([Paragraph(_p(linha.get(c.chave, "")), _estilo_celula(c.alinhamento, negrito))
                      for c in tabela.colunas])

    estilo = [("BACKGROUND", (0, 0), (-1, 0), COR_PRINCIPAL),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("GRID", (0, 0), (-1, -1), 0.25, COR_BORDA),
              ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
              ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
              ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COR_LINHA_ALT])]
    if regras.linha_de_total(tabela.linhas[-1], tabela.colunas) and len(tabela.linhas) > 1:
        estilo += [("BACKGROUND", (0, -1), (-1, -1), COR_TOTAL),
                   ("LINEABOVE", (0, -1), (-1, -1), 1, COR_PRINCIPAL)]
    grade = Table(dados, colWidths=_larguras(tabela, largura), repeatRows=1)
    grade.setStyle(TableStyle(estilo))
    partes.append(grade)
    return partes


def _bloco_observacoes(relatorio):
    if not relatorio.observacoes:
        return []
    partes = [Paragraph("Observações", ESTILOS["obs_titulo"])]
    partes += [Paragraph(_p(o), ESTILOS["obs"]) for o in relatorio.observacoes]
    return partes


def gerar_pdf(relatorio, destino):
    """Grava o relatório em `destino` (.pdf). Devolve o caminho (Path)."""
    destino = Path(destino)
    cab = relatorio.cabecalho
    pagina = landscape(A4) if _usa_paisagem(relatorio) else portrait(A4)
    largura = pagina[0] - 2 * MARGEM
    doc = SimpleDocTemplate(
        str(destino), pagesize=pagina, leftMargin=MARGEM, rightMargin=MARGEM,
        topMargin=MARGEM_SUPERIOR, bottomMargin=MARGEM_INFERIOR,
        title=seguro(f"{cab.nome_pousada} — {cab.titulo}"), author=seguro(cab.emitido_por),
        subject=seguro(cab.periodo), creator="Sistema de gestão da pousada")

    historia = _bloco_cabecalho(relatorio, largura) + _bloco_indicadores(relatorio, largura)
    for tabela in relatorio.tabelas:
        historia += _bloco_tabela(tabela, largura)
    historia += _bloco_observacoes(relatorio)
    doc.build(historia, canvasmaker=_canvas_com_rodape(relatorio))
    return destino
