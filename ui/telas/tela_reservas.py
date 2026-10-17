from datetime import date, timedelta
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.services.reserva_regras import (calcular_diarias, calcular_total, pode_cancelar,
                                         validar_capacidade, validar_periodo)
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campos import CampoSelecao, CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.tabela import Tabela
from ui.estilos import AZUL, COR_TEXTO, COR_TEXTO_SUAVE, VERDE, VERMELHO, fonte
from ui.telas.tela_base import TelaBase
from src.utils.constantes import QUARTO_MANUTENCAO
from src.utils.formatacao import formatar_data, formatar_moeda, ler_data

COLUNAS = [("Código", "codigo", 70), ("Hóspede", "hospede", 210), ("Quarto", "quarto", 70),
           ("Entrada", "entrada", 100), ("Saída", "saida", 100), ("Total", "total", 120),
           ("Status", "situacao", 110)]


class TelaReservas(TelaBase):
    titulo = "Reservas"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        self._hospedes = {}   # texto do combo -> id
        self._quartos = {}

        topo = ctk.CTkFrame(self.corpo, fg_color="transparent")
        topo.pack(fill="x")
        topo.grid_columnconfigure(0, weight=3, uniform="topo")
        topo.grid_columnconfigure(1, weight=2, uniform="topo")
        self._montar_formulario(topo)
        self._montar_resumo(topo)
        self._montar_tabela()
        self.limpar()

    # ---------- montagem ----------
    def _montar_formulario(self, topo):
        form = Cartao(topo, "Nova reserva")
        form.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        grade = ctk.CTkFrame(form, fg_color="transparent")
        grade.pack(fill="x", padx=20)
        grade.grid_columnconfigure((0, 1, 2), weight=1, uniform="campos")

        self.hospede = CampoSelecao(grade, "Hóspede", [], self.atualizar_resumo)
        self.quarto = CampoSelecao(grade, "Quarto", [], self.atualizar_resumo)
        self.num = CampoTexto(grade, "Nº de hóspedes", "1", self.atualizar_resumo)
        self.entrada = CampoTexto(grade, "Data de entrada", "dd/mm/aaaa", self.atualizar_resumo)
        self.saida = CampoTexto(grade, "Data de saída", "dd/mm/aaaa", self.atualizar_resumo)
        self.hospede.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.quarto.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(0, 10))
        self.num.grid(row=2, column=0, sticky="ew", padx=(0, 8))
        self.entrada.grid(row=2, column=1, sticky="ew", padx=8)
        self.saida.grid(row=2, column=2, sticky="ew", padx=(8, 0))

        botoes = ctk.CTkFrame(form, fg_color="transparent")
        botoes.pack(anchor="w", padx=20, pady=(14, 18))
        botao_primario(botoes, "Confirmar reserva", self.confirmar, 170).pack(side="left")
        botao_secundario(botoes, "Limpar", self.limpar).pack(side="left", padx=10)

    def _montar_resumo(self, topo):
        resumo = Cartao(topo, "Resumo da reserva")
        resumo.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self.lbl_diarias = self._linha_resumo(resumo, "Diárias")
        self.lbl_valor = self._linha_resumo(resumo, "Valor da diária")
        ctk.CTkLabel(resumo, text="Total", font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(anchor="w", padx=20, pady=(12, 0))
        self.lbl_total = ctk.CTkLabel(resumo, text="—", font=fonte(32, True), text_color=AZUL)
        self.lbl_total.pack(anchor="w", padx=20)
        self.lbl_aviso = ctk.CTkLabel(resumo, text="", font=fonte(13, True), wraplength=330,
                                      justify="left", text_color=COR_TEXTO_SUAVE)
        self.lbl_aviso.pack(anchor="w", padx=20, pady=(10, 16))

    def _linha_resumo(self, pai, rotulo):
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=20, pady=2)
        ctk.CTkLabel(linha, text=rotulo, font=fonte(13), text_color=COR_TEXTO_SUAVE
                     ).pack(side="left")
        valor = ctk.CTkLabel(linha, text="—", font=fonte(13, True), text_color=COR_TEXTO)
        valor.pack(side="right")
        return valor

    def _montar_tabela(self):
        lista = Cartao(self.corpo, "Reservas")
        lista.pack(fill="both", expand=True, pady=(16, 0))
        # a barra de ações é empacotada primeiro, embaixo, para nunca ser espremida
        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", anchor="w", padx=20, pady=(0, 16))
        botao_perigo(acoes, "Cancelar reserva selecionada", self.cancelar, 240).pack(side="left")
        self.tabela = Tabela(lista, COLUNAS, altura=110)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

    # ---------- dados ----------
    def ao_exibir(self):
        self._carregar_opcoes()
        self.atualizar_tabela()
        self.atualizar_resumo()

    def _carregar_opcoes(self):
        self._hospedes = {f"{h.nome} — {h.cpf}": h.id for h in self.servicos.hospedes.listar()}
        self._quartos = {f"{q.numero} · {q.tipo} · {formatar_moeda(q.preco_diaria)}/dia": q.id
                         for q in self.servicos.quartos.listar()}
        self.hospede.definir_opcoes(list(self._hospedes))
        self.quarto.definir_opcoes(list(self._quartos))
        if self.hospede.valor() not in self._hospedes:
            self.hospede.limpar()
        if self.quarto.valor() not in self._quartos:
            self.quarto.limpar()

    def atualizar_tabela(self):
        reservas = sorted(self.servicos.reservas.listar(), key=lambda r: r.id, reverse=True)
        self.tabela.carregar(self.servicos.linhas_reservas(reservas))

    def _quarto_selecionado(self):
        quarto_id = self._quartos.get(self.quarto.valor())
        return self.servicos.quartos.buscar_por_id(quarto_id) if quarto_id else None

    # ---------- resumo e validação ----------
    def _mostrar(self, diarias=None, valor=None, total=None, aviso="",
                 cor=COR_TEXTO_SUAVE, valido=False):
        self.lbl_diarias.configure(text="—" if diarias is None else str(diarias))
        self.lbl_valor.configure(text="—" if valor is None else formatar_moeda(valor))
        self.lbl_total.configure(text="—" if total is None else formatar_moeda(total))
        self.lbl_aviso.configure(text=aviso, text_color=cor)
        return valido

    def atualizar_resumo(self):
        """Recalcula o resumo e retorna True se a reserva puder ser confirmada."""
        try:
            entrada = ler_data(self.entrada.valor())
            saida = ler_data(self.saida.valor())
        except ValueError as erro:
            return self._mostrar(aviso=str(erro))
        try:
            validar_periodo(entrada, saida)
        except ValueError as erro:
            return self._mostrar(aviso=str(erro), cor=VERMELHO)

        diarias = calcular_diarias(entrada, saida)
        quarto = self._quarto_selecionado()
        if quarto is None:
            return self._mostrar(diarias, aviso="Selecione um quarto.")

        total = calcular_total(diarias, quarto.preco_diaria)
        resultado = dict(diarias=diarias, valor=quarto.preco_diaria, total=total)

        if quarto.situacao == QUARTO_MANUTENCAO:
            return self._mostrar(**resultado, aviso="Quarto em manutenção.", cor=VERMELHO)
        if self.servicos.reservas.tem_conflito(quarto.id, entrada, saida):
            return self._mostrar(**resultado, aviso="Quarto já reservado neste período.",
                                 cor=VERMELHO)
        try:
            validar_capacidade(quarto, int(self.num.valor()))
        except ValueError as erro:
            texto = "Informe o número de hóspedes." if "invalid literal" in str(erro) else str(erro)
            return self._mostrar(**resultado, aviso=texto, cor=VERMELHO)

        return self._mostrar(**resultado, aviso="Quarto disponível no período.",
                             cor=VERDE, valido=True)

    # ---------- ações ----------
    def limpar(self):
        self.hospede.limpar()
        self.quarto.limpar()
        self.num.definir("1")
        hoje = date.today()
        self.entrada.definir(formatar_data(hoje))
        self.saida.definir(formatar_data(hoje + timedelta(days=1)))
        self.atualizar_resumo()

    def confirmar(self):
        hospede_id = self._hospedes.get(self.hospede.valor())
        if hospede_id is None:
            messagebox.showwarning("Hóspede obrigatório", "Selecione o hóspede da reserva.")
            return
        if not self.atualizar_resumo():
            messagebox.showerror("Não foi possível reservar", self.lbl_aviso.cget("text"))
            return

        quarto = self._quarto_selecionado()
        entrada, saida = ler_data(self.entrada.valor()), ler_data(self.saida.valor())
        try:
            reserva = self.servicos.reservas.criar_reserva(
                hospede_id, quarto.id, entrada, saida, int(self.num.valor()))
        except ErroNegocio as erro:
            messagebox.showerror("Não foi possível reservar", str(erro))
            return
        messagebox.showinfo("Reserva confirmada",
                            f"Reserva criada. Total: {formatar_moeda(reserva.valor_total)}")
        self.limpar()
        self.atualizar_tabela()

    def cancelar(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Cancelar", "Selecione uma reserva na tabela.")
            return
        reserva = self.servicos.reservas.buscar_por_id(linha["id"])
        if reserva is None or not pode_cancelar(reserva):
            messagebox.showerror("Não é possível cancelar",
                                 "Só é possível cancelar reservas confirmadas, antes do check-in.")
            return
        if not messagebox.askyesno("Cancelar reserva", f"Cancelar a reserva {linha['codigo']}?"):
            return
        try:
            self.servicos.reservas.cancelar(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Não é possível cancelar", str(erro))
            return
        self.atualizar_tabela()
        self.atualizar_resumo()
