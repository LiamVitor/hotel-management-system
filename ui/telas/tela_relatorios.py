import math
import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.services.relatorios import relatorio_periodo
from src.utils.constantes import GRANULARIDADE_DIA, GRANULARIDADE_MES, GRANULARIDADE_SEMANA
from src.utils.periodos import ATALHOS_RELATORIO, PERSONALIZADO, periodo_do_atalho
from ui.componentes.botoes import botao_primario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoSelecao
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.tabela import Tabela
from ui.estilos import AZUL, COR_BORDA, COR_CARTAO, COR_TEXTO, COR_TEXTO_SUAVE, FONTE_FAMILIA, fonte
from ui.telas.tela_base import TelaBase
from src.utils.formatacao import formatar_data, formatar_moeda, formatar_percentual, ler_data

LARGURA_GRAFICO = 900
ALTURA_GRAFICO = 290
LARGURA_ROTULO = 48        # espaço que um rótulo do eixo (dd/mm ou mm/aa) ocupa, em pixels
LARGURA_VALOR = 40         # faixa mínima por barra para caber o "100%" em cima dela

# o que cada barra do gráfico representa, conforme o tamanho do período
LEGENDA_BARRAS = {
    GRANULARIDADE_DIA: "Cada barra é um dia.",
    GRANULARIDADE_SEMANA: "Cada barra é a média de ocupação de uma semana "
                          "(7 dias seguidos, a partir da data indicada).",
    GRANULARIDADE_MES: "Cada barra é a média de ocupação de um mês.",
}


# relatórios que o seletor oferece -> qual quadro mostrar
VISOES = {"Ocupação por dia": "dia", "Ocupação por quarto": "quarto"}


