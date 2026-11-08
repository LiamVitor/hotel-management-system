from datetime import date
from tkinter import messagebox

from src.services.erros import ErroNegocio
from ui.componentes.cartao import Cartao
from ui.componentes.janela_pagamentos import abrir_pagamentos
from ui.componentes.tabela import Tabela
from ui.telas.tela_base import TelaBase
from src.utils.constantes import RESERVA_CONFIRMADA, RESERVA_HOSPEDADA
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao

COLUNAS_CHECKIN = [("Hóspede", "hospede", 230), ("Quarto", "quarto", 80),
                   ("Entrada", "entrada", 110), ("Saída", "saida", 110), ("Status", "situacao", 110)]
COLUNAS_CHECKOUT = [("Hóspede", "hospede", 230), ("Quarto", "quarto", 80),
                    ("Entrada", "entrada", 110), ("Saída", "saida", 110),
                    ("Saldo a pagar", "saldo", 120)]


class TelaCheckinCheckout(TelaBase):
    titulo = "Check-in / Check-out"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

        cartao_in = Cartao(self.corpo, "Check-ins previstos para hoje")
        cartao_in.pack(fill="both", expand=True)
        self.tabela_in = Tabela(cartao_in, COLUNAS_CHECKIN, altura=170,
                                acao=("Fazer check-in", self.fazer_checkin))
        self.tabela_in.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        cartao_out = Cartao(self.corpo, "Hóspedes hospedados")
        cartao_out.pack(fill="both", expand=True, pady=(16, 0))
        self.tabela_out = Tabela(cartao_out, COLUNAS_CHECKOUT, altura=170,
                                 acao=("Fazer check-out", self.fazer_checkout))
        self.tabela_out.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def ao_exibir(self):
        self.atualizar_tabelas()

    def atualizar_tabelas(self):
        hoje = date.today()
        reservas = self.servicos.reservas.listar()
        previstos = [r for r in reservas
                     if r.situacao == RESERVA_CONFIRMADA and r.data_entrada == hoje]
        hospedados = [r for r in reservas if r.situacao == RESERVA_HOSPEDADA]
        self.tabela_in.carregar(self.servicos.linhas_reservas(previstos))
        self.tabela_out.carregar(self.servicos.linhas_reservas(hospedados))

    def fazer_checkin(self, linha):
        pergunta = f"Fazer check-in de {linha['hospede']} no quarto {linha['quarto']}?"
        if not messagebox.askyesno("Check-in", pergunta):
            return
        try:
            self.servicos.reservas.fazer_checkin(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Check-in", str(erro))
            return
        self.atualizar_tabelas()

    def fazer_checkout(self, linha):
        reserva = self.servicos.reservas.buscar_por_id(linha["id"])
        if reserva is None:
            return
        resumo = self.servicos.pagamentos.resumo(reserva.id)
        if resumo.saldo > 0 and Sessao.pode("pagamentos.registrar"):
            resposta = messagebox.askyesnocancel(
                "Saldo pendente",
                f"{linha['hospede']} ainda tem {formatar_moeda(resumo.saldo)} a pagar.\n\n"
                "Sim: registrar o pagamento agora\n"
                "Não: fazer o check-out com o saldo pendente\n"
                "Cancelar: voltar")
            if resposta is None:
                return
            if resposta:
                abrir_pagamentos(self, self.servicos, reserva.id, self.atualizar_tabelas)
                resumo = self.servicos.pagamentos.resumo(reserva.id)
        pergunta = (f"Fazer check-out de {linha['hospede']}?\n"
                    f"Total: {formatar_moeda(resumo.valor_total)}    "
                    f"Pago: {formatar_moeda(resumo.total_pago)}\n"
                    f"Saldo pendente: {formatar_moeda(resumo.saldo)}")
        if not messagebox.askyesno("Check-out", pergunta):
            return
        try:
            self.servicos.reservas.fazer_checkout(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Check-out", str(erro))
            return
        self.atualizar_tabelas()
