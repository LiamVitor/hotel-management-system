import customtkinter as ctk

from ui.componentes.botoes import botao_secundario
from ui.componentes.cartao import Cartao
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, ESTILO_NIVEL_ALERTA, VERDE, fonte

MARGEM_TEXTO = 150      # espaço reservado ao botão e às bordas ao quebrar a mensagem


class ListaAlertas(Cartao):
    """Cartão "Atenção": uma linha por alerta (faixa colorida, mensagem e botão "Abrir").

    `carregar(alertas, ao_abrir)`: `ao_abrir(alerta)` é chamado no clique do botão. Sem alertas,
    mostra uma linha dizendo que está tudo em dia (o cartão não some, para a tela não pular).
    """

    def __init__(self, master, titulo="Atenção"):
        super().__init__(master, titulo)
        self.corpo = ctk.CTkFrame(self, fg_color="transparent")
        self.corpo.pack(fill="x", padx=20, pady=(0, 14))
        self._mensagens = []
        self.corpo.bind("<Configure>", self._ajustar_quebra)

    def carregar(self, alertas, ao_abrir):
        for filho in self.corpo.winfo_children():
            filho.destroy()
        self._mensagens = []
        if not alertas:
            self._linha(VERDE, "Nenhuma pendência no momento. Está tudo em dia.", None, None)
            return
        for alerta in alertas:
            cor = ESTILO_NIVEL_ALERTA[alerta.nivel][1]
            self._linha(cor, alerta.mensagem, alerta, ao_abrir)
        self._ajustar_quebra()

    def mensagens(self):
        """Textos exibidos agora (usado nos testes)."""
        return [m.cget("text") for m in self._mensagens]

    def _linha(self, cor, texto, alerta, ao_abrir):
        linha = ctk.CTkFrame(self.corpo, fg_color="transparent")
        linha.pack(fill="x", pady=3)
        ctk.CTkFrame(linha, width=4, height=28, corner_radius=2, fg_color=cor
                     ).pack(side="left", fill="y", padx=(0, 10))
        if alerta is not None:
            botao_secundario(linha, "Abrir", lambda a=alerta: ao_abrir(a), 80
                             ).pack(side="right", padx=(10, 0))
        mensagem = ctk.CTkLabel(linha, text=texto, font=fonte(13),
                                text_color=COR_TEXTO if alerta else COR_TEXTO_SUAVE,
                                anchor="w", justify="left")
        mensagem.pack(side="left", fill="x", expand=True)
        self._mensagens.append(mensagem)

    def _ajustar_quebra(self, _evento=None):
        """Quebra a mensagem na largura disponível, para não ficar cortada em janelas estreitas."""
        largura = max(240, self.corpo.winfo_width() - MARGEM_TEXTO + 70)
        for mensagem in self._mensagens:
            mensagem.configure(wraplength=largura)
