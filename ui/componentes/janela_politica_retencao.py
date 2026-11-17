"""Janela da administração para definir a regra de retenção e ver o histórico de definições."""
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import RETENCAO_DIAS_MAX
from src.utils.formatacao import formatar_data_hora, formatar_percentual, ler_valor
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campos import CampoTexto, somente_numero
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COLUNAS = [("Antecedência", "dias", 90), ("Cancel. tardio", "tardio", 100),
           ("No-show", "no_show", 80), ("Definida em", "definido_em", 130),
           ("Definida por", "responsavel", 130)]


def abrir_politica_retencao(master, servicos, ao_atualizar=None):
    janela = JanelaPoliticaRetencao(master, servicos, ao_atualizar)
    master.wait_window(janela)


class JanelaPoliticaRetencao(ctk.CTkToplevel):
    LARGURA, ALTURA = 640, 660

    def __init__(self, master, servicos, ao_atualizar=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self._ao_atualizar = ao_atualizar
        self.title("Regra de retenção")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())
        self._montar()
        self._carregar()
        self.bind("<Escape>", lambda _e: self.destroy())
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
        ctk.CTkLabel(self, text="Regra de retenção", font=fonte(18, True),
                     text_color=COR_TEXTO).pack(anchor="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(self, text="Define quanto do valor da reserva fica retido quando ela é "
                                "cancelada com pouca antecedência ou marcada como no-show. A "
                                "retenção nunca passa do que o hóspede já pagou. Mudar a regra "
                                "não altera cancelamentos já registrados.",
                     font=fonte(12), text_color=COR_TEXTO_SUAVE, wraplength=self.LARGURA - 48,
                     justify="left").pack(anchor="w", padx=24, pady=(0, 12))

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")

        form = Cartao(self, "Definir regra")
        form.pack(fill="x", padx=24)
        linha = ctk.CTkFrame(form, fg_color="transparent")
        linha.pack(fill="x", padx=20)
        linha.grid_columnconfigure((0, 1, 2), weight=1, uniform="campos")
        self.dias = CampoTexto(linha, f"Antecedência mínima (dias, até {RETENCAO_DIAS_MAX})", "7",
                               mascara=lambda t: "".join(c for c in t if c.isdigit()))
        self.tardio = CampoTexto(linha, "Retido no cancelamento tardio (%)", "30,00",
                                 mascara=somente_numero)
        self.no_show = CampoTexto(linha, "Retido no no-show (%)", "100,00", mascara=somente_numero)
        for coluna, campo in enumerate((self.dias, self.tardio, self.no_show)):
            campo.grid(row=0, column=coluna, sticky="ew", padx=4)
        botao_primario(form, "Salvar regra", self._salvar, 160).pack(anchor="w", padx=20, pady=(12, 0))
        self.lbl_aviso = ctk.CTkLabel(form, text="", font=fonte(12, True), anchor="w",
                                      justify="left", wraplength=self.LARGURA - 100)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(8, 16))

        lista = Cartao(self, "Histórico de definições (a mais recente é a que vale)")
        lista.pack(fill="both", expand=True, padx=24, pady=(12, 0))
        self.tabela = Tabela(lista, COLUNAS, altura=150)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 12))

    def _carregar(self):
        historico = self.servicos.politica_retencao.historico()
        self.tabela.carregar(self.servicos.linhas_politica_retencao(historico))
        if historico:
            p = historico[0][0]
            self.dias.definir(str(p.dias_antecedencia))
            self.tardio.definir(f"{p.percentual_cancelamento_tardio:.2f}".replace(".", ","))
            self.no_show.definir(f"{p.percentual_no_show:.2f}".replace(".", ","))

    def _aviso(self, texto, erro=False):
        self.lbl_aviso.configure(text=texto, text_color=VERMELHO if erro else VERDE)

    def _salvar(self):
        try:
            dias = int(self.dias.valor() or "")
            tardio, no_show = ler_valor(self.tardio.valor()), ler_valor(self.no_show.valor())
        except (ErroNegocio, ValueError):
            self._aviso("Informe a antecedência em dias e os percentuais em números.", erro=True)
            return
        if not messagebox.askyesno(
                "Confirmar regra de retenção",
                f"Cancelamento com menos de {dias} dia(s) de antecedência: reter "
                f"{formatar_percentual(tardio)}.\nNo-show: reter {formatar_percentual(no_show)}."
                f"\n\nValerá para os próximos cancelamentos e no-shows."):
            return
        try:
            self.servicos.politica_retencao.definir(dias, tardio, no_show)
        except ErroNegocio as erro:
            self._aviso(str(erro), erro=True)
            return
        self._carregar()
        self._aviso("Regra salva.")
        if self._ao_atualizar:
            self._ao_atualizar()
