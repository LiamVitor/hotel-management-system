from src.repositories.hospede_repository import HospedeRepository
from src.repositories.reserva_repository import ReservaRepository
from src.services.erros import ErroNegocio
from src.utils.alteracoes import calcular_alteracoes
from src.utils.filtros import normalizar_texto, parece_numerico
from src.utils.formatacao import apenas_digitos, formatar_cpf, formatar_telefone
from src.utils.sessao import Sessao
from src.utils.validacao import email_valido


class HospedeService:
    def __init__(self, repo=None, reserva_repo=None):
        self.repo = repo or HospedeRepository()
        self.reserva_repo = reserva_repo or ReservaRepository()

    def listar(self, termo=""):
        """Lista hóspedes em ordem alfabética.

        O termo é procurado no nome e no e-mail (sem diferenciar maiúsculas e acentos)
        e, quando só tem números/símbolos de CPF ou telefone, nos dígitos do CPF e do telefone.
        """
        hospedes = self.repo.listar()
        termo = (termo or "").strip()
        if not termo:
            return hospedes

        texto = normalizar_texto(termo)
        digitos = apenas_digitos(termo) if parece_numerico(termo) else ""
        encontrados = []
        for h in hospedes:
            if (texto in normalizar_texto(h.nome)
                    or texto in normalizar_texto(h.email or "")
                    or (digitos and (digitos in apenas_digitos(h.cpf)
                                     or digitos in apenas_digitos(h.telefone)))):
                encontrados.append(h)
        return encontrados

    def buscar_por_id(self, hospede_id):
        return self.repo.buscar_por_id(hospede_id)

    def validar(self, hospede):
        """Normaliza e valida os dados, sem gravar nada. Levanta ErroNegocio se algo estiver errado.

        CPF e telefone são guardados só com os dígitos; a máscara é só da interface.
        """
        Sessao.exigir("hospedes.salvar")
        hospede.nome = (hospede.nome or "").strip()
        hospede.cpf = apenas_digitos(hospede.cpf)
        hospede.telefone = apenas_digitos(hospede.telefone) or None
        hospede.email = (hospede.email or "").strip().lower() or None

        if not hospede.nome or not hospede.cpf:
            raise ErroNegocio("Informe o nome e o CPF.")
        if len(hospede.cpf) != 11:
            raise ErroNegocio("O CPF deve ter 11 dígitos.")
        if hospede.telefone and len(hospede.telefone) not in (10, 11):
            raise ErroNegocio("Telefone inválido. Informe o DDD e o número (10 ou 11 dígitos).")
        if hospede.email and not email_valido(hospede.email):
            raise ErroNegocio("E-mail inválido. Use o formato nome@dominio.com.")

        # compara só os dígitos, assim cadastros antigos (com pontos e traço) também contam
        for outro in self.repo.listar():
            if outro.id != hospede.id and apenas_digitos(outro.cpf) == hospede.cpf:
                raise ErroNegocio("Já existe um hóspede com este CPF.")

    def diferencas(self, hospede):
        """O que muda ao salvar este hóspede já validado (lista de Alteracao, vazia se nada mudou)."""
        atual = self.repo.buscar_por_id(hospede.id)
        if atual is None:
            raise ErroNegocio("Hóspede não encontrado.")
        return calcular_alteracoes([
            ("Nome", atual.nome, hospede.nome),
            ("CPF", formatar_cpf(atual.cpf), formatar_cpf(hospede.cpf)),
            ("Telefone", formatar_telefone(atual.telefone), formatar_telefone(hospede.telefone)),
            ("E-mail", atual.email, hospede.email),
        ])

    def salvar(self, hospede):
        """Cria (id vazio) ou atualiza um hóspede, aplicando as validações."""
        self.validar(hospede)
        if hospede.id is None:
            return self.repo.criar(hospede)
        self.repo.atualizar(hospede)
        return hospede

    def excluir(self, hospede_id):
        Sessao.exigir("hospedes.excluir")
        if self.reserva_repo.listar_por_hospede(hospede_id):
            raise ErroNegocio("Este hóspede possui reservas e não pode ser excluído.")
        self.repo.remover(hospede_id)
