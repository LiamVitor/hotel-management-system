"""Cabeçalho padrão dos relatórios: pousada (nome e logotipo), título, período, geração e emissor."""
import io
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from src.services.relatorio_padrao import texto_emissor, texto_geracao
from ui.componentes import icones_menu
from ui.componentes.cartao import Cartao
from ui.estilos import AZUL, COR_BORDA, COR_TEXTO, COR_TEXTO_SUAVE, fonte

LADO_LOGO = 44
# O cabeçalho mostra um ícone desenhado no mesmo estilo dos do menu lateral, em vez do arquivo de
# logotipo. Para trocar, use o nome de qualquer item do menu: "Quartos", "Reservas", "Início"...
ICONE_CABECALHO = "Quartos"
LADO_ICONE = 26
_logos = {}      # caminho -> CTkImage (ou None se o arquivo não abriu)


ESCALA_SVG = 4       # o SVG é desenhado 4x maior que o espaço do logotipo, para ficar nítido


def abrir_imagem_logo(caminho, lado=LADO_LOGO):
    """Abre o logotipo (PNG, JPG ou SVG) como imagem PIL, ou levanta OSError/ValueError/ImportError.

    SVG é desenhado pelo pacote `resvg-py` (pip install resvg-py): o Tk não lê SVG sozinho.
    """
    caminho = Path(caminho)
    if caminho.suffix.lower() in (".svg", ".svgz"):
        import resvg_py
        # o SVG pode não ser quadrado: a maior dimensão vai a `lado`, a outra segue a proporção
        png = resvg_py.svg_to_bytes(svg_path=str(caminho), width=lado * ESCALA_SVG)
        imagem = Image.open(io.BytesIO(bytes(png)))
        if imagem.height > imagem.width:
            png = resvg_py.svg_to_bytes(svg_path=str(caminho), height=lado * ESCALA_SVG)
            imagem = Image.open(io.BytesIO(bytes(png)))
        return imagem.convert("RGBA")
    return Image.open(caminho).convert("RGBA")


def carregar_logo(caminho, lado=LADO_LOGO):
    """Imagem do logotipo, ou None se não há arquivo ou ele não abre (aí vale o monograma).

    Se o SVG não puder ser desenhado (arquivo inválido ou `resvg-py` não instalado), tenta o
    `logo.png` da mesma pasta antes de desistir.
    """
    if not caminho:
        return None
    if caminho not in _logos:
        _logos[caminho] = None
        candidatos = [Path(caminho)]
        if candidatos[0].suffix.lower() in (".svg", ".svgz"):
            candidatos.append(candidatos[0].with_suffix(".png"))
        for candidato in candidatos:
            try:
                imagem = abrir_imagem_logo(candidato, lado)
            except (OSError, ValueError, ImportError):
                continue
            proporcao = imagem.width / imagem.height
            tamanho = (lado, round(lado / proporcao)) if proporcao >= 1 else (round(lado * proporcao), lado)
            _logos[caminho] = ctk.CTkImage(light_image=imagem, size=tamanho)
            break
    return _logos[caminho]


def limpar_cache():
    """Esquece os logotipos guardados (mesmo motivo de `icones_menu.limpar_cache`)."""
    _logos.clear()


class CabecalhoPadrao(Cartao):
    """Mostra um `CabecalhoRelatorio`: logotipo e nome da pousada, título, período, quando foi
    gerado e por quem. É o mesmo bloco no topo de todos os relatórios."""

    def __init__(self, master):
        super().__init__(master)
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(14, 0))
        topo.grid_columnconfigure(1, weight=1)
        self._logo = ctk.CTkLabel(topo, text="", width=LADO_LOGO, height=LADO_LOGO)
        self._logo.grid(row=0, column=0, rowspan=2, sticky="w")
        self.lbl_pousada = ctk.CTkLabel(topo, text="", font=fonte(16, True), text_color=COR_TEXTO,
                                        anchor="w")
        self.lbl_pousada.grid(row=0, column=1, sticky="sw", padx=(12, 0))
        ctk.CTkLabel(topo, text="Relatório gerencial", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                     anchor="w").grid(row=1, column=1, sticky="nw", padx=(12, 0))
        self.lbl_geracao = ctk.CTkLabel(topo, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                                        anchor="e")
        self.lbl_geracao.grid(row=0, column=2, sticky="se")
        self.lbl_emissor = ctk.CTkLabel(topo, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                                        anchor="e")
        self.lbl_emissor.grid(row=1, column=2, sticky="ne")

        ctk.CTkFrame(self, height=1, fg_color=COR_BORDA).pack(fill="x", padx=20, pady=(12, 10))
        self.lbl_titulo = ctk.CTkLabel(self, text="", font=fonte(20, True), text_color=COR_TEXTO,
                                       anchor="w")
        self.lbl_titulo.pack(anchor="w", padx=20)
        self.lbl_periodo = ctk.CTkLabel(self, text="", font=fonte(13), text_color=COR_TEXTO_SUAVE,
                                        anchor="w")
        self.lbl_periodo.pack(anchor="w", padx=20, pady=(0, 14))

    def atualizar(self, cabecalho): 
        icone = icones_menu.icone(ICONE_CABECALHO, "#FFFFFF", LADO_ICONE)
        self._logo.configure(image=icone, text="", fg_color=AZUL, corner_radius=10)
        self.lbl_pousada.configure(text=cabecalho.nome_pousada)
        self.lbl_titulo.configure(text=cabecalho.titulo)
        self.lbl_periodo.configure(text=cabecalho.periodo)
        self.lbl_geracao.configure(text=texto_geracao(cabecalho))
        self.lbl_emissor.configure(text=texto_emissor(cabecalho))
