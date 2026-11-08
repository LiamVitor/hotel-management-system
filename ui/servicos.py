"""Reúne os services usados pelas telas e prepara linhas para as tabelas."""
from src.models.pagamento import Pagamento
from src.services.hospede_service import HospedeService
from src.services.pagamento_regras import saldo_pendente, situacao_pagamento
from src.services.pagamento_service import PagamentoService
from src.services.quarto_service import QuartoService
from src.services.reserva_service import ReservaService
from src.services.usuario_service import UsuarioService
from src.utils.constantes import PAGAMENTO_REEMBOLSO, RESERVA_CANCELADA
from src.utils.formatacao import formatar_data, formatar_moeda


class Servicos:
    def __init__(self):
        self.hospedes = HospedeService()
        self.quartos = QuartoService()
        self.reservas = ReservaService()
        self.pagamentos = PagamentoService()
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
                "pagamento": "—" if cancelada else situacao_pagamento(r.valor_total, pago),
                "situacao": r.situacao,
            })
        return linhas

    def linhas_pagamentos(self, historico):
        """Converte [(Pagamento, nome de quem lançou)] em dicionários para a tabela."""
        return [{
            "id": p.id,
            "data_hora": p.data_hora.strftime("%d/%m/%Y %H:%M"),
            "valor": (("- " if p.tipo == PAGAMENTO_REEMBOLSO else "")
                      + formatar_moeda(p.valor)),
            "forma": p.forma,
            "tipo": p.tipo,
            "responsavel": nome or "—",
        } for p, nome in historico]
