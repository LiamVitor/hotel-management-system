"""Detalhes da reserva: o que estava previsto ao lado do que realmente aconteceu."""
import customtkinter as ctk

from src.services import reserva_regras as regras
from src.utils.constantes import (RESERVA_CANCELADA, RESERVA_CONFIRMADA, RESERVA_FINALIZADA,
                                  RESERVA_HOSPEDADA)
from src.utils.formatacao import formatar_data
from ui.componentes.botoes import botao_secundario
from ui.componentes.cartao import Cartao
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, fonte

COR_SITUACAO = {RESERVA_CONFIRMADA: "#2563EB", RESERVA_HOSPEDADA: VERDE,
                RESERVA_FINALIZADA: "#6B7280", RESERVA_CANCELADA: "#DC2626"}


def abrir_detalhes(master, servicos, reserva_id):
    janela = JanelaDetalhesReserva(master, servicos, reserva_id)
    master.wait_window(janela)


def texto_evento(quando, nome):
    """'08/11/2026 às 14:32' e, se houver, 'por Nome' na linha de baixo."""
    base = f"{quando:%d/%m/%Y} às {quando:%H:%M}"
    return f"{base}\npor {nome}" if nome else base


def descrever_diferenca(dias, evento):
    """Frase curta sobre a diferença entre o dia real e o previsto (dias = real - previsto)."""
    if dias == 0:
        return f"{evento} no dia previsto."
    unidade = "dia" if abs(dias) == 1 else "dias"
    return f"{evento} {abs(dias)} {unidade} {'depois' if dias > 0 else 'antes'} do previsto."


class JanelaDetalhesReserva(ctk.CTkToplevel):
    LARGURA, ALTURA = 780, 480

    def __init__(self, master, servicos, reserva_id):
        super().__init__(master, fg_color=COR_FUNDO)
        self.reserva = servicos.reservas.buscar_por_id(reserva_id)
        self.servicos = servicos
        self.nomes = servicos.reservas.responsaveis([self.reserva])

        self.title(f"Detalhes da reserva {reserva_id:04d}")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        self._montar_cabecalho()
        self._montar_rodape()
        self._montar_colunas()
        self.bind("<Escape>", lambda _e: self.destroy())
        # no Windows, o foco e o bloqueio da janela de trás só funcionam depois que ela aparece
        self.after(150, self._ativar)

    def _centralizar(self, master):
        topo = master.winfo_toplevel()
        altura = min(self.ALTURA, topo.winfo_screenheight() - 100)
        x = topo.winfo_rootx() + max((topo.winfo_width() - self.LARGURA) // 2, 0)
        y = topo.winfo_rooty() + max((topo.winfo_height() - altura) // 2, 0)
        self.geometry(f"{self.LARGURA}x{altura}+{x}+{y}")

    # ---------- montagem ----------
    def _montar_cabecalho(self):
        r = self.reserva
        hospede = self.servicos.hospedes.buscar_por_id(r.hospede_id)
        quarto = self.servicos.quartos.buscar_por_id(r.quarto_id)
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=24, pady=(20, 12))
        textos = ctk.CTkFrame(cabecalho, fg_color="transparent")
        textos.pack(side="left")
        ctk.CTkLabel(textos, text=f"Reserva {r.id:04d}", font=fonte(18, True),
                     text_color=COR_TEXTO).pack(anchor="w")
        ctk.CTkLabel(textos, text=f"{hospede.nome if hospede else '—'}  ·  Quarto "
                                  f"{quarto.numero if quarto else '—'}", font=fonte(13),
                     text_color=COR_TEXTO_SUAVE).pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(cabecalho, text=r.situacao, width=100, height=28, corner_radius=14,
                     font=fonte(12, True), text_color="white",
                     fg_color=COR_SITUACAO.get(r.situacao, "#6B7280")).pack(side="right")

    def _montar_rodape(self):
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")

    def _montar_colunas(self):
        r = self.reserva
        colunas = ctk.CTkFrame(self, fg_color="transparent")
        colunas.pack(fill="x", padx=24)
        colunas.grid_columnconfigure((0, 1), weight=1, uniform="col")

        previsto = Cartao(colunas, "Previsto na reserva")
        previsto.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._linha(previsto, "Entrada", formatar_data(r.data_entrada))
        self._linha(previsto, "Saída", formatar_data(r.data_saida))
        self._linha(previsto, "Diárias previstas", str(regras.calcular_diarias(r.data_entrada, r.data_saida)))
        ctk.CTkFrame(previsto, fg_color="transparent", height=10).pack()

        real = Cartao(colunas, "Real (o que aconteceu)")
        real.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self._linha(real, "Check-in", self._evento(r.checkin_em, r.checkin_por, self._sem_checkin()))
        self._linha(real, "Check-out", self._evento(r.checkout_em, r.checkout_por, self._sem_checkout()))
        noites = regras.noites_reais(r)
        self._linha(real, "Noites reais", "—" if noites is None else str(noites))
        ctk.CTkFrame(real, fg_color="transparent", height=10).pack()

        notas = Cartao(self, "Previsto x real")
        notas.pack(fill="x", padx=24, pady=(12, 0))
        frases = self._frases()
        for frase in frases or ["Ainda não há check-in ou check-out registrado para comparar."]:
            ctk.CTkLabel(notas, text="•  " + frase, font=fonte(13), text_color=COR_TEXTO,
                         anchor="w", justify="left", wraplength=self.LARGURA - 90
                         ).pack(anchor="w", padx=20, pady=2)
        ctk.CTkFrame(notas, fg_color="transparent", height=10).pack()

    @staticmethod
    def _linha(cartao, rotulo, valor):
        linha = ctk.CTkFrame(cartao, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(linha, text=rotulo, font=fonte(12), text_color=COR_TEXTO_SUAVE,
                     width=110, anchor="nw").pack(side="left", anchor="n")
        ctk.CTkLabel(linha, text=valor, font=fonte(13, True), text_color=COR_TEXTO,
                     anchor="w", justify="left").pack(side="left")

    # ---------- textos ----------
    def _sem_checkin(self):
        situacao = self.reserva.situacao
        if situacao == RESERVA_CONFIRMADA:
            return "Ainda não realizado"
        if situacao == RESERVA_CANCELADA:
            return "—"
        return "Não registrado\n(reserva anterior ao registro de horários)"

    def _sem_checkout(self):
        situacao = self.reserva.situacao
        if situacao in (RESERVA_CONFIRMADA, RESERVA_HOSPEDADA):
            return "Ainda não realizado"
        if situacao == RESERVA_CANCELADA:
            return "—"
        return "Não registrado\n(reserva anterior ao registro de horários)"

    def _evento(self, quando, usuario_id, texto_vazio):
        if quando is None:
            return texto_vazio
        return texto_evento(quando, self.nomes.get(usuario_id))

    def _frases(self):
        r = self.reserva
        frases = []
        entrada = regras.dias_de_diferenca_entrada(r)
        saida = regras.dias_de_diferenca_saida(r)
        if entrada is not None:
            frases.append(descrever_diferenca(entrada, "Entrada"))
        if saida is not None:
            frases.append(descrever_diferenca(saida, "Saída"))
        return frases

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
