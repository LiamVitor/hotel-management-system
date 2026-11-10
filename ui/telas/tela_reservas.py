from datetime import date, timedelta
from tkinter import messagebox

import customtkinter as ctk

from src.services.erros import ErroNegocio
from src.services.reserva_regras import (calcular_diarias, calcular_total, pode_cancelar,
                                         validar_capacidade, validar_periodo)
from ui.componentes.botoes import botao_perigo, botao_primario, botao_secundario
from ui.componentes.campo_data import CampoData
from ui.componentes.campos import CampoTexto, reformatar_entrada
from ui.componentes.cartao import Cartao
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.janela_pagamentos import abrir_pagamentos as abrir_janela_pagamentos
from ui.componentes.janela_reembolso import abrir_reembolso
from ui.componentes.seletor import CampoSeletor, JanelaSelecao
from ui.componentes.tabela import Tabela
from ui.estilos import (AZUL, COR_BORDA_CAMPO, COR_SELECAO, COR_TEXTO, COR_TEXTO_SUAVE, VERDE,
                        VERMELHO, fonte)
from ui.telas.tela_base import TelaBase
from src.utils.constantes import QUARTO_MANUTENCAO, SITUACOES_RESERVA
from src.utils.filtros import normalizar_texto
from src.utils.sessao import Sessao
from src.utils.formatacao import (formatar_cpf, formatar_data, formatar_moeda,
                                  formatar_telefone, ler_data, mascara_data)

COLUNAS = [("Código", "codigo", 66), ("Hóspede", "hospede", 190), ("Quarto", "quarto", 62),
           ("Entrada", "entrada", 95), ("Saída", "saida", 95), ("Total", "total", 110),
           ("Status", "situacao", 100), ("Pagamento", "pagamento", 95)]

COLUNAS_SELECAO_HOSPEDE = [("Nome", "nome", 230), ("CPF", "cpf", 130),
                           ("Telefone", "telefone", 140), ("E-mail", "email", 200)]
COLUNAS_SELECAO_QUARTO = [("Número", "numero", 90), ("Tipo", "tipo", 130),
                          ("Capacidade", "capacidade", 110), ("Diária", "diaria", 130),
                          ("Status", "situacao", 130)]

TODAS = "Todas"


