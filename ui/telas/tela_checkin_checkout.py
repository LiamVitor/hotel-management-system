from tkinter import messagebox

import customtkinter as ctk

from src.services import checkin_regras as regras
from src.services import reserva_regras
from src.services.erros import ErroNegocio
from ui.componentes.campos import CampoTexto
from ui.componentes.cartao import Cartao
from ui.componentes.cartao_indicador import CartaoIndicador
from ui.componentes.janela_detalhes_reserva import abrir_detalhes
from ui.componentes.janela_pagamentos import abrir_pagamentos
from ui.componentes.tabela import Tabela
from ui.estilos import COR_TEXTO, COR_TEXTO_SUAVE, VERMELHO, estilo_badge_status, fonte
from ui.telas.tela_base import TelaBase
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.sessao import Sessao

ESPACO = 6                       # metade do espaço entre dois cartões
LARGURA_QUATRO_COLUNAS = 800     # abaixo disso, os cartões passam a ser 2 por linha

COLUNAS_CHEGADAS = [("Hóspede", "hospede", 200), ("Quarto", "quarto", 70),
                    ("Entrada", "entrada", 100), ("Saída", "saida", 100),
                    ("Pagamento", "pagamento", 105), ("Chegada", "chegada", 140)]
COLUNAS_HOSPEDADOS = [("Hóspede", "hospede", 190), ("Quarto", "quarto", 65),
                      ("Check-in real", "checkin_real_curto", 105), ("Saída prevista", "saida", 105),
                      ("Situação", "situacao_saida", 130), ("Saldo a pagar", "saldo", 105)]
COLUNAS_MOVIMENTOS = [("Hora", "hora", 70), ("Operação", "tipo", 100), ("Hóspede", "hospede", 230),
                      ("Quarto", "quarto", 70), ("Responsável", "responsavel", 160)]


