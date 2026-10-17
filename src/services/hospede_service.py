from src.repositories.hospede_repository import HospedeRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services.erros import ErroNegocio


class HospedeService:
    def __init__(self, repo=None, reserva_repo=None):
        self.repo = repo or HospedeRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()

    def listar(self, termo=""):
        """Lista hóspedes em ordem alfabética, filtrando por nome ou CPF."""
        termo = termo.strip().lower()
        return [h for h in self.repo.listar()
                if not termo or termo in h.nome.lower() or termo in h.cpf]

    def buscar_por_id(self, hospede_id):
        return self.repo.buscar_por_id(hospede_id)

    def salvar(self, hospede):
        """Cria (id vazio) ou atualiza um hóspede, aplicando as validações."""
        hospede.nome = (hospede.nome or "").strip()
        hospede.cpf = (hospede.cpf or "").strip()
        hospede.telefone = (hospede.telefone or "").strip() or None
        hospede.email = (hospede.email or "").strip() or None

        if not hospede.nome or not hospede.cpf:
            raise ErroNegocio("Informe o nome e o CPF.")
        existente = self.repo.buscar_por_cpf(hospede.cpf)
        if existente is not None and existente.id != hospede.id:
            raise ErroNegocio("Já existe um hóspede com este CPF.")

        if hospede.id is None:
            return self.repo.criar(hospede)
        self.repo.atualizar(hospede)
        return hospede

    def excluir(self, hospede_id):
        if self.reserva_repo.listar_por_hospede(hospede_id):
            raise ErroNegocio("Este hóspede possui reservas e não pode ser excluído.")
        self.repo.remover(hospede_id)
