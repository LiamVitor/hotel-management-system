from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk

from src.services import inicio_regras as regras
from src.services.erros import ErroNegocio
from src.utils.constantes import (ALERTA_CAIXA_SEM_SALDO, ALERTA_CHECKIN_ATRASADO,
                                  ALERTA_CHECKOUT_ATRASADO, ALERTA_CONTAS_VENCIDAS,
                                  ALERTA_QUARTOS_INDISPONIVEIS, DIAS_OCUPACAO_INICIO,
                                  SITUACOES_QUARTO)
from src.utils.formatacao import (formatar_data_extenso, formatar_moeda, formatar_percentual)
from src.utils.sessao import Sessao
from ui.componentes.barra_proporcional import BarraProporcional
from ui.componentes.botoes import botao_primario, botao_secundario
from ui.componentes.cartao import Cartao
from ui.componentes.cartao_indicador import CartaoIndicador
from ui.componentes.grafico_barras import GraficoBarras
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.lista_alertas import ListaAlertas
from ui.componentes.tabela import Tabela
from ui.estilos import (COR_SITUACAO_QUARTO, COR_TEXTO, COR_TEXTO_SUAVE, TAMANHO_INDICADOR,
                        VERMELHO, estilo_badge_status, fonte)
from ui.telas.tela_base import TelaBase

ESPACO = 6      # metade do espaço entre dois cartões
LARGURA_QUATRO_COLUNAS = 800    # abaixo disso, os cartões passam a ser 2 por linha
LARGURA_FAIXA_COMPACTA = 800    # abaixo disso, os atalhos descem para baixo da saudação

COLUNAS_RESERVAS = [("Hóspede", "hospede", 230), ("Quarto", "quarto", 70),
                    ("Entrada", "entrada", 100), ("Saída", "saida", 100),
                    ("Pagamento", "pagamento", 110), ("Status", "situacao", 120)]
COLUNAS_CONTAS = [("Reserva", "reserva", 80), ("Hóspede", "hospede", 230),
                  ("Saldo", "saldo", 110), ("Vencimento", "vencimento", 110),
                  ("Situação", "situacao", 160)]

# para onde cada alerta leva a pessoa (nome da tela no menu lateral)
DESTINO_ALERTA = {
    ALERTA_CHECKIN_ATRASADO: "Reservas",          # lá estão o check-in e o "Marcar no-show"
    ALERTA_CHECKOUT_ATRASADO: "Check-in / Check-out",
    ALERTA_CONTAS_VENCIDAS: "Relatórios",
    ALERTA_CAIXA_SEM_SALDO: "Caixa",
    ALERTA_QUARTOS_INDISPONIVEIS: "Quartos",
}


