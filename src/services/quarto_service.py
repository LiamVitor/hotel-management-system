from src.repositories.quarto_repository import QuartoRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services.erros import ErroNegocio
from src.utils.constantes import SITUACOES_QUARTO, TIPOS_QUARTO
from src.utils.alteracoes import calcular_alteracoes
from src.utils.filtros import criar_filtro_faixa, normalizar_texto
from src.utils.formatacao import formatar_moeda
from src.utils.sessao import Sessao


class QuartoService:
    def __init__(self, repo=None, reserva_repo=None):
        self.repo = repo or QuartoRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()

    def listar(self):
        return self.repo.listar()

    def pesquisar(self, numero="", tipo="", situacao="", capacidade_min="", capacidade_max="",
                  diaria_min="", diaria_max=""):
        """Filtra os quartos. Todos os filtros são opcionais e se combinam (E).

        numero:     parte do número ('10' acha 101, 102, 210...)
        tipo, situacao: valor exato
        capacidade_min/max, diaria_min/max: faixa com os limites incluídos; qualquer lado
                    pode ficar vazio (sem limite)
        """
        try:
            filtro_capacidade = criar_filtro_faixa(capacidade_min, capacidade_max)
            filtro_diaria = criar_filtro_faixa(diaria_min, diaria_max)
        except ValueError as erro:
            raise ErroNegocio(str(erro))

        numero = normalizar_texto((numero or "").strip())
        encontrados = []
        for q in self.repo.listar():
            if numero and numero not in normalizar_texto(q.numero):
                continue
            if tipo and q.tipo != tipo:
                continue
            if situacao and q.situacao != situacao:
                continue
            if filtro_capacidade and not filtro_capacidade(q.capacidade):
                continue
            if filtro_diaria and not filtro_diaria(q.preco_diaria):
                continue
            encontrados.append(q)
        return encontrados

    def buscar_por_id(self, quarto_id):
        return self.repo.buscar_por_id(quarto_id)

    def listar_disponiveis(self, entrada, saida, capacidade_minima=1):
        return self.repo.listar_disponiveis(entrada, saida, capacidade_minima)

    def validar(self, quarto):
        """Normaliza e valida os dados, sem gravar nada. Levanta ErroNegocio se algo estiver errado."""
        Sessao.exigir("quartos.salvar")
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

    def diferencas(self, quarto):
        """O que muda ao salvar este quarto já validado (lista de Alteracao, vazia se nada mudou)."""
        atual = self.repo.buscar_por_id(quarto.id)
        if atual is None:
            raise ErroNegocio("Quarto não encontrado.")
        return calcular_alteracoes([
            ("Número", atual.numero, quarto.numero),
            ("Tipo", atual.tipo, quarto.tipo),
            ("Capacidade", atual.capacidade, quarto.capacidade),
            ("Diária", formatar_moeda(atual.preco_diaria), formatar_moeda(quarto.preco_diaria)),
            ("Status", atual.situacao, quarto.situacao),
        ])

    def salvar(self, quarto):
        """Cria (id vazio) ou atualiza um quarto, aplicando as validações."""
        self.validar(quarto)
        if quarto.id is None:
            return self.repo.criar(quarto)
        self.repo.atualizar(quarto)
        return quarto

    def excluir(self, quarto_id):
        Sessao.exigir("quartos.excluir")
        if self.reserva_repo.listar_por_quarto(quarto_id):
            raise ErroNegocio("Este quarto possui reservas. Se não for mais usado, "
                              "altere o status para Manutenção.")
        self.repo.remover(quarto_id)
