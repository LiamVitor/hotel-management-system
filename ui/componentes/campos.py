import customtkinter as ctk

from ui.estilos import (COR_BORDA_CAMPO, COR_SELECAO, COR_TEXTO, COR_TEXTO_SUAVE, fonte)


def reformatar_entrada(entrada, mascara):
    """Aplica a máscara ao texto do campo mantendo o cursor ao lado do mesmo dígito."""
    atual = entrada.get()
    novo = mascara(atual)
    if novo == atual:
        return
    posicao = entrada.index("insert")
    digitos_antes = sum(c.isdigit() for c in atual[:posicao])

    entrada.delete(0, "end")
    entrada.insert(0, novo)

    nova_posicao = 0 if digitos_antes == 0 else len(novo)
    contados = 0
    for i, caractere in enumerate(novo):
        if caractere.isdigit():
            contados += 1
            if contados == digitos_antes:
                nova_posicao = i + 1
                break
    entrada.icursor(nova_posicao)


class CampoTexto(ctk.CTkFrame):
    """Rótulo + campo de texto.

    mascara: função texto -> texto formatado, aplicada enquanto a pessoa digita
             (ex.: formatar_cpf, formatar_telefone, mascara_data).
    ocultar: mostra bolinhas no lugar do texto (campos de senha).
    """

    def __init__(self, master, rotulo, placeholder="", ao_mudar=None, mascara=None,
                 ocultar=False):
        super().__init__(master, fg_color="transparent")
        self._mascara = mascara
        self._ao_mudar = ao_mudar
        ctk.CTkLabel(self, text=rotulo, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w")
        self.entrada = ctk.CTkEntry(self, placeholder_text=placeholder, height=36,
                                    fg_color="white", border_color=COR_BORDA_CAMPO,
                                    text_color=COR_TEXTO, placeholder_text_color="#9CA3AF",
                                    font=fonte(13), show="•" if ocultar else "")
        self.entrada.pack(fill="x", pady=(4, 0))
        if mascara or ao_mudar:
            self.entrada.bind("<KeyRelease>", self._ao_digitar)

    def _ao_digitar(self, _evento=None):
        if self._mascara:
            reformatar_entrada(self.entrada, self._mascara)
        if self._ao_mudar:
            self._ao_mudar()

    def valor(self):
        return self.entrada.get().strip()

    def valor_sem_cortar(self):
        """Texto exatamente como digitado (para senhas, em que espaços contam)."""
        return self.entrada.get()

    def definir(self, texto):
        texto = str(texto)
        if self._mascara:
            texto = self._mascara(texto)
        self.entrada.delete(0, "end")
        self.entrada.insert(0, texto)

    def limpar(self):
        self.entrada.delete(0, "end")
        # tira o foco do campo para o texto de exemplo (placeholder) voltar a aparecer
        self.winfo_toplevel().focus_set()

    def marcar_erro(self, com_erro, cor_erro="#DC2626"):
        """Pinta a borda de vermelho (ou volta ao normal)."""
        self.entrada.configure(border_color=cor_erro if com_erro else COR_BORDA_CAMPO)


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
