from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.utils.constantes import SITUACOES_RESERVA
from src.utils.formatacao import formatar_cpf, formatar_data, formatar_moeda, formatar_telefone
from ui.componentes.campos import CampoSelecao
from ui.componentes.cartao import Cartao, CartaoResumo
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.seletor_hospede import CampoSeletorHospede
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO_SUAVE, fonte
from ui.telas.tela_base import TelaBase

TODAS = "Todas"
COLUNAS = [("Reserva", "reserva", 70), ("Quarto", "quarto", 130), ("Entrada", "entrada", 95),
           ("Saída", "saida", 95), ("Noites", "noites", 65), ("Total", "total", 105),
           ("Valor pago", "pago", 105), ("Situação", "situacao", 125)]
CARTOES = ["Hospedagens", "Noites hospedadas", "Quartos utilizados", "Total pago"]


class TelaHistoricoHospedagem(TelaBase):
    titulo = "Histórico de hospedagem"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        filtro = Cartao(self.corpo, "Hóspede")
        filtro.pack(fill="x")
        linha = ctk.CTkFrame(filtro, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=(0, 8))
        linha.grid_columnconfigure(0, weight=3)
        linha.grid_columnconfigure(1, weight=1)
        self.hospede = CampoSeletorHospede(linha, self.servicos, ao_mudar=self.consultar)
        self.situacao = CampoSelecao(linha, "Situação das reservas", [TODAS] + SITUACOES_RESERVA,
                                     self.consultar)
        self.hospede.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.situacao.grid(row=0, column=1, sticky="ew", padx=(10, 0))
        self.lbl_hospede = ctk.CTkLabel(filtro, text="", anchor="w", font=fonte(12),
                                        text_color=COR_TEXTO_SUAVE)
        self.lbl_hospede.pack(anchor="w", padx=20, pady=(0, 14))

        cartoes = ctk.CTkFrame(self.corpo, fg_color="transparent")
        cartoes.pack(fill="x", pady=(16, 0))
        self.cartoes = {}
        for i, nome in enumerate(CARTOES):
            cartoes.grid_columnconfigure(i, weight=1, uniform="resumo")
            cartao = CartaoResumo(cartoes, nome, "—")
            cartao.grid(row=0, column=i, sticky="ew",
                        padx=(0 if i == 0 else 8, 0 if i == len(CARTOES) - 1 else 8))
            self.cartoes[nome] = cartao

        lista = Cartao(self.corpo, "Reservas do hóspede")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        self.lbl_resumo = ctk.CTkLabel(lista, text="", anchor="w", justify="left",
                                       font=fonte(12), text_color=COR_TEXTO_SUAVE,
                                       wraplength=860)
        self.lbl_resumo.pack(side="bottom", anchor="w", padx=20, pady=(0, 14))
        self.tabela = Tabela(lista, COLUNAS, altura=200,
                             ao_duplo_clique=lambda linha: abrir_detalhes(
                                 self, self.servicos, linha["id"]))
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        self.situacao.definir(TODAS)
        self._limpar()

    def ao_exibir(self):
        # o hóspede escolhido pode ter sido editado ou excluído, e há reservas novas
        self.hospede.atualizar()
        self.consultar()

    def _limpar(self):
        for cartao in self.cartoes.values():
            cartao.atualizar("—")
        self.lbl_hospede.configure(text="Escolha um hóspede para ver o histórico dele.")
        self.lbl_resumo.configure(text="Dê um duplo clique em uma reserva para ver os detalhes.")
        self.tabela.carregar([])

    def consultar(self):
        hospede_id = self.hospede.valor()
        if hospede_id is None:
            self._limpar()
            return
        filtro = self.situacao.valor()
        try:
            historico = self.servicos.historico_hospedagem.historico(
                hospede_id, "" if filtro in ("", TODAS) else filtro)
        except ErroNegocio as erro:
            messagebox.showwarning("Histórico de hospedagem", str(erro))
            self._limpar()
            return

        h, r = historico.hospede, historico.resumo
        contato = " · ".join(t for t in (formatar_cpf(h.cpf), formatar_telefone(h.telefone),
                                         h.email) if t)
        self.lbl_hospede.configure(text=f"{h.nome}  ·  {contato}")
        self.cartoes["Hospedagens"].atualizar(r["hospedagens"])
        self.cartoes["Noites hospedadas"].atualizar(r["noites"])
        self.cartoes["Quartos utilizados"].atualizar(len(r["quartos_utilizados"]))
        self.cartoes["Total pago"].atualizar(formatar_moeda(r["total_pago"]))
        self.tabela.carregar(self.servicos.linhas_historico_hospedagem(historico.itens))

        partes = [f"Quartos utilizados: {', '.join(r['quartos_utilizados']) or '—'}"]
        if r["ultima_hospedagem"]:
            partes.append(f"Última hospedagem: {formatar_data(r['ultima_hospedagem'])}")
        partes.append(f"{r['reservas']} reserva(s) no total: {r['futuras']} futura(s), "
                      f"{r['canceladas']} cancelada(s), {r['no_shows']} sem comparecimento")
        self.lbl_resumo.configure(
            text="  ·  ".join(partes) + ". Os números dos cartões são do histórico completo; "
                                        "duplo clique em uma reserva mostra os detalhes.")
