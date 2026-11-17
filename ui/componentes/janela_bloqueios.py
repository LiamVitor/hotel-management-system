"""Janela de bloqueios de quartos: registrar um bloqueio e consultar o histórico."""
from datetime import date, datetime
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import MOTIVO_BLOQUEIO_MAX
from src.utils.formatacao import formatar_data_hora, ler_hora, mascara_hora
from src.utils.sessao import Sessao
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import COR_FUNDO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte

COLUNAS = [("Quarto", "quarto", 55), ("Início", "inicio", 115), ("Término", "fim", 115),
           ("Situação", "situacao", 95), ("Motivo", "motivo", 190),
           ("Responsável", "responsavel", 115), ("Registrado em", "registrado_em", 115)]

DICA_DETALHE = "Clique em um bloqueio para ver o motivo completo."


def abrir_bloqueios(master, servicos, quarto_id=None):
    """Abre a janela e espera ela ser fechada.

    quarto_id: com um quarto, mostra o histórico dele e (para quem pode) o formulário de
    novo bloqueio; sem quarto, mostra o histórico de todos os quartos, só para consulta.
    """
    janela = JanelaBloqueios(master, servicos, quarto_id)
    master.wait_window(janela)


class JanelaBloqueios(ctk.CTkToplevel):
    LARGURA = 1000

    def __init__(self, master, servicos, quarto_id=None):
        super().__init__(master, fg_color=COR_FUNDO)
        self.servicos = servicos
        self.quarto_id = quarto_id
        self.quarto = servicos.quartos.buscar_por_id(quarto_id) if quarto_id else None
        self.com_formulario = self.quarto is not None and Sessao.pode("bloqueios.gerenciar")
        self.ALTURA = 760 if self.com_formulario else 560

        self.title(f"Bloqueios do quarto {self.quarto.numero}" if self.quarto
                   else "Histórico de bloqueios")
        self.resizable(False, False)
        self._centralizar(master)
        self.transient(master.winfo_toplevel())

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(side="bottom", fill="x", padx=24, pady=(8, 20))
        botao_secundario(rodape, "Fechar", self.destroy, 120).pack(side="right")

        self._montar_cabecalho()
        if self.com_formulario:
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
        cabecalho = ctk.CTkFrame(self, fg_color="transparent")
        cabecalho.pack(fill="x", padx=24, pady=(20, 12))
        if self.quarto:
            titulo = f"Bloqueios do quarto {self.quarto.numero}"
            detalhe = (f"{self.quarto.tipo}  ·  capacidade {self.quarto.capacidade}  ·  "
                       "período em que o quarto fica indisponível (manutenção, reforma...)")
        else:
            titulo = "Histórico de bloqueios"
            detalhe = "Todos os quartos, do bloqueio mais recente para o mais antigo."
        ctk.CTkLabel(cabecalho, text=titulo, font=fonte(18, True), text_color=COR_TEXTO
                     ).pack(anchor="w")
        ctk.CTkLabel(cabecalho, text=detalhe, font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w", pady=(2, 0))

    def _montar_formulario(self):
        form = Cartao(self, "Registrar bloqueio")
        form.pack(fill="x", padx=24)
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        for coluna, peso in enumerate((3, 2, 3, 2)):
            grade.grid_columnconfigure(coluna, weight=peso)
        hoje = lambda: date.today()
        self.data_inicio = CampoData(grade, "Início — data", data_minima=hoje)
        self.hora_inicio = CampoTexto(grade, "Início — hora", "08:00", mascara=mascara_hora)
        self.data_fim = CampoData(grade, "Término — data", data_minima=hoje)
        self.hora_fim = CampoTexto(grade, "Término — hora", "18:00", mascara=mascara_hora)
        self.data_inicio.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.hora_inicio.grid(row=0, column=1, sticky="ew", padx=8)
        self.data_fim.grid(row=0, column=2, sticky="ew", padx=8)
        self.hora_fim.grid(row=0, column=3, sticky="ew", padx=(8, 0))
        self.motivo = CampoTexto(grade, "Motivo (obrigatório)",
                                 "Ex.: reforma do banheiro, troca do ar-condicionado, dedetização")
        self.motivo.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(fill="x", padx=20, pady=(14, 0))
        botao_primario(botoes, "Registrar bloqueio", self._registrar, 180).pack(side="left")
        botao_secundario(botoes, "Limpar", self._limpar_formulario, 120).pack(side="left", padx=10)
        self.lbl_form = ctk.CTkLabel(
            form, font=fonte(12, True), text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
            wraplength=self.LARGURA - 100,
            text=(f"O motivo pode ter até {MOTIVO_BLOQUEIO_MAX} caracteres. O bloqueio impede novas "
                  "reservas no período e fica no histórico com a data, a hora e o seu usuário."))
        self.lbl_form.pack(anchor="w", padx=20, pady=(8, 14))

    def _montar_historico(self):
        historico = Cartao(self, "Histórico de bloqueios")
        historico.pack(fill="both", expand=True, padx=24, pady=(14, 0))
        # o texto de detalhe é empacotado antes, embaixo, para nunca ser espremido pela tabela
        self.lbl_detalhe = ctk.CTkLabel(historico, text=DICA_DETALHE, font=fonte(12),
                                        text_color=COR_TEXTO_SUAVE, anchor="w", justify="left",
                                        wraplength=self.LARGURA - 100)
        self.lbl_detalhe.pack(side="bottom", anchor="w", padx=20, pady=(0, 12))
        self.tabela = Tabela(historico, COLUNAS, altura=110, ao_selecionar=self._mostrar_detalhe)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 6))

    # ---------- estado ----------
    def _atualizar(self):
        bloqueios = self.servicos.bloqueios.historico(self.quarto_id)
        self.tabela.carregar(self.servicos.linhas_bloqueios(bloqueios))
        self.lbl_detalhe.configure(text=DICA_DETALHE if bloqueios
                                   else "Nenhum bloqueio registrado ainda.")

    def _mostrar_detalhe(self, linha):
        self.lbl_detalhe.configure(
            text=f"Motivo: {linha['motivo']}\n"
                 f"Registrado por {linha['responsavel']} em {linha['registrado_em']}.")

    def _mensagem(self, texto, cor):
        self.lbl_form.configure(text=texto, text_color=cor)

    # ---------- ações ----------
    @staticmethod
    def _ler_data_hora(campo_data, campo_hora, nome):
        data = campo_data.data()
        if data is None:
            raise ErroNegocio(f"Informe a data de {nome}.")
        try:
            hora = ler_hora(campo_hora.valor())
        except ValueError:
            raise ErroNegocio(f"Informe a hora de {nome} no formato hh:mm.")
        return datetime.combine(data, hora)

    def _registrar(self):
        try:
            inicio = self._ler_data_hora(self.data_inicio, self.hora_inicio, "início")
            fim = self._ler_data_hora(self.data_fim, self.hora_fim, "término")
        except ErroNegocio as erro:
            self._mensagem(str(erro), VERMELHO)
            return
        motivo = self.motivo.valor()
        confirmar = messagebox.askyesno(
            "Confirmar bloqueio",
            f"Bloquear o quarto {self.quarto.numero} de {formatar_data_hora(inicio)} "
            f"a {formatar_data_hora(fim)}?\n\nMotivo: {motivo}\n\n"
            "O quarto ficará indisponível para novas reservas nesse período, e o registro "
            "permanece no histórico.", parent=self)
        if not confirmar:
            return
        try:
            self.servicos.bloqueios.registrar(self.quarto_id, inicio, fim, motivo)
        except ErroNegocio as erro:         # ErroPermissao também cai aqui (é uma ErroNegocio)
            self._mensagem(str(erro), VERMELHO)
            return
        self._limpar_formulario()
        self._atualizar()
        self._mensagem("Bloqueio registrado.", VERDE)

    def _limpar_formulario(self):
        for campo in (self.data_inicio, self.hora_inicio, self.data_fim, self.hora_fim,
                      self.motivo):
            campo.limpar()

    def _ativar(self):
        if not self.winfo_exists():
            return
        self.lift()
        self.grab_set()
