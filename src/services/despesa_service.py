import math
from datetime import date, datetime

from src.models.despesa import CategoriaDespesa, DadosDespesa, Despesa
from src.repositories.categoria_despesa_repository import CategoriaDespesaRepository
from src.repositories.despesa_repository import DespesaRepository
from src.repositories.usuario_repository import UsuarioRepository
from src.services import despesa_regras as regras
from src.services.erros import ErroNegocio
from src.utils.alteracoes import calcular_alteracoes
from src.utils.filtros import normalizar_texto
from src.utils.formatacao import formatar_data, formatar_moeda
from src.utils.sessao import Sessao

PERMISSAO = "despesas.gerenciar"


def _agora():
    """Hora atual sem microssegundos, igual ao que o banco guarda."""
    return datetime.now().replace(microsecond=0)


DESCRICAO_MIN, DESCRICAO_MAX = 3, 200
CATEGORIA_MIN, CATEGORIA_MAX = 2, 40


class DespesaService:
    """Despesas da pousada e suas categorias. Só gerente e administrador acessam."""

    def __init__(self, repo=None, categoria_repo=None, usuario_repo=None):
        self.repo = repo or DespesaRepository()
        self.categoria_repo = categoria_repo or CategoriaDespesaRepository()
        self.usuario_repo = usuario_repo or UsuarioRepository()

    # =============== categorias ===============
    def listar_categorias(self, apenas_ativas=False):
        Sessao.exigir(PERMISSAO)
        return self.categoria_repo.listar(apenas_ativas)

    def nomes_categorias(self):
        """{categoria_id: nome} de todas as categorias (ativas e inativas)."""
        Sessao.exigir(PERMISSAO)
        return {c.id: c.nome for c in self.categoria_repo.listar()}

    def contagem_por_categoria(self):
        Sessao.exigir(PERMISSAO)
        return self.repo.contar_por_categoria()

    def criar_categoria(self, nome):
        Sessao.exigir(PERMISSAO)
        nome = self._validar_nome_categoria(nome)
        return self.categoria_repo.criar(CategoriaDespesa(nome=nome))

    def renomear_categoria(self, categoria_id, nome):
        Sessao.exigir(PERMISSAO)
        categoria = self._obter_categoria(categoria_id)
        categoria.nome = self._validar_nome_categoria(nome, ignorar_id=categoria_id)
        self.categoria_repo.atualizar(categoria)
        return categoria

    def definir_categoria_ativa(self, categoria_id, ativa):
        """Desativar tira a categoria das listas de escolha; as despesas antigas continuam nela."""
        Sessao.exigir(PERMISSAO)
        categoria = self._obter_categoria(categoria_id)
        categoria.ativa = bool(ativa)
        self.categoria_repo.atualizar(categoria)
        return categoria

    # =============== despesas ===============
    def validar(self, dados, despesa_id=None):
        """Normaliza e valida o que foi preenchido, sem gravar. Devolve os dados prontos.

        Ao editar (despesa_id), manter a categoria atual é sempre permitido, mesmo que ela
        tenha sido desativada depois; trocar para outra exige uma categoria ativa.
        """
        Sessao.exigir(PERMISSAO)
        if not isinstance(dados.data, date) or isinstance(dados.data, datetime):
            raise ErroNegocio("Informe a data da despesa.")
        if dados.data > date.today():
            raise ErroNegocio("A data da despesa não pode ser futura.")

        descricao = (dados.descricao or "").strip()
        if len(descricao) < DESCRICAO_MIN:
            raise ErroNegocio("Informe a descrição da despesa.")
        if len(descricao) > DESCRICAO_MAX:
            raise ErroNegocio(f"A descrição deve ter no máximo {DESCRICAO_MAX} caracteres.")

        try:
            valor = regras.arredondar(float(dados.valor))
        except (TypeError, ValueError):
            raise ErroNegocio("Informe um valor válido para a despesa.")
        if not math.isfinite(valor) or valor <= 0:
            raise ErroNegocio("O valor da despesa deve ser maior que zero.")

        categoria = self.categoria_repo.buscar_por_id(dados.categoria_id)
        if categoria is None:
            raise ErroNegocio("Selecione a categoria da despesa.")
        if not categoria.ativa:
            atual = self.repo.buscar_por_id(despesa_id) if despesa_id else None
            if atual is None or atual.categoria_id != categoria.id:
                raise ErroNegocio("Esta categoria está desativada. Escolha outra ou reative-a.")
        return DadosDespesa(data=dados.data, descricao=descricao, valor=valor,
                            categoria_id=categoria.id)

    def registrar(self, dados):
        """Lança uma despesa nova. O responsável é o usuário logado e a hora é a do lançamento."""
        dados = self.validar(dados)
        return self.repo.criar(Despesa(
            data=dados.data, descricao=dados.descricao, valor=dados.valor,
            categoria_id=dados.categoria_id, usuario_id=Sessao.usuario.id,
            criada_em=_agora()))

    def diferencas(self, despesa_id, dados):
        """O que muda ao salvar estes dados já validados (lista de Alteracao, vazia se nada mudou)."""
        Sessao.exigir(PERMISSAO)
        atual = self._obter(despesa_id)
        nomes = {c.id: c.nome for c in self.categoria_repo.listar()}
        return calcular_alteracoes([
            ("Data", formatar_data(atual.data), formatar_data(dados.data)),
            ("Categoria", nomes.get(atual.categoria_id, "—"), nomes.get(dados.categoria_id, "—")),
            ("Valor", formatar_moeda(atual.valor), formatar_moeda(dados.valor)),
            ("Descrição", atual.descricao, dados.descricao),
        ])

    def atualizar(self, despesa_id, dados):
        """Altera uma despesa. Quem lançou originalmente não muda; fica registrado quem editou."""
        dados = self.validar(dados, despesa_id=despesa_id)
        despesa = self._obter(despesa_id)
        despesa.data, despesa.descricao = dados.data, dados.descricao
        despesa.valor, despesa.categoria_id = dados.valor, dados.categoria_id
        despesa.atualizada_em, despesa.atualizada_por = _agora(), Sessao.usuario.id
        if not self.repo.atualizar(despesa):
            raise ErroNegocio("Despesa não encontrada.")
        return despesa

    def excluir(self, despesa_id):
        """Marca a despesa como excluída (some das consultas, mas fica no banco para auditoria)."""
        Sessao.exigir(PERMISSAO)
        self._obter(despesa_id)
        self.repo.excluir(despesa_id, Sessao.usuario.id, _agora())

    def buscar_por_id(self, despesa_id):
        Sessao.exigir(PERMISSAO)
        return self.repo.buscar_por_id(despesa_id)

    def listar(self, data_de=None, data_ate=None, categoria_id=None, termo=""):
        """Consulta por período (datas inclusivas), categoria e/ou trecho da descrição.

        Todos os filtros são opcionais e se combinam. Mais recentes primeiro.
        """
        Sessao.exigir(PERMISSAO)
        if data_de and data_ate and data_ate < data_de:
            raise ErroNegocio("No período, a data final deve ser igual ou posterior à inicial.")
        despesas = self.repo.listar(data_de, data_ate, categoria_id)
        texto = normalizar_texto((termo or "").strip())
        if texto:
            despesas = [d for d in despesas if texto in normalizar_texto(d.descricao)]
        return despesas

    def resumir(self, despesas):
        """Total, quantidade e divisão por categoria de uma lista já consultada."""
        Sessao.exigir(PERMISSAO)
        return regras.resumir(despesas, {c.id: c.nome for c in self.categoria_repo.listar()})

    def nomes_responsaveis(self, despesas):
        """{usuario_id: nome} de quem lançou ou editou as despesas informadas.

        Busca direto no repositório de usuários, pois listar usuários é restrito ao administrador.
        """
        Sessao.exigir(PERMISSAO)
        ids = {d.usuario_id for d in despesas} | {d.atualizada_por for d in despesas
                                                  if d.atualizada_por}
        nomes = {}
        for usuario_id in ids:
            usuario = self.usuario_repo.buscar_por_id(usuario_id)
            nomes[usuario_id] = usuario.nome if usuario else "—"
        return nomes

    # =============== internos ===============
    def _obter(self, despesa_id):
        despesa = self.repo.buscar_por_id(despesa_id)
        if despesa is None:
            raise ErroNegocio("Despesa não encontrada.")
        return despesa

    def _obter_categoria(self, categoria_id):
        categoria = self.categoria_repo.buscar_por_id(categoria_id)
        if categoria is None:
            raise ErroNegocio("Categoria não encontrada.")
        return categoria

    def _validar_nome_categoria(self, nome, ignorar_id=None):
        nome = " ".join((nome or "").split())          # tira espaços sobrando
        if len(nome) < CATEGORIA_MIN:
            raise ErroNegocio("Informe o nome da categoria.")
        if len(nome) > CATEGORIA_MAX:
            raise ErroNegocio(f"O nome deve ter no máximo {CATEGORIA_MAX} caracteres.")
        chave = normalizar_texto(nome)                 # 'manutencao' = 'Manutenção'
        for existente in self.categoria_repo.listar():
            if existente.id != ignorar_id and normalizar_texto(existente.nome) == chave:
                raise ErroNegocio("Já existe uma categoria com este nome.")
        return nome