class TelaReservas(TelaBase):
    titulo = "Reservas"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)

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

        self.hospede = CampoSeletor(grade, "Hóspede", "Clique para pesquisar e escolher o hóspede…",
                                    self._abrir_selecao_hospede, self.atualizar_resumo)
        self.quarto = CampoSeletor(grade, "Quarto", "Clique para pesquisar e escolher o quarto…",
                                   self._abrir_selecao_quarto, self.atualizar_resumo)
        self.num = CampoTexto(grade, "Nº de hóspedes", "1", self.atualizar_resumo)
        self.entrada = CampoData(grade, "Data de entrada", self.atualizar_resumo,
                                 ao_escolher=self._ao_escolher_entrada)
        self.saida = CampoData(grade, "Data de saída", self.atualizar_resumo,
                               data_minima=self._menor_data_de_saida)
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
        self._montar_filtros(lista)

        # a barra de ações é empacotada antes da tabela, embaixo, para nunca ser espremida
        acoes = ctk.CTkFrame(lista, fg_color="transparent")
        acoes.pack(side="bottom", fill="x", padx=20, pady=(0, 16))
        if Sessao.pode("reservas.cancelar"):
            botao_perigo(acoes, "Cancelar reserva selecionada", self.cancelar, 240
                         ).pack(side="left")
        botao_secundario(acoes, "Pagamentos da reserva selecionada", self.abrir_pagamentos, 270
                         ).pack(side="left", padx=(10, 0))
        botao_secundario(acoes, "Detalhes da reserva", self.abrir_detalhes, 160
                         ).pack(side="left", padx=(10, 0))
        self.lbl_filtro = ctk.CTkLabel(acoes, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE)
        self.lbl_filtro.pack(side="left", padx=14)

        self.tabela = Tabela(lista, COLUNAS, altura=110, ao_duplo_clique=self.abrir_pagamentos)
        self.tabela.pack(fill="both", expand=True, padx=20, pady=(0, 8))

    def _montar_filtros(self, lista):
        filtros = ctk.CTkFrame(lista, fg_color="transparent")
        filtros.pack(fill="x", padx=20, pady=(0, 10))

        self.busca = self._entrada_filtro(filtros, "Hóspede, CPF, quarto ou código", 280)
        self.filtro_situacao = ctk.CTkComboBox(
            filtros, values=[TODAS, *SITUACOES_RESERVA], state="readonly", width=130, height=36,
            command=lambda _v: self.atualizar_tabela(), fg_color="white",
            border_color=COR_BORDA_CAMPO, button_color=COR_BORDA_CAMPO,
            button_hover_color="#9CA3AF", text_color=COR_TEXTO, dropdown_fg_color="white",
            dropdown_text_color=COR_TEXTO, dropdown_hover_color=COR_SELECAO, font=fonte(13))
        self.filtro_situacao.set(TODAS)
        self.filtro_situacao.pack(side="left", padx=(0, 10))

        ctk.CTkLabel(filtros, text="Período", font=fonte(12, True), text_color=COR_TEXTO_SUAVE
                     ).pack(side="left", padx=(4, 8))
        self.filtro_de = self._entrada_filtro(filtros, "dd/mm/aaaa", 110, mascara_data, 0)
        ctk.CTkLabel(filtros, text="até", font=fonte(12), text_color=COR_TEXTO_SUAVE
                     ).pack(side="left", padx=(0, 8))
        self.filtro_ate = self._entrada_filtro(filtros, "dd/mm/aaaa", 110, mascara_data)
        botao_secundario(filtros, "Limpar filtros", self.limpar_filtros, 120).pack(side="left")

    def _entrada_filtro(self, pai, placeholder, largura, mascara=None, espaco_direita=10):
        entrada = ctk.CTkEntry(pai, placeholder_text=placeholder, width=largura, height=36,
                               fg_color="white", border_color=COR_BORDA_CAMPO,
                               text_color=COR_TEXTO, placeholder_text_color="#9CA3AF",
                               font=fonte(13))
        entrada.pack(side="left", padx=(0, espaco_direita))

        def ao_digitar(_evento=None):
            if mascara:
                reformatar_entrada(entrada, mascara)
            self.atualizar_tabela()
        entrada.bind("<KeyRelease>", ao_digitar)
        return entrada

    # ---------- datas ----------
    def _menor_data_de_saida(self):
        """No calendário da saída, os dias até a entrada ficam bloqueados."""
        entrada = self.entrada.data()
        return entrada + timedelta(days=1) if entrada else None

    def _ao_escolher_entrada(self, entrada):
        """Escolheu a entrada no calendário: se a saída ficou vazia ou não é posterior,
        leva a saída para o dia seguinte."""
        saida = self.saida.data()
        if saida is None or saida <= entrada:
            self.saida.definir(formatar_data(entrada + timedelta(days=1)))

    # ---------- escolha de hóspede e quarto ----------
    @staticmethod
    def _texto_hospede(h):
        return f"{h.nome} — {formatar_cpf(h.cpf)}"

    @staticmethod
    def _texto_quarto(q):
        return f"{q.numero} · {q.tipo} · {formatar_moeda(q.preco_diaria)}/dia"

    def _abrir_selecao_hospede(self, escolher):
        def buscar(termo, _opcao):
            return [{"id": h.id, "nome": h.nome, "cpf": formatar_cpf(h.cpf),
                     "telefone": formatar_telefone(h.telefone), "email": h.email or "",
                     "texto": self._texto_hospede(h)}
                    for h in self.servicos.hospedes.listar(termo)]

        JanelaSelecao(self, "Selecionar hóspede", COLUNAS_SELECAO_HOSPEDE, buscar,
                      lambda linha: escolher(linha["id"], linha["texto"]),
                      placeholder="Buscar por nome, CPF, telefone ou e-mail")

    def _abrir_selecao_quarto(self, escolher):
        periodo = self._periodo_informado()
        pessoas = self._numero_hospedes() or 1
        if periodo:
            entrada, saida = periodo
            opcao = ("Mostrar só quartos disponíveis no período e com capacidade suficiente", True)
            informacao = (f"Período de {formatar_data(entrada)} a {formatar_data(saida)} "
                          f"para {pessoas} hóspede(s).")
        else:
            opcao = None
            informacao = ("Informe datas de entrada e saída válidas para filtrar só os quartos "
                          "disponíveis no período.")

        def buscar(termo, so_disponiveis):
            if periodo and so_disponiveis:
                quartos = self.servicos.quartos.listar_disponiveis(*periodo, pessoas)
            else:
                quartos = self.servicos.quartos.listar()
            termo = normalizar_texto(termo.strip())
            return [{"id": q.id, "numero": q.numero, "tipo": q.tipo,
                     "capacidade": q.capacidade, "diaria": formatar_moeda(q.preco_diaria),
                     "situacao": q.situacao, "texto": self._texto_quarto(q)}
                    for q in quartos
                    if not termo or termo in normalizar_texto(q.numero)
                    or termo in normalizar_texto(q.tipo)]

        JanelaSelecao(self, "Selecionar quarto", COLUNAS_SELECAO_QUARTO, buscar,
                      lambda linha: escolher(linha["id"], linha["texto"]),
                      placeholder="Buscar por número ou tipo", opcao=opcao,
                      informacao=informacao)

    def _periodo_informado(self):
        """(entrada, saida) se as duas datas do formulário forem válidas; senão None."""
        try:
            entrada, saida = ler_data(self.entrada.valor()), ler_data(self.saida.valor())
            validar_periodo(entrada, saida)
        except ValueError:
            return None
        return entrada, saida

    def _numero_hospedes(self):
        try:
            numero = int(self.num.valor())
        except ValueError:
            return None
        return numero if numero >= 1 else None

    # ---------- dados ----------
    def ao_exibir(self):
        self._atualizar_selecoes()
        self.atualizar_tabela()
        self.atualizar_resumo()

    def _atualizar_selecoes(self):
        """Se o hóspede/quarto escolhido foi editado ou excluído, atualiza ou limpa."""
        if self.hospede.valor():
            h = self.servicos.hospedes.buscar_por_id(self.hospede.valor())
            if h is None:
                self.hospede.limpar(notificar=False)
            else:
                self.hospede.definir(h.id, self._texto_hospede(h), notificar=False)
        if self.quarto.valor():
            q = self.servicos.quartos.buscar_por_id(self.quarto.valor())
            if q is None:
                self.quarto.limpar(notificar=False)
            else:
                self.quarto.definir(q.id, self._texto_quarto(q), notificar=False)

    def _ler_data_filtro(self, entrada):
        """Data do filtro, ou None enquanto a pessoa ainda está digitando."""
        texto = entrada.get().strip()
        return ler_data(texto) if len(texto) == 10 else None

    def atualizar_tabela(self):
        try:
            situacao = self.filtro_situacao.get()
            reservas = self.servicos.reservas.pesquisar(
                self.busca.get(), "" if situacao in ("", TODAS) else situacao,
                self._ler_data_filtro(self.filtro_de), self._ler_data_filtro(self.filtro_ate))
        except (ValueError, ErroNegocio) as erro:
            self.lbl_filtro.configure(text=str(erro), text_color=VERMELHO)
            return
        self.lbl_filtro.configure(text=f"{len(reservas)} reserva(s) encontrada(s)",
                                  text_color=COR_TEXTO_SUAVE)
        self.tabela.carregar(self.servicos.linhas_reservas(reservas))

    def limpar_filtros(self):
        for entrada in (self.busca, self.filtro_de, self.filtro_ate):
            entrada.delete(0, "end")
        self.filtro_situacao.set(TODAS)
        self.winfo_toplevel().focus_set()   # devolve o texto de exemplo aos campos
        self.atualizar_tabela()

    def _quarto_selecionado(self):
        quarto_id = self.quarto.valor()
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
        self.hospede.limpar(notificar=False)
        self.quarto.limpar(notificar=False)
        self.num.definir("1")
        hoje = date.today()
        self.entrada.definir(formatar_data(hoje))
        self.saida.definir(formatar_data(hoje + timedelta(days=1)))
        self.atualizar_resumo()

    def confirmar(self):
        hospede_id = self.hospede.valor()
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

    def abrir_detalhes(self):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Detalhes", "Selecione uma reserva na tabela.")
            return
        abrir_detalhes(self, self.servicos, linha["id"])

    def abrir_pagamentos(self, _linha=None):
        linha = self.tabela.selecionado()
        if linha is None:
            messagebox.showinfo("Pagamentos", "Selecione uma reserva na tabela.")
            return
        abrir_janela_pagamentos(self, self.servicos, linha["id"], self.atualizar_tabela)

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
        self._oferecer_reembolso(linha)

    def _oferecer_reembolso(self, linha):
        """Depois de cancelar uma reserva já paga, oferece registrar a devolução do valor."""
        pago = self.servicos.pagamentos.resumo(linha["id"]).total_pago
        if pago <= 0 or not Sessao.pode("pagamentos.reembolsar"):
            return
        if messagebox.askyesno("Reembolso", f"Esta reserva tinha {formatar_moeda(pago)} pagos.\n\n"
                                            "Deseja registrar o reembolso agora?"):
            abrir_reembolso(self, self.servicos, linha["id"], ao_atualizar=self.atualizar_tabela)
