"""Campo de data: a pessoa pode digitar (com máscara dd/mm/aaaa) ou escolher num calendário."""
import calendar
from datetime import date, timedelta

import customtkinter as ctk
from PIL import Image, ImageDraw

from src.utils.formatacao import formatar_data, ler_data, mascara_data
from ui.componentes.botoes import botao_secundario
from ui.componentes.campos import reformatar_entrada
from ui.estilos import (AZUL, AZUL_HOVER, COR_BORDA_CAMPO, COR_FUNDO, COR_SELECAO, COR_TEXTO,
                        COR_TEXTO_SUAVE, fonte)

MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto",
         "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS_DA_SEMANA = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

COR_DIA_BLOQUEADO = "#D1D5DB"
COR_DIA_OUTRO_MES = "#9CA3AF"


def dias_do_calendario(ano, mes):
    """As 42 datas (6 semanas, começando no domingo) que preenchem a grade do mês."""
    primeira_semana = calendar.Calendar(firstweekday=6).monthdatescalendar(ano, mes)[0]
    inicio = primeira_semana[0]
    return [inicio + timedelta(days=i) for i in range(42)]


def _icone_calendario(cor="#6B7280"):
    """Desenha o ícone de calendário (sem depender de arquivo de imagem nem de fonte de emoji)."""
    escala, lado = 4, 18
    imagem = Image.new("RGBA", (lado * escala, lado * escala), (0, 0, 0, 0))
    d = ImageDraw.Draw(imagem)
    espessura = 2 * escala
    d.rounded_rectangle((2 * escala, 4 * escala, 16 * escala, 16 * escala),
                        radius=2 * escala, outline=cor, width=espessura)
    d.line((2 * escala, 8 * escala, 16 * escala, 8 * escala), fill=cor, width=espessura)
    for x in (6, 12):
        d.line((x * escala, 1 * escala, x * escala, 5 * escala), fill=cor, width=espessura)
    for x in (5, 8, 11):
        for y in (9.6, 11.9):
            d.rectangle((x * escala, y * escala, (x + 1.5) * escala, (y + 1.5) * escala), fill=cor)
    return ctk.CTkImage(light_image=imagem, size=(lado, lado))


