"""Janela para registrar a devolução de um valor ao hóspede (reembolso)."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import FORMAS_PAGAMENTO, MOTIVO_REEMBOLSO_MAX
from src.utils.formatacao import formatar_moeda, ler_valor
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto, somente_numero
from ui.componentes.cartao import Cartao
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

SEM_ORIGEM = "Somente a reserva (sem vincular a um pagamento)"


def abrir_reembolso(master, servicos, reserva_id, pagamento_origem_id=None, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada.

    pagamento_origem_id: pagamento que já vem escolhido (opcional)
    ao_atualizar: funcao() chamada depois que o reembolso é registrado
    """
    janela = JanelaReembolso(master, servicos, reserva_id, pagamento_origem_id, ao_atualizar)
    master.wait_window(janela)


class JanelaReembolso(ctk.CTkToplevel):
    LARGURA, ALTURA = 700, 620

    def __init__(self, master, servicos, reserva_id, pagamento_origem_id=None, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self.reserva_id = reserva_id
        self._ao_atualizar = ao_atualizar
        self._opcoes = {}          # texto da lista -> (id do pagamento ou None, valor máximo)
        self.resumo = servicos.pagamentos.resumo(reserva_id)

        self.title(f"Reembolso da reserva {reserva_id:04d}")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar(servicos.reservas.buscar_por_id(reserva_id))
        self._carregar_origens(pagamento_origem_id)

        self.bind("<Escape>", lambda _e: self.destroy())
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
        ctk.CTkLabel(self, text="Registrar reembolso", font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w", padx=24, pady=(20, 0))
        ctk.CTkLabel(self, text=f"Reserva {self.reserva_id:04d}  ·  {hospede.nome if hospede else '—'}",
                     font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w", padx=24, pady=(2, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Cancelar", self.destroy, 120).pack(side="right")

        valores = Cartao(self)
        valores.pack(fill="x", padx=24)
        valores.grid_columnconfigure((0, 1, 2), weight=1, uniform="valores")
        self._estatistica(valores, 0, "Pago (já sem reembolsos)",
                          formatar_moeda(self.resumo.total_pago), VERDE)
        self._estatistica(valores, 1, "Já reembolsado",
                          formatar_moeda(self.resumo.total_reembolsado), COR_TEXTO)
        self.lbl_maximo = self._estatistica(valores, 2, "Máximo para esta origem", "—", COR_TEXTO)

        form = Cartao(self, "Dados do reembolso")
        form.pack(fill="x", padx=24, pady=(14, 0))
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1), weight=1, uniform="campos")
        self.origem = CampoSelecao(grade, "Referente a", [SEM_ORIGEM], self._ao_mudar_origem)
        self.valor = CampoTexto(grade, "Valor (R$)", "0,00", mascara=somente_numero)
        self.forma = CampoSelecao(grade, "Forma do reembolso", FORMAS_PAGAMENTO)
        self.motivo = CampoTexto(grade, "Motivo (obrigatório)",
                                 "Ex.: cancelamento da reserva, cobrança em duplicidade")
        self.origem.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.valor.grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=(0, 10))
        self.forma.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(0, 10))
        self.motivo.grid(row=2, column=0, columnspan=2, sticky="ew")

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(14, 0))
        self.btn_registrar = botao_primario(botoes, "Registrar reembolso", self._registrar, 180)
        self.btn_registrar.pack(side="left")
        self.btn_maximo = botao_secundario(botoes, "Preencher com o máximo", self._preencher_maximo, 190)
        self.btn_maximo.pack(side="left", padx=10)
        self.lbl_aviso = ctk.CTkLabel(form, text="", font=fonte(12, True), text_color=COR_TEXTO_SUAVE,
                                      anchor="w", justify="left", wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

    @staticmethod
    def _estatistica(pai, coluna, rotulo, valor, cor):
        quadro = ctk.CTkFrame(pai, fg_color="transparent")
        quadro.grid(row=0, column=coluna, sticky="w", padx=20, pady=14)
        ctk.CTkLabel(quadro, text=rotulo, font=fonte(12), text_color=COR_TEXTO_SUAVE).pack(anchor="w")
        rotulo_valor = ctk.CTkLabel(quadro, text=valor, font=fonte(18, True), text_color=cor)
        rotulo_valor.pack(anchor="w")
        return rotulo_valor

    # ---------- origem e limites ----------
    def _carregar_origens(self, pagamento_origem_id):
        self._opcoes = {SEM_ORIGEM: (None, self.resumo.total_pago)}
        escolhido = SEM_ORIGEM
        for pagamento, restante in self.servicos.pagamentos.reembolsaveis(self.reserva_id):
            texto = (f"{pagamento.data_hora:%d/%m/%Y %H:%M}  ·  {formatar_moeda(pagamento.valor)}  ·  "
                     f"{pagamento.forma}  (reembolsável {formatar_moeda(restante)})")
            self._opcoes[texto] = (pagamento.id, min(restante, self.resumo.total_pago))
            if pagamento.id == pagamento_origem_id:
                escolhido = texto
        self.origem.definir_opcoes(list(self._opcoes))
        self.origem.definir(escolhido)

        if self.resumo.total_pago <= 0:
            self._bloquear("Esta reserva não tem valor pago para reembolsar.")
        self._ao_mudar_origem()

    def _maximo(self):
        return self._opcoes.get(self.origem.valor(), (None, 0.0))[1]

    def _ao_mudar_origem(self):
        self.lbl_maximo.configure(text=formatar_moeda(self._maximo()))

    def _bloquear(self, motivo):
        for campo in (self.valor.entrada, self.motivo.entrada):
            campo.configure(state="disabled")
        self.origem.caixa.configure(state="disabled")
        self.forma.caixa.configure(state="disabled")
        self.btn_registrar.configure(state="disabled")
        self.btn_maximo.configure(state="disabled")
        self.lbl_aviso.configure(text=motivo, text_color=COR_TEXTO_SUAVE)

    def _aviso(self, texto):
        self.lbl_aviso.configure(text=texto, text_color=VERMELHO)

    # ---------- ações ----------
    def _preencher_maximo(self):
        self.valor.definir(f"{self._maximo():.2f}".replace(".", ","))

    def _registrar(self):
        try:
            valor = ler_valor(self.valor.valor())
        except ValueError as erro:
            self._aviso(str(erro))
            return
        forma = self.forma.valor()
        if not forma:
            self._aviso("Selecione a forma do reembolso.")
            return
        motivo = self.motivo.valor()
        if len(motivo) < 3:
            self._aviso("Informe o motivo do reembolso.")
            return
        if len(motivo) > MOTIVO_REEMBOLSO_MAX:
            self._aviso(f"O motivo deve ter no máximo {MOTIVO_REEMBOLSO_MAX} caracteres.")
            return

        origem_id = self._opcoes.get(self.origem.valor(), (None, 0))[0]
        confirmar = messagebox.askyesno(
            "Confirmar reembolso",
            f"Registrar reembolso de {formatar_moeda(valor)} em {forma}?\n\nMotivo: {motivo}\n\n"
            "Depois de lançado, o reembolso não pode ser alterado nem apagado. "
            "O pagamento original será mantido no histórico.", parent=self)
        if not confirmar:
            return
        try:
            self.servicos.pagamentos.registrar_reembolso(
                self.reserva_id, valor, forma, motivo, pagamento_origem_id=origem_id)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível registrar", str(erro), parent=self)
            return
        if self._ao_atualizar:
            self._ao_atualizar()
        self.destroy()

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