class TelaInicio(TelaBase):
    """Painel do dia: números da operação, pendências, reservas de hoje e (para quem pode) o financeiro."""

    titulo = "Início"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self._navegar = None
        # A página é mais alta que a área útil de notebooks: a rolagem fica só no conteúdo.
        self.conteudo = ctk.CTkScrollableFrame(self.corpo, fg_color="transparent", corner_radius=0)
        self.conteudo.pack(fill="both", expand=True)

        self._montar_boas_vindas()
        self.cartoes = self._linha_de_cartoes([
            ("ocupacao", "Ocupação agora", "Quartos"),
            ("checkins", "Check-ins hoje", "Check-in / Check-out"),
            ("checkouts", "Check-outs hoje", "Check-in / Check-out"),
            ("livres", "Quartos disponíveis", "Quartos")])
        self.alertas = ListaAlertas(self.conteudo)
        self.alertas.pack(fill="x", pady=(16, 0))
        self._montar_reservas()
        self._montar_ocupacao_e_quartos()
        self.cartoes_financeiro = {}
        self.tabela_contas = None
        if Sessao.pode("caixa.ver") or Sessao.pode("relatorios.ver"):
            self._montar_financeiro()

    def definir_navegacao(self, navegar):
        """Recebe a função que troca de tela (o App entrega depois de criar todas as telas)."""
        self._navegar = navegar

    def _ir(self, nome):
        if self._navegar and nome:
            self._navegar(nome)

    # ---------- montagem ----------
    def _montar_boas_vindas(self):
        self.faixa = Cartao(self.conteudo)
        self.faixa.pack(fill="x")
        self.faixa.grid_columnconfigure(0, weight=1)
        textos = ctk.CTkFrame(self.faixa, fg_color="transparent")
        textos.grid(row=0, column=0, sticky="w", padx=20, pady=16)
        self.lbl_saudacao = ctk.CTkLabel(textos, text="", font=fonte(20, True),
                                         text_color=COR_TEXTO, anchor="w")
        self.lbl_saudacao.pack(anchor="w")
        self.lbl_data = ctk.CTkLabel(textos, text="", font=fonte(13),
                                     text_color=COR_TEXTO_SUAVE, anchor="w")
        self.lbl_data.pack(anchor="w", pady=(2, 0))

        self.acoes = ctk.CTkFrame(self.faixa, fg_color="transparent")
        self.acoes.grid(row=0, column=1, sticky="e", padx=(0, 12))
        atalhos = [("Nova reserva", "reservas.criar", "Reservas", botao_primario),
                   ("Check-in / Check-out", "reservas.checkin", "Check-in / Check-out",
                    botao_secundario),
                   ("Hóspedes", "hospedes.ver", "Hóspedes", botao_secundario)]
        for texto, permissao, destino, criar in atalhos:
            if Sessao.pode(permissao):
                criar(self.acoes, texto, lambda d=destino: self._ir(d), 150
                      ).pack(side="left", padx=(0, 8))
        self._faixa_compacta = False
        self.faixa.bind("<Configure>", self._ajustar_faixa)

    def _ajustar_faixa(self, evento):
        """Em janela estreita os atalhos descem para a linha de baixo, em vez de serem cortados."""
        compacta = evento.width < LARGURA_FAIXA_COMPACTA
        if compacta == self._faixa_compacta:
            return
        self._faixa_compacta = compacta
        if compacta:
            self.acoes.grid(row=1, column=0, columnspan=2, sticky="w", padx=(20, 12), pady=(0, 12))
        else:
            self.acoes.grid(row=0, column=1, columnspan=1, sticky="e", padx=(0, 12), pady=0)

    def _linha_de_cartoes(self, definicoes, tamanho_valor=28):
        """Fileira de CartaoIndicador de mesmo tamanho; devolve {chave: cartão}.

        Em janela estreita a fileira vira duas colunas, para o texto dos cartões não ser cortado.
        """
        quadro = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        quadro.pack(fill="x", pady=(16, 0))
        cartoes = {}
        for chave, titulo, destino in definicoes:
            cartoes[chave] = CartaoIndicador(quadro, titulo, lambda d=destino: self._ir(d),
                                             tamanho_valor)
        quadro._colunas_atuais = 0
        quadro.bind("<Configure>", lambda e, q=quadro, c=list(cartoes.values()):
                    self._distribuir(q, c, e.width))
        self._distribuir(quadro, list(cartoes.values()), LARGURA_QUATRO_COLUNAS)
        return cartoes

    def _distribuir(self, quadro, cartoes, largura):
        """Põe os cartões em uma linha (janela larga) ou em duas colunas (janela estreita)."""
        colunas = len(cartoes) if largura >= LARGURA_QUATRO_COLUNAS else 2
        if colunas == quadro._colunas_atuais:
            return
        quadro._colunas_atuais = colunas
        for coluna in range(len(cartoes)):
            usada = coluna < colunas
            quadro.grid_columnconfigure(coluna, weight=1 if usada else 0,
                                        uniform="indicador" if usada else "")
        for posicao, cartao in enumerate(cartoes):
            linha, coluna = divmod(posicao, colunas)
            cartao.grid(row=linha, column=coluna, sticky="ew",
                        padx=(0 if coluna == 0 else ESPACO, 0 if coluna == colunas - 1 else ESPACO),
                        pady=(0 if linha == 0 else 12, 0))

    def _montar_reservas(self):
        quadro = Cartao(self.conteudo, "Reservas de hoje")
        quadro.pack(fill="x", pady=(16, 0))
        self.tabela = Tabela(
            quadro, COLUNAS_RESERVAS, altura=190,
            ao_duplo_clique=lambda linha: abrir_detalhes(self, self.servicos, linha["id"]),
            badges={"pagamento": estilo_badge_status, "situacao": estilo_badge_status})
        self.tabela.pack(fill="x", padx=20, pady=(0, 6))
        self.lbl_reservas = ctk.CTkLabel(quadro, text="", font=fonte(12),
                                         text_color=COR_TEXTO_SUAVE, anchor="w")
        self.lbl_reservas.pack(anchor="w", padx=20, pady=(0, 14))

    def _montar_ocupacao_e_quartos(self):
        meio = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        meio.pack(fill="x", pady=(16, 0))
        meio.grid_columnconfigure(0, weight=3, uniform="meio")
        meio.grid_columnconfigure(1, weight=2, uniform="meio")

        previsao = Cartao(meio, f"Ocupação prevista · próximos {DIAS_OCUPACAO_INICIO} dias")
        previsao.grid(row=0, column=0, sticky="nsew", padx=(0, ESPACO))
        self.grafico = GraficoBarras(previsao)
        self.grafico.pack(fill="both", expand=True, padx=20, pady=(0, 4))
        ctk.CTkLabel(previsao, text="Reservas confirmadas e hospedagens, descontando bloqueios.",
                     font=fonte(12), text_color=COR_TEXTO_SUAVE, anchor="w", wraplength=420
                     ).pack(anchor="w", padx=20, pady=(0, 14))

        quartos = Cartao(meio, "Situação dos quartos")
        quartos.grid(row=0, column=1, sticky="nsew", padx=(ESPACO, 0))
        self.barra_quartos = BarraProporcional(quartos)
        self.barra_quartos.pack(fill="x", padx=20, pady=(0, 20))

    def _montar_financeiro(self):
        ctk.CTkLabel(self.conteudo, text="Financeiro", font=fonte(16, True), text_color=COR_TEXTO,
                     anchor="w").pack(anchor="w", pady=(24, 0))
        definicoes = []
        if Sessao.pode("caixa.ver"):
            definicoes += [("saldo", "Saldo do caixa", "Caixa"),
                           ("entradas", "Entradas no mês", "Caixa"),
                           ("saidas", "Saídas no mês", "Caixa")]
        if Sessao.pode("relatorios.ver"):
            definicoes.append(("a_receber", "A receber", "Relatórios"))
        self.cartoes_financeiro = self._linha_de_cartoes(definicoes, TAMANHO_INDICADOR)

        if Sessao.pode("relatorios.ver"):
            quadro = Cartao(self.conteudo, "Contas a receber em aberto")
            quadro.pack(fill="x", pady=(16, 0))
            self.tabela_contas = Tabela(
                quadro, COLUNAS_CONTAS, altura=150,
                ao_duplo_clique=lambda linha: abrir_detalhes(self, self.servicos, linha["id"]),
                badges={"situacao": estilo_badge_status})
            self.tabela_contas.pack(fill="x", padx=20, pady=(0, 6))
            self.lbl_contas = ctk.CTkLabel(quadro, text="", font=fonte(12),
                                           text_color=COR_TEXTO_SUAVE, anchor="w")
            self.lbl_contas.pack(anchor="w", padx=20, pady=(0, 14))

    # ---------- dados ----------
    def ao_exibir(self):
        try:
            resumo = self.servicos.inicio.resumo()
        except ErroNegocio as erro:
            messagebox.showwarning("Início", str(erro))
            return
        self._mostrar_boas_vindas(resumo)
        self._mostrar_indicadores(resumo.indicadores)
        self.alertas.carregar(resumo.alertas, self._abrir_alerta)
        self._mostrar_reservas(resumo.reservas_hoje)
        self.grafico.carregar(resumo.ocupacao_prevista, destaque=resumo.hoje)
        self.barra_quartos.carregar([(s, resumo.situacao_quartos.get(s, 0), COR_SITUACAO_QUARTO[s])
                                     for s in SITUACOES_QUARTO])
        if resumo.financeiro is not None and self.cartoes_financeiro:
            self._mostrar_financeiro(resumo.financeiro)

    def _abrir_alerta(self, alerta):
        self._ir(DESTINO_ALERTA.get(alerta.tipo))

    def _mostrar_boas_vindas(self, resumo):
        usuario = Sessao.usuario
        primeiro_nome = usuario.nome.split()[0] if usuario and usuario.nome.strip() else ""
        saudacao = regras.saudacao(datetime.now())
        self.lbl_saudacao.configure(text=f"{saudacao}, {primeiro_nome}" if primeiro_nome else saudacao)
        self.lbl_data.configure(text=formatar_data_extenso(resumo.hoje))

    def _mostrar_indicadores(self, i):
        operacionais = i.total_quartos - i.em_manutencao
        self.cartoes["ocupacao"].atualizar(
            formatar_percentual(i.taxa_ocupacao), f"{i.ocupados} de {operacionais} quartos em uso")
        self.cartoes["checkins"].atualizar(
            f"{i.chegadas_feitas}/{i.chegadas_previstas}",
            regras.texto_movimento(i.chegadas_previstas, i.chegadas_feitas))
        self.cartoes["checkouts"].atualizar(
            f"{i.saidas_feitas}/{i.saidas_previstas}",
            regras.texto_movimento(i.saidas_previstas, i.saidas_feitas))
        self.cartoes["livres"].atualizar(i.livres, regras.texto_quartos(i))

    def _mostrar_reservas(self, reservas):
        self.tabela.carregar(self.servicos.linhas_reservas(reservas))
        total = len(reservas)
        self.lbl_reservas.configure(
            text="Nenhuma reserva movimenta o dia." if not total else
            f"{total} reserva{'s' if total != 1 else ''} · duplo clique para ver os detalhes.")

    def _mostrar_financeiro(self, financeiro):
        caixa, totais = financeiro.caixa, financeiro.totais_contas
        if caixa is not None:
            self.cartoes_financeiro["saldo"].atualizar(
                formatar_moeda(caixa.saldo_final),
                f"Início do mês: {formatar_moeda(caixa.saldo_inicial)}")
            self.cartoes_financeiro["entradas"].atualizar(
                formatar_moeda(caixa.entradas), "Pagamentos recebidos")
            self.cartoes_financeiro["saidas"].atualizar(
                formatar_moeda(caixa.saidas), "Despesas e reembolsos")
        if totais is not None:
            vencido = totais["total_vencido"]
            self.cartoes_financeiro["a_receber"].atualizar(
                formatar_moeda(totais["total_a_receber"]),
                f"{formatar_moeda(vencido)} vencido" if vencido else "Nada vencido",
                cor_detalhe=VERMELHO if vencido else COR_TEXTO_SUAVE)
            self.tabela_contas.carregar(
                self.servicos.linhas_contas_receber(financeiro.contas_abertas))
            exibidas, em_aberto = len(financeiro.contas_abertas), totais["qtd_em_aberto"]
            self.lbl_contas.configure(
                text="Nenhuma conta em aberto." if not em_aberto else
                f"Mostrando as {exibidas} mais antigas de {em_aberto} em aberto · "
                "o relatório completo está em Relatórios.")
