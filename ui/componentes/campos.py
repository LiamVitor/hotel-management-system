import customtkinter as ctk

from ui.estilos import (COR_BORDA_CAMPO, COR_SELECAO, COR_TEXTO, COR_TEXTO_SUAVE, fonte)


class CampoTexto(ctk.CTkFrame):
    """Rótulo + campo de texto."""

    def __init__(self, master, rotulo, placeholder="", ao_mudar=None):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=rotulo, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w")
        self.entrada = ctk.CTkEntry(self, placeholder_text=placeholder, height=36,
                                    fg_color="white", border_color=COR_BORDA_CAMPO,
                                    text_color=COR_TEXTO, placeholder_text_color="#9CA3AF",
                                    font=fonte(13))
        self.entrada.pack(fill="x", pady=(4, 0))
        if ao_mudar:
            self.entrada.bind("<KeyRelease>", lambda _e: ao_mudar())

    def valor(self):
        return self.entrada.get().strip()

    def definir(self, texto):
        self.entrada.delete(0, "end")
        self.entrada.insert(0, str(texto))

    def limpar(self):
        self.entrada.delete(0, "end")
        # tira o foco do campo para o texto de exemplo (placeholder) voltar a aparecer
        self.winfo_toplevel().focus_set()


class CampoSelecao(ctk.CTkFrame):
    """Rótulo + lista de seleção (só permite escolher, não digitar)."""

    def __init__(self, master, rotulo, opcoes, ao_mudar=None):
        super().__init__(master, fg_color="transparent")
        ctk.CTkLabel(self, text=rotulo, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w")
        comando = (lambda _valor: ao_mudar()) if ao_mudar else None
        self.caixa = ctk.CTkComboBox(self, values=list(opcoes), state="readonly", height=36,
                                     command=comando, fg_color="white",
                                     border_color=COR_BORDA_CAMPO, button_color=COR_BORDA_CAMPO,
                                     button_hover_color="#9CA3AF", text_color=COR_TEXTO,
                                     dropdown_fg_color="white", dropdown_text_color=COR_TEXTO,
                                     dropdown_hover_color=COR_SELECAO, font=fonte(13))
        self.caixa.pack(fill="x", pady=(4, 0))
        self.caixa.set("")

    def valor(self):
        return self.caixa.get()

    def definir(self, texto):
        self.caixa.set(texto)

    def definir_opcoes(self, opcoes):
        self.caixa.configure(values=list(opcoes))

    def limpar(self):
        self.caixa.set("")