class JanelaCalendario(ctk.CTkToplevel):
    """Calendário em janela pequena, aberta embaixo do campo de data.

    data_atual:  data que aparece marcada (e o mês que abre); None = mês de hoje
    data_minima: dias antes dela ficam bloqueados; None = sem bloqueio
    ao_escolher: funcao(date) chamada com o dia clicado
    """

    LARGURA, ALTURA = 328, 396

    def __init__(self, master, ancora, data_atual, data_minima, ao_escolher):
        super().__init__(master, fg_color=COR_FUNDO)
        self._data_atual = data_atual
        self._data_minima = data_minima
        self._ao_escolher = ao_escolher
        base = data_atual or data_minima or date.today()
        self._ano, self._mes = base.year, base.month

        self.title("Escolher data")
        self.resizable(False, False)
        self._posicionar(ancora)
        self.transient(master.winfo_toplevel())

        self._montar_cabecalho()
        self._montar_rodape()
        self._grade = ctk.CTkFrame(self, fg_color="transparent")
        self._grade.pack(padx=14, pady=(2, 0))
        self._desenhar_mes()

        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    # ---------- montagem ----------
    def _posicionar(self, ancora):
        x = ancora.winfo_rootx()
        y = ancora.winfo_rooty() + ancora.winfo_height() + 4
        tela_largura, tela_altura = self.winfo_screenwidth(), self.winfo_screenheight()
        if y + self.ALTURA > tela_altura:                      # não cabe embaixo: abre em cima
            y = max(ancora.winfo_rooty() - self.ALTURA - 4, 0)
        x = max(min(x, tela_largura - self.LARGURA), 0)
        self.geometry(f"{self.LARGURA}x{self.ALTURA}+{x}+{y}")

    def _montar_cabecalho(self):
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=14, pady=(14, 8))
        for texto, delta, lado in (("«", -12, "left"), ("‹", -1, "left"),
                                   ("»", 12, "right"), ("›", 1, "right")):
            ctk.CTkButton(cabecalho, text=texto, width=34, height=30, corner_radius=6,
                          fg_color="transparent", hover_color=COR_SELECAO, text_color=COR_TEXTO,
                          font=fonte(16, True), command=lambda d=delta: self._mudar_mes(d)
                          ).pack(side=lado, padx=1)
        self._lbl_mes = ctk.CTkLabel(cabecalho, text="", font=fonte(14, True), text_color=COR_TEXTO)
        self._lbl_mes.pack(expand=True)

    def _montar_rodape(self):
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=14, pady=(6, 14))
        hoje = botao_secundario(rodape, "Hoje", self._escolher_hoje, 90)
        hoje.pack(side="left")
        if self._data_minima and date.today() < self._data_minima:
            hoje.configure(state="disabled")
        botao_secundario(rodape, "Fechar", self.destroy, 90).pack(side="right")

    def _desenhar_mes(self):
        for filho in self._grade.winfo_children():
            filho.destroy()
        self._lbl_mes.configure(text=f"{MESES[self._mes - 1]} {self._ano}")
        for coluna, nome in enumerate(DIAS_DA_SEMANA):
            ctk.CTkLabel(self._grade, text=nome, width=42, height=24, font=fonte(11, True),
                         text_color=COR_TEXTO_SUAVE).grid(row=0, column=coluna)
        hoje = date.today()
        for i, dia in enumerate(dias_do_calendario(self._ano, self._mes)):
            self._criar_botao_dia(dia, hoje).grid(row=1 + i // 7, column=i % 7, padx=1, pady=1)

    def _criar_botao_dia(self, dia, hoje):
        bloqueado = self._data_minima is not None and dia < self._data_minima
        selecionado = dia == self._data_atual
        cor_texto = COR_TEXTO if dia.month == self._mes else COR_DIA_OUTRO_MES
        opcoes = dict(fg_color="transparent", hover_color=COR_SELECAO, text_color=cor_texto,
                      border_width=0)
        if dia == hoje:
            opcoes.update(border_width=1, border_color=AZUL)
        if selecionado:
            opcoes.update(fg_color=AZUL, hover_color=AZUL_HOVER, text_color="white")
        if bloqueado:
            opcoes.update(text_color=COR_DIA_BLOQUEADO)
        return ctk.CTkButton(self._grade, text=str(dia.day), width=42, height=36,
                             corner_radius=6, font=fonte(13, selecionado),
                             state="disabled" if bloqueado else "normal",
                             command=lambda d=dia: self._escolher(d), **opcoes)

    # ---------- ações ----------
    def _mudar_mes(self, delta):
        indice = self._ano * 12 + (self._mes - 1) + delta
        self._ano, self._mes = indice // 12, indice % 12 + 1
        self._ano = min(max(self._ano, 1), 9999)
        self._desenhar_mes()

    def _escolher(self, dia):
        self.destroy()
        self._ao_escolher(dia)

    def _escolher_hoje(self):
        self._escolher(date.today())

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()


class CampoData(ctk.CTkFrame):
    """Rótulo + campo de data com botão de calendário.

    A pessoa pode digitar (a barra aparece sozinha: 25122026 vira 25/12/2026) ou clicar no
    ícone e escolher o dia no calendário.

    ao_mudar:    funcao() chamada quando a data muda, digitando ou escolhendo
    data_minima: funcao() -> date | None, menor data liberada no calendário
    ao_escolher: funcao(date) chamada só quando o dia é escolhido no calendário
    """

    def __init__(self, master, rotulo, ao_mudar=None, data_minima=None, ao_escolher=None):
        super().__init__(master, fg_color="transparent")
        self._ao_mudar = ao_mudar
        self._data_minima = data_minima
        self._ao_escolher = ao_escolher
        self._calendario = None

        ctk.CTkLabel(self, text=rotulo, font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w")
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", pady=(4, 0))
        self.entrada = ctk.CTkEntry(linha, placeholder_text="dd/mm/aaaa", width=40, height=36,
                                    fg_color="white", border_color=COR_BORDA_CAMPO,
                                    text_color=COR_TEXTO, placeholder_text_color="#9CA3AF",
                                    font=fonte(13))
        self.entrada.pack(side="left", fill="x", expand=True)
        self.entrada.bind("<KeyRelease>", self._ao_digitar)
        ctk.CTkButton(linha, text="", image=_icone_calendario(), width=36, height=36,
                      corner_radius=6, fg_color="white", hover_color="#F9FAFB",
                      border_width=1, border_color=COR_BORDA_CAMPO,
                      command=self._abrir_calendario).pack(side="left", padx=(6, 0))

    # ---------- valor ----------
    def valor(self):
        return self.entrada.get().strip()

    def data(self):
        """A data digitada como date, ou None se estiver vazia, incompleta ou inválida."""
        texto = self.valor()
        if len(texto) != 10:
            return None
        try:
            return ler_data(texto)
        except ValueError:
            return None

    def definir(self, texto):
        self.entrada.delete(0, "end")
        self.entrada.insert(0, mascara_data(str(texto)))

    def limpar(self):
        self.entrada.delete(0, "end")
        self.winfo_toplevel().focus_set()

    # ---------- eventos ----------
    def _ao_digitar(self, _evento=None):
        reformatar_entrada(self.entrada, mascara_data)
        if self._ao_mudar:
            self._ao_mudar()

    def _abrir_calendario(self):
        if self._calendario is not None and self._calendario.winfo_exists():
            self._calendario.destroy()
            self._calendario = None
            return
        minima = self._data_minima() if self._data_minima else None
        self._calendario = JanelaCalendario(self, self.entrada, self.data(), minima,
                                            self._ao_escolher_no_calendario)

    def _ao_escolher_no_calendario(self, dia):
        self.definir(formatar_data(dia))
        if self._ao_escolher:
            self._ao_escolher(dia)
        if self._ao_mudar:
            self._ao_mudar()
