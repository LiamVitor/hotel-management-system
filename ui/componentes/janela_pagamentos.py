"""Janela financeira de uma reserva: resumo, novo pagamento, reembolsos e histórico."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import (FORMAS_PAGAMENTO, PAGTO_CANCELADA, PAGTO_PAGO, PAGTO_PARCIAL,
                                  PAGTO_PENDENTE, RESERVA_CANCELADA)
from src.utils.formatacao import formatar_data, formatar_moeda, ler_valor
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto, somente_numero
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.janela_reembolso import abrir_reembolso
from ui.componentes.tabela import Tabela
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COLUNAS = [("Data e hora", "data_hora", 125), ("Valor", "valor", 100), ("Forma", "forma", 125),
           ("Tipo", "tipo", 90), ("Responsável", "responsavel", 130), ("Detalhe", "detalhe", 215)]

COR_SITUACAO = {PAGTO_PENDENTE: VERMELHO, PAGTO_PARCIAL: "#D97706", PAGTO_PAGO: VERDE,
                PAGTO_CANCELADA: "#6B7280"}
COR_REEMBOLSO = "#D97706"
DICA_DETALHE = "Clique em um lançamento para ver os detalhes."


def abrir_pagamentos(master, servicos, reserva_id, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada.

    ao_atualizar: funcao() chamada a cada pagamento ou reembolso registrado, para a tela
    de trás recarregar a tabela.
    """
    janela = JanelaPagamentos(master, servicos, reserva_id, ao_atualizar)
    master.wait_window(janela)


