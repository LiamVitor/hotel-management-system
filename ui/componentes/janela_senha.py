from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoTexto
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, fonte


class JanelaAlterarSenha(ctk.CTkToplevel):
    """Janela para o usuário logado trocar a própria senha."""

    def __init__(self, master, servico_usuarios):
        super().__init__(master, fg_color=COR_FUNDO)
        self._servico = servico_usuarios
        self.title("Alterar senha")
        self.resizable(False, False)
        self._centralizar(master, 400, 470)
        self.transient(master.winfo_toplevel())

        ctk.CTkLabel(self, text="Alterar senha", font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(self, text="Use pelo menos 6 caracteres.", font=fonte(12),
                     text_color=COR_TEXTO_SUAVE).pack(anchor="w", padx=28, pady=(0, 14))

        self.atual = CampoTexto(self, "Senha atual", ocultar=True)
        self.nova = CampoTexto(self, "Nova senha", ocultar=True)
        self.confirmar = CampoTexto(self, "Confirmar nova senha", ocultar=True)
        for campo in (self.atual, self.nova, self.confirmar):
            campo.pack(fill="x", padx=28, pady=(0, 10))

        self.lbl_erro = ctk.CTkLabel(self, text="", font=fonte(12, True), text_color=VERMELHO,
                                     wraplength=340, justify="left")
        self.lbl_erro.pack(anchor="w", padx=28)

        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(side="bottom", fill="x", padx=28, pady=(8, 24))
        botao_primario(botoes, "Salvar", self.salvar, 130).pack(side="right")
        botao_secundario(botoes, "Cancelar", self.destroy, 110).pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda _e: self.salvar())
        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

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
        self.atual.entrada.focus()

    def salvar(self):
        try:
            self._servico.alterar_propria_senha(self.atual.valor_sem_cortar(),
                                                self.nova.valor_sem_cortar(),
                                                self.confirmar.valor_sem_cortar())
        except ErroNegocio as erro:
            self.lbl_erro.configure(text=str(erro))
            return
        messagebox.showinfo("Senha alterada", "Sua senha foi alterada com sucesso.", parent=self)
        self.destroy()
