"""Cabeçalho padrão dos relatórios: pousada (nome e logotipo), título, período, geração e emissor."""
import customtkinter as ctk
from PIL import Image

from src.services.relatorio_padrao import texto_emissor, texto_geracao
from ui.componentes.cartao import Cartao
from ui.estilos import AZUL, COR_BORDA, COR_TEXTO, COR_TEXTO_SUAVE, fonte

LADO_LOGO = 44
_logos = {}      # caminho -> CTkImage (ou None se o arquivo não abriu)


def carregar_logo(caminho, lado=LADO_LOGO):
    """Imagem do logotipo, ou None se não há arquivo ou ele não abre (aí vale o monograma)."""
    if not caminho:
        return None
    if caminho not in _logos:
        try:
            imagem = Image.open(caminho).convert("RGBA")
            _logos[caminho] = ctk.CTkImage(light_image=imagem, size=(lado, lado))
        except (OSError, ValueError):
            _logos[caminho] = None
    return _logos[caminho]


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
        logo = carregar_logo(cabecalho.arquivo_logo)
        if logo is not None:
            self._logo.configure(image=logo, text="", fg_color="transparent")
        else:      # sem arquivo de logotipo: monograma com a inicial da pousada
            self._logo.configure(image=None, text=cabecalho.nome_pousada[:1].upper(), fg_color=AZUL,
                                 text_color="white", corner_radius=10, font=fonte(22, True))
        self.lbl_pousada.configure(text=cabecalho.nome_pousada)
        self.lbl_titulo.configure(text=cabecalho.titulo)
        self.lbl_periodo.configure(text=cabecalho.periodo)
        self.lbl_geracao.configure(text=texto_geracao(cabecalho))
        self.lbl_emissor.configure(text=texto_emissor(cabecalho))
