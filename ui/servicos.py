"""Reúne os services usados pelas telas e prepara linhas para as tabelas."""
from src.models.pagamento import Pagamento
from src.services.despesa_service import DespesaService
from src.services.hospede_service import HospedeService
from src.services.pagamento_regras import saldo_pendente, situacao_pagamento
from src.services.pagamento_service import PagamentoService
from src.services.quarto_service import QuartoService
from src.services.reserva_service import ReservaService
from src.services.usuario_service import UsuarioService
from src.utils.constantes import PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA, RESERVA_NO_SHOW
from src.utils.formatacao import formatar_data, formatar_data_hora, formatar_moeda


class Servicos:
    def __init__(self):
        self.hospedes = HospedeService()
        self.quartos = QuartoService()
        self.reservas = ReservaService()
        self.pagamentos = PagamentoService()
        self.despesas = DespesaService()
        self.usuarios = UsuarioService()

    def linhas_reservas(self, reservas):
        """Converte reservas em dicionários prontos para as tabelas."""
        nomes = {h.id: h.nome for h in self.hospedes.listar()}
        numeros = {q.id: q.numero for q in self.quartos.listar()}
        totais_pagos = self.pagamentos.totais_por_reserva()
        linhas = []
        for r in reservas:
            pago = totais_pagos.get(r.id, 0.0)
            cancelada = r.situacao == RESERVA_CANCELADA
            no_show = r.situacao == RESERVA_NO_SHOW
            linhas.append({
                "id": r.id,
                "codigo": f"{r.id:04d}",
                "hospede": nomes.get(r.hospede_id, "—"),
                "quarto": numeros.get(r.quarto_id, "—"),
                "entrada": formatar_data(r.data_entrada),
                "saida": formatar_data(r.data_saida),
                "total": formatar_moeda(r.valor_total),
                "pago": formatar_moeda(pago),
                "saldo": formatar_moeda(saldo_pendente(r.valor_total, pago)),
                "pagamento": (("A reembolsar" if pago > 0 else "—") if cancelada
                              else ("Valor retido" if pago > 0 else "—") if no_show
                              else situacao_pagamento(r.valor_total, pago)),
                "situacao": r.situacao,
                # datas e horários REAIS (as de cima, entrada e saida, são as previstas)
                "checkin_real": formatar_data_hora(r.checkin_em),
                "checkin_real_curto": formatar_data_hora(r.checkin_em, curto=True),
                "checkout_real": formatar_data_hora(r.checkout_em),
                "checkout_real_curto": formatar_data_hora(r.checkout_em, curto=True),
                "criada_em": formatar_data_hora(r.criada_em),
                "cancelada_em": formatar_data_hora(r.cancelada_em),
                "noshow_em": formatar_data_hora(r.noshow_em),
            })
        return linhas

    def linhas_pagamentos(self, historico):
        """Converte [(Pagamento, nome de quem lançou)] em dicionários para a tabela.

        Cada linha traz "detalhe" (curto, para a coluna) e "descricao" (completa, mostrada
        ao selecionar a linha). Pagamentos já reembolsados continuam na lista, com a marcação.
        """
        por_id = {p.id: p for p, _ in historico}
        devolvido = {}
        for p, _ in historico:
            if p.tipo == PAGAMENTO_REEMBOLSO and p.pagamento_origem_id:
                devolvido[p.pagamento_origem_id] = round(
                    devolvido.get(p.pagamento_origem_id, 0.0) + p.valor, 2)

        linhas = []
        for p, nome in historico:
            quando = p.data_hora.strftime("%d/%m/%Y %H:%M")
            quem = nome or "—"
            if p.tipo == PAGAMENTO_REEMBOLSO:
                origem = por_id.get(p.pagamento_origem_id)
                referencia = (
                    f"Referente ao pagamento de {origem.data_hora:%d/%m/%Y %H:%M} "
                    f"({origem.forma}, {formatar_moeda(origem.valor)})."
                    if origem else "Vinculado à reserva, sem um pagamento específico.")
                detalhe = p.motivo or ""
                descricao = (f"Reembolso de {formatar_moeda(p.valor)} em {p.forma}, lançado por "
                             f"{quem} em {quando}. Motivo: {p.motivo or '—'}. {referencia}")
                valor = "- " + formatar_moeda(p.valor)
            else:
                voltou = devolvido.get(p.id, 0.0)
                detalhe = f"Reembolsado: {formatar_moeda(voltou)}" if voltou else ""
                descricao = (f"Pagamento de {formatar_moeda(p.valor)} em {p.forma}, lançado por "
                             f"{quem} em {quando}.")
                if voltou:
                    descricao += (f" Já reembolsado: {formatar_moeda(voltou)} "
                                  f"(restam {formatar_moeda(p.valor - voltou)}).")
                valor = formatar_moeda(p.valor)
            linhas.append({
                "id": p.id, "data_hora": quando, "valor": valor, "forma": p.forma,
                "tipo": p.tipo, "responsavel": quem, "detalhe": detalhe, "descricao": descricao,
            })
        return linhas

    def linhas_despesas(self, despesas):
        """Converte despesas em dicionários prontos para a tabela (com nomes em vez de ids)."""
        categorias = self.despesas.nomes_categorias()
        responsaveis = self.despesas.nomes_responsaveis(despesas)
        return [{
            "id": d.id,
            "data": formatar_data(d.data),
            "categoria": categorias.get(d.categoria_id, "—"),
            "descricao": d.descricao,
            "valor": formatar_moeda(d.valor),
            "responsavel": responsaveis.get(d.usuario_id, "—"),
        } for d in despesas]
