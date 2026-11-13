"""Janela para definir o saldo inicial do caixa e ver o histórico das definições."""
from datetime import date
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.formatacao import formatar_data, formatar_data_hora, formatar_moeda, ler_valor
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoTexto, somente_numero
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COLUNAS = [("Saldo inicial", "valor", 120), ("Vale desde", "data", 100),
           ("Definido em", "definido_em", 130), ("Definido por", "responsavel", 140)]


def abrir_saldo_inicial(master, servicos, ao_atualizar=None):
    """Abre a janela e espera ela ser fechada.

    ao_atualizar: funcao() chamada quando o saldo inicial muda, para a tela de trás recalcular.
    """
    janela = JanelaSaldoInicial(master, servicos, ao_atualizar)
    master.wait_window(janela)


class JanelaSaldoInicial(ctk.CTkToplevel):
    LARGURA, ALTURA = 640, 620

    def __init__(self, master, servicos, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self._ao_atualizar = ao_atualizar

        self.title("Saldo inicial do caixa")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar()
        self._carregar()

        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    def _ativar(self):
        self.lift()
        self.focus_force()
        self.grab_set()

    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    def _montar(self):
        ctk.CTkLabel(self, text="Saldo inicial do caixa", font=fonte(18, True),
                     text_color=COR_TEXTO).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="É o dinheiro que o caixa tinha no começo da data escolhida. "
                                "O caixa conta só os pagamentos, reembolsos e despesas a partir "
                                "dessa data.", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                     wraplength=self.LARGURA - 48, justify="left"
                     ).pack(anchor="w", padx=24, pady=(0, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")

        form = Cartao(self, "Definir saldo inicial")
        form.pack(fill="x", padx=24)
        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(fill="x", padx=20)
        linha.grid_columnconfigure((0, 1), weight=1, uniform="campos")
        self.valor = CampoTexto(linha, "Saldo inicial (R$)", "0,00", mascara=somente_numero)
        self.data = CampoData(linha, "Vale desde")
        self.valor.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.data.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        botao_primario(form, "Salvar saldo inicial", self._salvar, 200
                       ).pack(anchor="w", padx=20, pady=(12, 0))
        self.lbl_aviso = ctk.CTkLabel(form, text="", font=fonte(12, True), anchor="w",
                                      justify="left", wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

        lista = Cartao(self, "Histórico de definições (a mais recente é a que vale)")
        lista.pack(fill="both", expand=True, padx=24, pady=(12, 0))
        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    def _carregar(self):
        historico = self.servicos.caixa.historico_saldo_inicial()
        self.tabela.carregar([
            {"valor": formatar_moeda(s.valor), "data": formatar_data(s.data_referencia),
             "definido_em": formatar_data_hora(s.definido_em), "responsavel": nome}
            for s, nome in historico])
        if historico:
            vigente = historico[0][0]
            self.valor.definir(f"{vigente.valor:.2f}".replace(".", ","))
            self.data.definir(formatar_data(vigente.data_referencia))
        else:
            self.data.definir(formatar_data(date.today()))

    def _aviso(self, texto, erro=False):
        self.lbl_aviso.configure(text=texto, text_color=VERMELHO if erro else VERDE)

    def _salvar(self):
        try:
            valor = ler_valor(self.valor.valor())
            data = self.data.data()
            if data is None:
                raise ErroNegocio("Informe uma data válida (dd/mm/aaaa).")
        except (ErroNegocio, ValueError) as erro:
            self._aviso(str(erro), erro=True)
            return
        if not messagebox.askyesno(
                "Confirmar saldo inicial",
                f"Definir o saldo inicial em {formatar_moeda(valor)}, valendo desde "
                f"{formatar_data(data)}?\n\nOs saldos de todos os períodos serão recalculados."):
            return
        try:
            self.servicos.caixa.definir_saldo_inicial(valor, data)
        except ErroNegocio as erro:
            self._aviso(str(erro), erro=True)
            return
        self._carregar()
        self._aviso("Saldo inicial salvo.")
        if self._ao_atualizar:
            self._ao_atualizar()