class TelaRelatorios(TelaBase):
    titulo = "Relatórios"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self.corpo, "Período")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 18))
        linha.grid_columnconfigure((0, 1, 2), weight=1, uniform="datas")
        self.atalho = CampoSelecao(linha, "Período rápido", ATALHOS_RELATORIO,
                                   self._ao_escolher_atalho)
        self.inicio = CampoData(linha, "Data inicial", self._ao_digitar_periodo)
        self.fim = CampoData(linha, "Data final", self._ao_digitar_periodo)
        self.atalho.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.inicio.grid(row=0, column=1, sticky="ew", padx=10)
        self.fim.grid(row=0, column=2, sticky="ew", padx=10)
        botao_primario(linha, "Gerar relatório", self.gerar, 160).grid(
            row=0, column=3, sticky="s", padx=(10, 0))

        cartoes = ctk.CTkFrame(self.corpo, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        # linha 1: resumo financeiro e de ocupação; linha 2: quartos ocupados/disponíveis/bloqueados
        for linha_cartoes, nomes in enumerate([
                ["Taxa de ocupação", "Faturamento", "Reservas no período", "Ticket médio"],
                ["Quartos ocupados (média/dia)", "Quartos disponíveis (média/dia)",
                 "Quartos bloqueados (média/dia)"]]):
            for i, nome in enumerate(nomes):
                cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
                cartao = CartaoResumo(cartoes, nome, "—")
                cartao.grid(row=linha_cartoes, column=i, sticky="ew",
                            padx=(0 if i == 0 else 8, 0 if i == len(nomes) - 1 else 8),
                            pady=(0 if linha_cartoes == 0 else 12, 0))
                self.cartoes[nome] = cartao

        # o gráfico e a tabela por quarto dividem o mesmo espaço; um seletor escolhe qual ver
        seletor = ctk.CTkFrame(self.corpo, fg_color="transparent")
        seletor.pack(fill="x", pady=(16, 0))
        self.visao = CampoSelecao(seletor, "Relatório", list(VISOES), self._trocar_visao)
        self.visao.caixa.configure(width=280)
        self.visao.pack(anchor="w")
        area = ctk.CTkFrame(self.corpo, fg_color="transparent")
        area.pack(fill="both", expand=True, pady=(8, 0))
        grafico = Cartao(area, "Ocupação por dia")
        quartos = Cartao(area, "Ocupação por quarto")
        self._visoes = {"dia": grafico, "quarto": quartos}
        self.tabela_quartos = Tabela(quartos, [
            ("Quarto", "numero", 90), ("Tipo", "tipo", 120),
            ("Noites ocupadas", "ocupadas", 150), ("Noites bloqueadas", "bloqueadas", 160),
            ("Noites livres", "livres", 130), ("Ocupação", "ocupacao", 110),
            ("Receita", "receita", 140)], altura=230)
        self.tabela_quartos.pack(fill="both", expand=True, padx=10, pady=(6, 4))
        ctk.CTkLabel(quartos, anchor="w", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                     text="Ocupação = noites ocupadas ÷ noites não bloqueadas. "
                          "Receita = valor da reserva dividido pelas noites dela, "
                          "somando só as noites dentro do período."
                     ).pack(anchor="w", padx=14, pady=(0, 6))
        self.canvas = tk.Canvas(grafico, width=LARGURA_GRAFICO, height=ALTURA_GRAFICO,
                                bg=COR_CARTAO, highlightthickness=0)
        self.canvas.pack(padx=20, pady=(0, 6))
        self.lbl_legenda = ctk.CTkLabel(grafico, text="", font=fonte(12),
                                        text_color=COR_TEXTO_SUAVE, anchor="w")
        self.lbl_legenda.pack(anchor="w", padx=20, pady=(0, 14))

        self.visao.definir("Ocupação por dia")
        self._trocar_visao()

        hoje = date.today()
        self.atalho.definir(PERSONALIZADO)
        self.inicio.definir(formatar_data(hoje - timedelta(days=6)))
        self.fim.definir(formatar_data(hoje))

    def _trocar_visao(self):
        escolhida = VISOES[self.visao.valor()]
        for chave, quadro in self._visoes.items():
            if chave == escolhida:
                quadro.pack(fill="both", expand=True)
            else:
                quadro.pack_forget()

    def ao_exibir(self):
        self.gerar(silencioso=True)

    def _ao_digitar_periodo(self):
        self.atalho.definir(PERSONALIZADO)

    def _ao_escolher_atalho(self):
        atalho = self.atalho.valor()
        if atalho != PERSONALIZADO:
            inicio, fim = periodo_do_atalho(atalho)
            self.inicio.definir(formatar_data(inicio))
            self.fim.definir(formatar_data(fim))
            self.gerar()

    def gerar(self, silencioso=False):
        try:
            inicio, fim = ler_data(self.inicio.valor()), ler_data(self.fim.valor())
            # só as reservas que tocam o período vêm do banco (nada de carregar o histórico todo)
            reservas = self.servicos.reservas.listar_para_relatorio(inicio, fim)
            quartos = self.servicos.quartos.listar()
            # bloqueios do período: quarto bloqueado não conta como disponível naquele dia
            bloqueios = self.servicos.bloqueios.historico(periodo_de=inicio, periodo_ate=fim)
            resumo = relatorio_periodo(reservas, quartos, inicio, fim, bloqueios)
        except (ValueError, ErroNegocio) as erro:      # data inválida, fim < início, longo demais
            if not silencioso:
                messagebox.showwarning("Período inválido", str(erro))
            return

        self.cartoes["Taxa de ocupação"].atualizar(formatar_percentual(resumo["taxa_ocupacao"]))
        self.cartoes["Faturamento"].atualizar(formatar_moeda(resumo["faturamento"]))
        self.cartoes["Reservas no período"].atualizar(resumo["reservas"])
        self.cartoes["Ticket médio"].atualizar(formatar_moeda(resumo["ticket_medio"]))
        totais = resumo["totais"]
        self.cartoes["Quartos ocupados (média/dia)"].atualizar(f"{totais['media_ocupados']:.1f}")
        self.cartoes["Quartos disponíveis (média/dia)"].atualizar(
            f"{totais['media_disponiveis']:.1f}")
        self.cartoes["Quartos bloqueados (média/dia)"].atualizar(
            f"{totais['media_bloqueados']:.1f}")
        self.tabela_quartos.carregar(self.servicos.linhas_ocupacao_quartos(resumo))
        self.lbl_legenda.configure(text=LEGENDA_BARRAS[resumo["granularidade"]])
        self._desenhar(resumo["barras"], resumo["granularidade"])

    def _desenhar(self, barras, granularidade):
        c = self.canvas
        c.delete("all")
        esquerda, base, topo = 44, 28, 12
        altura_util = ALTURA_GRAFICO - base - topo
        fonte_eixo = (FONTE_FAMILIA, 9)

        for pct in (0, 25, 50, 75, 100):
            y = topo + altura_util * (1 - pct / 100)
            c.create_line(esquerda, y, LARGURA_GRAFICO, y, fill=COR_BORDA)
            c.create_text(esquerda - 8, y, text=f"{pct}%", anchor="e",
                          fill=COR_TEXTO_SUAVE, font=fonte_eixo)

        n = len(barras)
        if n == 0:
            return
        faixa = (LARGURA_GRAFICO - esquerda - 10) / n
        largura_barra = min(44, faixa * 0.6)
        passo_rotulo = max(1, math.ceil(LARGURA_ROTULO / faixa))   # pula rótulos que não cabem
        formato_rotulo = "%m/%y" if granularidade == GRANULARIDADE_MES else "%d/%m"

        for i, (dia, pct) in enumerate(barras):
            centro = esquerda + faixa * i + faixa / 2
            y = topo + altura_util * (1 - pct / 100)
            if pct > 0:
                c.create_rectangle(centro - largura_barra / 2, y, centro + largura_barra / 2,
                                   topo + altura_util, fill=AZUL, outline="")
                if faixa >= LARGURA_VALOR:
                    c.create_text(centro, y - 8, text=f"{pct:.0f}%", fill=COR_TEXTO, font=fonte_eixo)
            if i % passo_rotulo == 0:
                c.create_text(centro, ALTURA_GRAFICO - base / 2 + 2, text=dia.strftime(formato_rotulo),
                              fill=COR_TEXTO_SUAVE, font=fonte_eixo)
