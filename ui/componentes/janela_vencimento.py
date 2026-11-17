"""Janela para registrar a data de vencimento de uma reserva (contas a receber)."""
import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.formatacao import formatar_data, formatar_moeda
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.cartao import Cartao
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, fonte


def abrir_vencimento(master, servicos, conta, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada. Devolve True se o vencimento foi alterado.

    conta: a ContaReceber (linha do relatório) cujo vencimento será alterado.
    ao_atualizar: funcao() chamada depois que o novo vencimento é gravado.
    """
    janela = JanelaVencimento(master, servicos, conta, ao_atualizar)
    master.wait_window(janela)
    return janela.alterado


class JanelaVencimento(ctk.CTkToplevel):
    LARGURA, ALTURA = 560, 360

    def __init__(self, master, servicos, conta, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self.conta = conta
        self._ao_atualizar = ao_atualizar
        self.alterado = False

        self.title(f"Vencimento da reserva {conta.reserva_id:04d}")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar()

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self._confirmar())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    def _montar(self):
        c = self.conta
        ctk.CTkLabel(self, text="Data de vencimento", font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=24, pady=(20, 0))
        ctk.CTkLabel(
            self, font=fonte(13), text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
            text=(f"Reserva {c.reserva_id:04d}  ·  {c.hospede}\n"
                  f"Total {formatar_moeda(c.valor_total)}  ·  pago {formatar_moeda(c.valor_pago)}"
                  f"  ·  saldo {formatar_moeda(c.saldo)}")
        ).pack(anchor="w", padx=24, pady=(2, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Voltar", self.destroy, 120).pack(side="right")
        botao_primario(rodape, "Salvar", self._confirmar, 120).pack(side="right", padx=10)

        form = Cartao(self, "Novo vencimento")
        form.pack(fill="x", padx=24)
        self.data = CampoData(form, "Vence em")
        self.data.pack(fill="x", padx=20)
        self.data.definir(formatar_data(c.data_vencimento))
        self.lbl_aviso = ctk.CTkLabel(
            form, text="A alteração fica registrada com a data, a hora e o seu usuário.",
            font=fonte(12), text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
            wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

    def _confirmar(self):
        """Pede a alteração ao service; a mensagem de erro dele aparece aqui mesmo."""
        nova = self.data.data()
        try:
            if nova is None:
                raise ErroNegocio("Informe a data no formato dd/mm/aaaa.")
            self.servicos.contas_receber.definir_vencimento(self.conta.reserva_id, nova)
        except ErroNegocio as erro:
            self.lbl_aviso.configure(text=str(erro), text_color=VERMELHO)
            return
        self.alterado = True
        if self._ao_atualizar:
            self._ao_atualizar()
        self.destroy()

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
