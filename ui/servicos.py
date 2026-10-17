"""Reúne os services usados pelas telas e prepara linhas para as tabelas."""
from src.services.hospede_service import HospedeService
from src.services.quarto_service import QuartoService
from src.services.reserva_service import ReservaService
from src.utils.formatacao import formatar_data, formatar_moeda


class Servicos:
    def __init__(self):
        self.hospedes = HospedeService()
        self.quartos = QuartoService()
        self.reservas = ReservaService()

    def linhas_reservas(self, reservas):
        """Converte reservas em dicionários prontos para as tabelas."""
        nomes = {h.id: h.nome for h in self.hospedes.listar()}
        numeros = {q.id: q.numero for q in self.quartos.listar()}
        return [{
            "id": r.id,
            "codigo": f"{r.id:04d}",
            "hospede": nomes.get(r.hospede_id, "—"),
            "quarto": numeros.get(r.quarto_id, "—"),
            "entrada": formatar_data(r.data_entrada),
            "saida": formatar_data(r.data_saida),
            "total": formatar_moeda(r.valor_total),
            "situacao": r.situacao,
        } for r in reservas]
