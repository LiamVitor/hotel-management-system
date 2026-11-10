"""Janela para cancelar uma reserva, pedindo o motivo."""
import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import MOTIVO_CANCELAMENTO_MAX
from src.utils.formatacao import formatar_data
from ui.componentes.botoes import botao_perigo, botao_secundario
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, fonte


def abrir_cancelamento(master, servicos, reserva_id, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada. Devolve True se a reserva foi cancelada.

    ao_atualizar: funcao() chamada depois que o cancelamento é registrado
    """
    janela = JanelaCancelamento(master, servicos, reserva_id, ao_atualizar)
    master.wait_window(janela)
    return janela.cancelada


class JanelaCancelamento(ctk.CTkToplevel):
    LARGURA, ALTURA = 600, 380

    def __init__(self, master, servicos, reserva_id, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self.reserva_id = reserva_id
        self._ao_atualizar = ao_atualizar
        self.cancelada = False

        self.title(f"Cancelar reserva {reserva_id:04d}")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar(servicos.reservas.buscar_por_id(reserva_id))

        self.bind("<Escape>", lambda _e: self.destroy())
        self.bind("<Return>", lambda _e: self._confirmar())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    # ---------- montagem ----------
    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    def _montar(self, reserva):
        hospede = self.servicos.hospedes.buscar_por_id(reserva.hospede_id)
        quarto = self.servicos.quartos.buscar_por_id(reserva.quarto_id)
        ctk.CTkLabel(self, text="Cancelar reserva", font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=24, pady=(20, 0))
        ctk.CTkLabel(
            self, font=fonte(13), text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
            text=(f"Reserva {reserva.id:04d}  ·  {hospede.nome if hospede else '—'}  ·  Quarto "
                  f"{quarto.numero if quarto else '—'}\n"
                  f"{formatar_data(reserva.data_entrada)} a {formatar_data(reserva.data_saida)}")
        ).pack(anchor="w", padx=24, pady=(2, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Voltar", self.destroy, 120).pack(side="right")
        botao_perigo(rodape, "Cancelar reserva", self._confirmar, 170).pack(side="right", padx=10)

        form = Cartao(self, "Motivo do cancelamento")
        form.pack(fill="x", padx=24)
        self.motivo = CampoTexto(form, "Motivo (obrigatório)",
                                 "Ex.: hóspede desistiu, mudança de datas, pagamento não realizado")
        self.motivo.pack(fill="x", padx=20)
        self.lbl_aviso = ctk.CTkLabel(
            form, text=(f"Até {MOTIVO_CANCELAMENTO_MAX} caracteres. O cancelamento fica registrado "
                        "com a data, a hora e o seu usuário."),
            font=fonte(12), text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
            wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

    # ---------- ações ----------
    def _confirmar(self):
        """Pede o cancelamento ao service; a mensagem de erro dele aparece aqui mesmo."""
        try:
            self.servicos.reservas.cancelar(self.reserva_id, self.motivo.valor())
        except ErroNegocio as erro:
            self.lbl_aviso.configure(text=str(erro), text_color=VERMELHO)
            self.motivo.marcar_erro(True)
            return
        self.cancelada = True
        if self._ao_atualizar:
            self._ao_atualizar()
        self.destroy()

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
        self.motivo.entrada.focus_set()