class JanelaPagamentos(ctk.CTkToplevel):
    LARGURA, ALTURA = 980, 790

    def __init__(self, master, servicos, reserva_id, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self.reserva_id = reserva_id
        self._ao_atualizar = ao_atualizar
        self.reserva = servicos.reservas.buscar_por_id(reserva_id)

        self.title(f"Pagamentos da reserva {reserva_id:04d}")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar_cabecalho()
        self._montar_resumo()
        self._montar_formulario()
        self._montar_historico()
        self._atualizar()

        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    # ---------- montagem ----------
    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)   # cabe em telas pequenas
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    def _montar_cabecalho(self):
        hospede = self.servicos.hospedes.buscar_por_id(self.reserva.hospede_id)
        quarto = self.servicos.quartos.buscar_por_id(self.reserva.quarto_id)
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=24, pady=(20, 12))
        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(textos, text=f"Pagamentos da reserva {self.reserva_id:04d}",
                     font=fonte(18, True), text_color=COR_TEXTO).pack(anchor="w")
        detalhe = (f"{hospede.nome if hospede else '—'}  ·  Quarto {quarto.numero if quarto else '—'}"
                   f"  ·  {formatar_data(self.reserva.data_entrada)} a "
                   f"{formatar_data(self.reserva.data_saida)}")
        ctk.CTkLabel(textos, text=detalhe, font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w", pady=(2, 0))
        self.selo = ctk.CTkLabel(cabecalho, text="", width=100, height=28, corner_radius=14,
                                 font=fonte(12, True), text_color="white")
        self.selo.pack(side="right")

    def _montar_resumo(self):
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=24)
        linha.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="resumo")
        self.cartao_total = CartaoResumo(linha, "Total da reserva", "—")
        self.cartao_pago = CartaoResumo(linha, "Pago (líquido)", "—", VERDE)
        self.cartao_reembolsado = CartaoResumo(linha, "Reembolsado", "—", COR_REEMBOLSO)
        self.cartao_saldo = CartaoResumo(linha, "Saldo pendente", "—")
        cartoes = (self.cartao_total, self.cartao_pago, self.cartao_reembolsado, self.cartao_saldo)
        for coluna, cartao in enumerate(cartoes):
            cartao.grid(row=0, column=coluna, sticky="ew",
                        padx=(0 if coluna == 0 else 5, 0 if coluna == 3 else 5))

    def _montar_formulario(self):
        self.form = Cartao(self, "Registrar pagamento")
        self.form.pack(fill="x", padx=24, pady=(14, 0))
        grade = ctk.CTkFrame(self.form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1), weight=1, uniform="campos")
        self.valor = CampoTexto(grade, "Valor (R$)", "0,00", mascara=somente_numero)
        self.forma = CampoSelecao(grade, "Forma de pagamento", FORMAS_PAGAMENTO)
        self.valor.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.forma.grid(row=0, column=1, sticky="ew", padx=(8, 0))

        botoes = ctk.CTkFrame(self.form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(12, 0))
        self.btn_registrar = botao_primario(botoes, "Registrar pagamento", self._registrar, 180)
        self.btn_registrar.pack(side="left")
        self.btn_saldo = botao_secundario(botoes, "Preencher com o saldo", self._preencher_saldo, 180)
        self.btn_saldo.pack(side="left", padx=10)
        self.lbl_form = ctk.CTkLabel(self.form, text="", font=fonte(12, True),
                                     text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
                                     wraplength=self.LARGURA - 100)
        self.lbl_form.pack(anchor="w", padx=20, pady=(8, 14))

    def _montar_historico(self):
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")
        self.btn_reembolso = botao_secundario(rodape, "Registrar reembolso...",
                                              self._abrir_reembolso, 190)
        if Sessao.pode("pagamentos.reembolsar"):
            self.btn_reembolso.pack(side="left")

        historico = Cartao(self, "Histórico financeiro da reserva")
        historico.pack(fill="both", expand=True, padx=24, pady=(14, 0))
        # o texto de detalhe é empacotado antes, embaixo, para nunca ser espremido pela tabela
        self.lbl_detalhe = ctk.CTkLabel(historico, text=DICA_DETALHE, font=fonte(12),
                                        text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
                                        wraplength=self.LARGURA - 100)
        self.lbl_detalhe.pack(side="bottom", anchor="w", padx=20, pady=(0, 12))
        self.tabela = Tabela(historico, COLUNAS, altura=90, ao_selecionar=self._mostrar_detalhe)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 6))

    # ---------- estado ----------
    def _motivo_bloqueio(self, resumo):
        if not Sessao.pode("pagamentos.registrar"):
            return "O seu perfil não pode registrar pagamentos."
        if self.reserva.situacao == RESERVA_CANCELADA:
            return "Reserva cancelada: não aceita novos pagamentos."
        if resumo.saldo <= 0:
            return "Reserva quitada: não há saldo pendente."
        return None

    def _habilitar_formulario(self, habilitar):
        estado = "normal" if habilitar else "disabled"
        self.valor.entrada.configure(state=estado)
        self.forma.caixa.configure(state="readonly" if habilitar else "disabled")
        self.btn_registrar.configure(state=estado)
        self.btn_saldo.configure(state=estado)

    def _atualizar(self, mensagem=None, erro=False):
        self.reserva = self.servicos.reservas.buscar_por_id(self.reserva_id)
        resumo = self.servicos.pagamentos.resumo(self.reserva_id)

        self.cartao_total.atualizar(formatar_moeda(resumo.valor_total))
        self.cartao_pago.atualizar(formatar_moeda(resumo.total_pago))
        self.cartao_reembolsado.atualizar(formatar_moeda(resumo.total_reembolsado))
        self.cartao_saldo.atualizar(formatar_moeda(resumo.saldo))
        self.cartao_saldo._valor.configure(text_color=VERMELHO if resumo.saldo > 0 else VERDE)
        self.selo.configure(text=resumo.situacao, fg_color=COR_SITUACAO[resumo.situacao])

        historico = self.servicos.pagamentos.historico(self.reserva_id)
        self.tabela.carregar(self.servicos.linhas_pagamentos(historico)[::-1])   # mais recente primeiro
        self.lbl_detalhe.configure(text=DICA_DETALHE if historico else "Nenhum lançamento ainda.")
        self.btn_reembolso.configure(state="normal" if resumo.total_pago > 0 else "disabled")

        motivo = self._motivo_bloqueio(resumo)
        self._habilitar_formulario(motivo is None)
        texto = mensagem or motivo or ""
        cor = VERMELHO if erro else (VERDE if mensagem else COR_TEXTO_SUAVE)
        self.lbl_form.configure(text=texto, text_color=cor)

    def _mostrar_detalhe(self, linha):
        self.lbl_detalhe.configure(text=linha["descricao"])

    # ---------- ações ----------
    def _preencher_saldo(self):
        saldo = self.servicos.pagamentos.resumo(self.reserva_id).saldo
        self.valor.definir(f"{saldo:.2f}".replace(".", ","))

    def _registrar(self):
        try:
            valor = ler_valor(self.valor.valor())
        except ValueError as erro:
            self._atualizar(str(erro), erro=True)
            return
        forma = self.forma.valor()
        if not forma:
            self._atualizar("Selecione a forma de pagamento.", erro=True)
            return
        confirmar = messagebox.askyesno(
            "Confirmar pagamento",
            f"Registrar pagamento de {formatar_moeda(valor)} em {forma}?\n\n"
            "Depois de lançado, o pagamento não pode ser alterado nem apagado.", parent=self)
        if not confirmar:
            return
        try:
            self.servicos.pagamentos.registrar(self.reserva_id, valor, forma)
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível registrar", str(erro), parent=self)
            self._atualizar()
            return

        self.valor.limpar()
        self.forma.limpar()
        mensagem = f"Pagamento de {formatar_moeda(valor)} registrado."
        if self.servicos.pagamentos.resumo(self.reserva_id).saldo <= 0:
            mensagem += " Reserva quitada."
        self._atualizar(mensagem)
        if self._ao_atualizar:
            self._ao_atualizar()

    def _abrir_reembolso(self):
        """Abre o reembolso já apontando para o pagamento selecionado na tabela, se houver."""
        linha = self.tabela.selecionado()
        origem_id = linha["id"] if linha and linha["tipo"] == "Pagamento" else None
        abrir_reembolso(self, self.servicos, self.reserva_id, origem_id,
                        ao_atualizar=self._apos_reembolso)
        if self.winfo_exists():
            self.grab_set()                 # a janela de reembolso soltou o bloqueio ao fechar

    def _apos_reembolso(self):
        self._atualizar("Reembolso registrado.")
        if self._ao_atualizar:
            self._ao_atualizar()

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