class TelaCheckinCheckout(TelaBase):
    titulo = "Check-in / Check-out"

    def __init__(self, master, servicos):
        super().__init__(master, servicos)
        # São três listas: a rolagem fica só no conteúdo, com o título sempre visível.
        self.conteudo = ctk.CTkScrollableFrame(self.corpo, fg_color="transparent", corner_radius=0)
        self.conteudo.pack(fill="both", expand=True)

        self.cartoes = self._linha_de_cartoes()
        self.busca = CampoTexto(self.conteudo, "Pesquisar",
                                "Hóspede, CPF, quarto ou código da reserva",
                                ao_mudar=self.atualizar_tabelas)
        self.busca.pack(fill="x", pady=(16, 0))

        self.tabela_in, self.lbl_in = self._montar_lista(
            "Chegadas", COLUNAS_CHEGADAS, ("Fazer check-in", self.fazer_checkin),
            {"pagamento": estilo_badge_status, "chegada": estilo_badge_status})
        self.tabela_out, self.lbl_out = self._montar_lista(
            "Hóspedes hospedados", COLUNAS_HOSPEDADOS, ("Fazer check-out", self.fazer_checkout),
            {"situacao_saida": estilo_badge_status})
        self.tabela_mov, self.lbl_mov = self._montar_lista(
            "Movimentado hoje", COLUNAS_MOVIMENTOS, None, {"tipo": estilo_badge_status},
            altura=120, detalhes=False)

    # ---------- montagem ----------
    def _linha_de_cartoes(self):
        quadro = ctk.CTkFrame(self.conteudo, fg_color="transparent")
        quadro.pack(fill="x")
        titulos = [("pendentes", "Check-ins para hoje"), ("atrasadas", "Chegadas atrasadas"),
                   ("saidas", "Check-outs hoje"), ("hospedados", "Hospedados agora")]
        cartoes = {chave: CartaoIndicador(quadro, titulo) for chave, titulo in titulos}
        quadro._colunas_atuais = 0
        lista = list(cartoes.values())
        quadro.bind("<Configure>", lambda e: self._distribuir(quadro, lista, e.width))
        self._distribuir(quadro, lista, LARGURA_QUATRO_COLUNAS)
        return cartoes

    @staticmethod
    def _distribuir(quadro, cartoes, largura):
        """Quatro cartões em uma linha, ou duas colunas se a janela estiver estreita."""
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

    def _montar_lista(self, titulo, colunas, acao, badges, altura=150, detalhes=True):
        quadro = Cartao(self.conteudo, titulo)
        quadro.pack(fill="x", pady=(16, 0))
        tabela = Tabela(
            quadro, colunas, altura=altura, acao=acao, badges=badges,
            ao_duplo_clique=((lambda l: abrir_detalhes(self, self.servicos, l["id"]))
                             if detalhes else None))
        tabela.pack(fill="x", padx=20, pady=(0, 6))
        legenda = ctk.CTkLabel(quadro, text="", font=fonte(12), text_color=COR_TEXTO_SUAVE,
                               anchor="w", justify="left", wraplength=800)
        legenda.pack(anchor="w", padx=20, pady=(0, 14))
        return tabela, legenda

    # ---------- dados ----------
    def ao_exibir(self):
        self.atualizar_tabelas()

    def atualizar_tabelas(self):
        try:
            painel = self.servicos.checkin.painel(self.busca.valor())
        except ErroNegocio as erro:
            messagebox.showwarning("Check-in / Check-out", str(erro))
            return
        self._mostrar_cartoes(painel)
        self._mostrar_chegadas(painel)
        self._mostrar_hospedados(painel)
        self._mostrar_movimentos(painel)

    def _mostrar_cartoes(self, p):
        c = self.cartoes
        c["pendentes"].atualizar(p.chegadas_hoje, "com entrada prevista hoje")
        c["atrasadas"].atualizar(
            p.chegadas_atrasadas, "sem check-in" if p.chegadas_atrasadas else "nenhuma atrasada",
            cor_valor=VERMELHO if p.chegadas_atrasadas else COR_TEXTO,
            cor_detalhe=VERMELHO if p.chegadas_atrasadas else COR_TEXTO_SUAVE)
        c["saidas"].atualizar(
            p.saidas_hoje,
            f"{p.saidas_atrasadas} com saída atrasada" if p.saidas_atrasadas else "saem hoje",
            cor_detalhe=VERMELHO if p.saidas_atrasadas else COR_TEXTO_SUAVE)
        c["hospedados"].atualizar(p.total_hospedados, "no hotel agora")

    def _rotulo_lista(self, legenda, total, singular, plural, vazio, filtrando, extra=""):
        if not total:
            texto = "Nada encontrado para a pesquisa." if filtrando else vazio
        else:
            texto = f"{total} {singular if total == 1 else plural} · duplo clique para ver os detalhes."
        legenda.configure(text=(texto + (" " + extra if extra else "")).strip(),
                          text_color=VERMELHO if extra else COR_TEXTO_SUAVE)

    def _mostrar_chegadas(self, p):
        linhas = self.servicos.linhas_reservas(p.chegadas)
        for reserva, linha in zip(p.chegadas, linhas):
            linha["chegada"] = regras.rotulo_chegada(reserva, p.hoje)
        self.tabela_in.carregar(linhas)
        atrasadas = sum(1 for r in p.chegadas if r.data_entrada < p.hoje)
        aviso = ("Chegadas atrasadas: faça o check-in ou, se o hóspede não veio, "
                 "marque como não compareceu na tela Reservas.") if atrasadas else ""
        self._rotulo_lista(self.lbl_in, len(p.chegadas), "chegada", "chegadas",
                           "Nenhuma chegada pendente.", bool(self.busca.valor()), aviso)

    def _mostrar_hospedados(self, p):
        linhas = self.servicos.linhas_reservas(p.hospedados)
        for reserva, linha in zip(p.hospedados, linhas):
            linha["situacao_saida"] = regras.rotulo_saida(reserva, p.hoje)
        self.tabela_out.carregar(linhas)
        self._rotulo_lista(self.lbl_out, len(p.hospedados), "hóspede", "hóspedes",
                           "Ninguém hospedado no momento.", bool(self.busca.valor()))

    def _mostrar_movimentos(self, p):
        nomes = {l["id"]: l for l in self.servicos.linhas_reservas([m.reserva for m in p.movimentos])}
        linhas = [{"id": m.reserva.id, "hora": f"{m.quando:%H:%M}", "tipo": m.tipo,
                   "hospede": nomes[m.reserva.id]["hospede"], "quarto": nomes[m.reserva.id]["quarto"],
                   "responsavel": m.responsavel} for m in p.movimentos]
        self.tabela_mov.carregar(linhas)
        self.lbl_mov.configure(text="" if linhas else "Nenhum check-in ou check-out feito hoje ainda.")

    # ---------- operações ----------
    def _resolver_saldo(self, linha, reserva, resumo, operacao):
        """Se o hóspede deve, oferece lançar o pagamento antes. Devolve o resumo atualizado,
        ou None se a pessoa desistiu."""
        if resumo.saldo > 0 and Sessao.pode("pagamentos.registrar"):
            resposta = messagebox.askyesnocancel(
                "Saldo pendente",
                f"{linha['hospede']} ainda tem {formatar_moeda(resumo.saldo)} a pagar.\n\n"
                "Sim: registrar o pagamento agora\n"
                f"Não: fazer o {operacao} com o saldo pendente\n"
                "Cancelar: voltar")
            if resposta is None:
                return None
            if resposta:
                abrir_pagamentos(self, self.servicos, reserva.id, self.atualizar_tabelas)
                resumo = self.servicos.pagamentos.resumo(reserva.id)
        return resumo

    def fazer_checkin(self, linha):
        reserva = self.servicos.reservas.buscar_por_id(linha["id"])
        if reserva is None:
            return
        resumo = self._resolver_saldo(linha, reserva, self.servicos.pagamentos.resumo(reserva.id),
                                      "check-in")
        if resumo is None:
            return
        noites = reserva_regras.calcular_diarias(reserva.data_entrada, reserva.data_saida)
        pergunta = (f"Fazer check-in de {linha['hospede']} no quarto {linha['quarto']}?\n\n"
                    f"Estadia: {formatar_data(reserva.data_entrada)} a "
                    f"{formatar_data(reserva.data_saida)} ({noites} noite(s))\n"
                    f"Total: {formatar_moeda(resumo.valor_total)}    "
                    f"Pago: {formatar_moeda(resumo.total_pago)}\n"
                    f"Saldo pendente: {formatar_moeda(resumo.saldo)}")
        if linha.get("chegada", "Hoje") != "Hoje":
            pergunta += f"\n\nChegada prevista para {formatar_data(reserva.data_entrada)} ({linha['chegada'].lower()})."
        if not messagebox.askyesno("Check-in", pergunta):
            return
        try:
            reserva = self.servicos.reservas.fazer_checkin(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Check-in", str(erro))
            self.atualizar_tabelas()
            return
        self.atualizar_tabelas()
        self._avisar("Check-in realizado", f"Check-in de {linha['hospede']} registrado", reserva,
                     reserva.checkin_em, reserva.checkin_por)

    def fazer_checkout(self, linha):
        reserva = self.servicos.reservas.buscar_por_id(linha["id"])
        if reserva is None:
            return
        resumo = self._resolver_saldo(linha, reserva, self.servicos.pagamentos.resumo(reserva.id),
                                      "check-out")
        if resumo is None:
            return
        pergunta = (f"Fazer check-out de {linha['hospede']}?\n"
                    f"Total: {formatar_moeda(resumo.valor_total)}    "
                    f"Pago: {formatar_moeda(resumo.total_pago)}\n"
                    f"Saldo pendente: {formatar_moeda(resumo.saldo)}")
        if not messagebox.askyesno("Check-out", pergunta):
            return
        try:
            reserva = self.servicos.reservas.fazer_checkout(linha["id"])
        except ErroNegocio as erro:
            messagebox.showerror("Check-out", str(erro))
            self.atualizar_tabelas()
            return
        self.atualizar_tabelas()
        noites = reserva_regras.noites_reais(reserva)
        self._avisar("Check-out realizado", f"Check-out de {linha['hospede']} registrado", reserva,
                     reserva.checkout_em, reserva.checkout_por,
                     extra=f"Permanência real: {noites} noite(s)." if noites is not None else "")

    def _avisar(self, titulo, inicio, reserva, quando, usuario_id, extra=""):
        """Confirma na tela o momento real e quem fez a operação (o usuário logado)."""
        nome = self.servicos.reservas.responsaveis([reserva]).get(usuario_id, "—")
        mensagem = f"{inicio} em {quando:%d/%m/%Y} às {quando:%H:%M}, por {nome}."
        if extra:
            mensagem += f"\n\n{extra}"
        messagebox.showinfo(titulo, mensagem)
