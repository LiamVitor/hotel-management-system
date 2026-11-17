"""Janela que mostra o que vai mudar numa edição e pergunta se a pessoa confirma ou cancela."""
import customtkinter as ctk

from ui.componentes.botoes import botao_primario, botao_secundario
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, fonte

# vermelho claro = valor atual, verde claro = valor novo, azul claro = dado oculto
COR_ANTES = ("#FEF2F2", "#B91C1C")
COR_DEPOIS = ("#F0FDF4", "#15803D")
COR_OCULTO = ("#EFF6FF", "#1D4ED8")

LARGURA = 720
ALTURA_BASE = 230      # título, cabeçalho, pergunta e botões
ALTURA_POR_LINHA = 62


def confirmar_alteracoes(master, titulo, descricao, alteracoes):
    """Abre a janela e espera a resposta. Devolve True se a pessoa confirmou.

    alteracoes: lista de Alteracao (src.utils.alteracoes). Fechar a janela ou
    clicar em Cancelar devolve False.
    """
    janela = JanelaConfirmarAlteracoes(master, titulo, descricao, alteracoes)
    master.wait_window(janela)
    return janela.confirmado


class JanelaConfirmarAlteracoes(ctk.CTkToplevel):
    def __init__(self, master, titulo, descricao, alteracoes):
        super().__init__(master, fg_color=COR_FUNDO)
        self.confirmado = False
        self.title(titulo)
        self.resizable(False, False)
        altura = min(ALTURA_BASE + ALTURA_POR_LINHA * len(alteracoes), 720)
        self._centralizar(master, LARGURA, altura)
        self.transient(master.winfo_toplevel())

        ctk.CTkLabel(self, text=titulo, font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=28, pady=(22, 2))
        ctk.CTkLabel(self, text=descricao, font=fonte(13), text_color=COR_TEXTO_SUAVE,
                     wraplength=LARGURA - 56, justify="left"
                     ).pack(anchor="w", padx=28, pady=(0, 14))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=28, pady=(8, 22))
        ctk.CTkLabel(rodape, text="Deseja confirmar a alteração?", font=fonte(13, True),
                     text_color=COR_TEXTO).pack(side="left")
        botao_primario(rodape, "Confirmar alteração", self._confirmar, 190).pack(side="right")
        botao_secundario(rodape, "Cancelar", self.destroy, 120).pack(side="right", padx=(0, 10))

        self._montar_lista(alteracoes)

        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    def _montar_lista(self, alteracoes):
        grade = ctk.CTkFrame(self, fg_color="transparent")
        grade.pack(fill="both", expand=True, padx=28)
        grade.grid_columnconfigure(0, minsize=140)
        grade.grid_columnconfigure(1, weight=1, uniform="valor")
        grade.grid_columnconfigure(2, minsize=34)
        grade.grid_columnconfigure(3, weight=1, uniform="valor")

        for coluna, texto in ((0, "Campo"), (1, "Antes"), (3, "Depois")):
            ctk.CTkLabel(grade, text=texto, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                         ).grid(row=0, column=coluna, sticky="w", pady=(0, 6))

        for linha, alteracao in enumerate(alteracoes, start=1):
            ctk.CTkLabel(grade, text=alteracao.campo, font=fonte(13, True), text_color=COR_TEXTO
                         ).grid(row=linha, column=0, sticky="nw", pady=(8, 0))
            if alteracao.oculto:
                self._caixa(grade, f"{alteracao.campo} será alterada. Por segurança, "
                                   "o valor não é exibido.", COR_OCULTO
                            ).grid(row=linha, column=1, columnspan=3, sticky="ew", pady=4)
                continue
            self._caixa(grade, alteracao.antes, COR_ANTES
                        ).grid(row=linha, column=1, sticky="ew", pady=4)
            ctk.CTkLabel(grade, text="→", font=fonte(16, True), text_color=COR_TEXTO_SUAVE
                         ).grid(row=linha, column=2, pady=(8, 0), sticky="n")
            self._caixa(grade, alteracao.depois, COR_DEPOIS
                        ).grid(row=linha, column=3, sticky="ew", pady=4)

    @staticmethod
    def _caixa(pai, texto, cores):
        fundo, cor_texto = cores
        caixa = ctk.CTkFrame(pai, fg_color=fundo, corner_radius=6)
        ctk.CTkLabel(caixa, text=texto or "(vazio)", font=fonte(13), text_color=cor_texto,
                     wraplength=230, justify="left", anchor="w"
                     ).pack(fill="x", padx=10, pady=7)
        return caixa

    def _centralizar(self, master, largura, altura):
        topo = master.winfo_toplevel()
        x = topo.winfo_rootx() + max((topo.winfo_width() - largura) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{largura}x{altura}+{x}+{y}")

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()

    def _confirmar(self):
        self.confirmado = True
        self.destroy()
