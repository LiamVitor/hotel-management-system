import customtkinter as ctk

from ui.componentes.cartao import Cartao
from ui.estilos import AZUL, COR_BORDA, COR_TEXTO, COR_TEXTO_SUAVE, fonte

TAMANHO_VALOR = 28


class CartaoIndicador(Cartao):
    """Cartão de resumo com título, número grande e uma linha de detalhe.

    Se receber `comando`, vira um atalho: o cursor muda, a borda destaca ao passar o mouse
    e o clique chama o comando (usado para levar a pessoa à tela do assunto).
    """

    def __init__(self, master, titulo, comando=None, tamanho_valor=TAMANHO_VALOR):
        super().__init__(master)
        self._comando = comando
        ctk.CTkLabel(self, text=titulo, font=fonte(13), text_color=COR_TEXTO_SUAVE, anchor="w"
                     ).pack(anchor="w", padx=20, pady=(16, 0))
        self._valor = ctk.CTkLabel(self, text="—", font=fonte(tamanho_valor, True),
                                   text_color=COR_TEXTO, anchor="w")
        self._valor.pack(anchor="w", padx=20, pady=(2, 0))
        self._detalhe = ctk.CTkLabel(self, text=" ", font=fonte(12),
                                     text_color=COR_TEXTO_SUAVE, anchor="w")
        self._detalhe.pack(anchor="w", padx=20, pady=(0, 16))
        if comando:
            self._tornar_clicavel()

    def atualizar(self, valor, detalhe="", cor_valor=COR_TEXTO, cor_detalhe=COR_TEXTO_SUAVE):
        self._valor.configure(text=str(valor), text_color=cor_valor)
        self._detalhe.configure(text=detalhe or " ", text_color=cor_detalhe)

    def texto(self):
        """O número que está no cartão agora."""
        return self._valor.cget("text")

    def detalhe(self):
        """A linha de detalhe que está no cartão agora."""
        return self._detalhe.cget("text").strip()

    # ---------- atalho clicável ----------
    def _tornar_clicavel(self):
        for widget in (self, *self.winfo_children()):
            widget.configure(cursor="hand2")
            widget.bind("<Button-1>", lambda _e: self._comando(), add="+")
            widget.bind("<Enter>", lambda _e: self.configure(border_color=AZUL), add="+")
            widget.bind("<Leave>", self._ao_sair, add="+")

    def _ao_sair(self, evento):
        """Só tira o destaque quando o mouse saiu do cartão (e não só passou para um filho)."""
        sob_o_mouse = self.winfo_containing(evento.x_root, evento.y_root)
        if sob_o_mouse is None or not str(sob_o_mouse).startswith(str(self)):
            self.configure(border_color=COR_BORDA)
