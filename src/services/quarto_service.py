from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services.erros import ErroNegocio
from src.utils.constantes import SITUACOES_QUARTO, TIPOS_QUARTO


class QuartoService:
    def __init__(self, repo=None, reserva_repo=None):
        self.repo = repo or QuartoRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()

    def listar(self):
        return self.repo.listar()

    def buscar_por_id(self, quarto_id):
        return self.repo.buscar_por_id(quarto_id)

    def listar_disponiveis(self, entrada, saida, capacidade_minima=1):
        return self.repo.listar_disponiveis(entrada, saida, capacidade_minima)

    def salvar(self, quarto):
        """Cria (id vazio) ou atualiza um quarto, aplicando as validações."""
        quarto.numero = (quarto.numero or "").strip()
        if not quarto.numero:
            raise ErroNegocio("Informe o número do quarto.")
        if quarto.tipo not in TIPOS_QUARTO:
            raise ErroNegocio("Selecione o tipo do quarto.")
        if quarto.situacao not in SITUACOES_QUARTO:
            raise ErroNegocio("Selecione o status do quarto.")
        if quarto.capacidade < 1:
            raise ErroNegocio("A capacidade deve ser maior que 0.")
        if quarto.preco_diaria <= 0:
            raise ErroNegocio("A diária deve ser maior que R$ 0,00.")
        existente = self.repo.buscar_por_numero(quarto.numero)
        if existente is not None and existente.id != quarto.id:
            raise ErroNegocio("Já existe um quarto com este número.")

        if quarto.id is None:
            return self.repo.criar(quarto)
        self.repo.atualizar(quarto)
        return quarto

    def excluir(self, quarto_id):
        if self.reserva_repo.listar_por_quarto(quarto_id):
            raise ErroNegocio("Este quarto possui reservas. Se não for mais usado, "
                              "altere o status para Manutenção.")
        self.repo.remover(quarto_id)
