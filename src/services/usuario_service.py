import re

from src.repositories.usuario_repository import UsuarioRepository
from src.services.erros import ErroNegocio, ErroPermissao
from src.utils.permissoes import ADMIN, PERFIS
from src.utils.sessao import Sessao

LOGIN_RE = re.compile(r"^[A-Za-z0-9_.-]{3,30}$")
TAMANHO_MINIMO_SENHA = 6


class UsuarioService:
    def __init__(self, repo=None):
        self.repo = repo or UsuarioRepository()

    # ---------- login ----------
    def autenticar(self, usuario, senha):
        """Devolve o usuário se login e senha conferem; None se não conferem.

        Levanta ErroNegocio se a senha estiver certa mas a conta estiver desativada.
        """
        encontrado = self.repo.validar_login(usuario, senha)
        if encontrado is None:
            return None
        if not encontrado.ativo:
            raise ErroNegocio("Este usuário está desativado. Procure um administrador.")
        return encontrado

    # ---------- administração (só perfil com usuarios.gerenciar) ----------
    def listar(self):
        Sessao.exigir("usuarios.gerenciar")
        return self.repo.listar()

    def buscar_por_id(self, usuario_id):
        Sessao.exigir("usuarios.gerenciar")
        return self.repo.buscar_por_id(usuario_id)

    def salvar(self, usuario, senha=None):
        """Cria (id vazio) ou atualiza um usuário. Ao editar, senha vazia mantém a atual."""
        Sessao.exigir("usuarios.gerenciar")
        usuario.nome = (usuario.nome or "").strip()
        usuario.usuario = (usuario.usuario or "").strip()
        if not usuario.nome:
            raise ErroNegocio("Informe o nome do usuário.")
        if not LOGIN_RE.match(usuario.usuario):
            raise ErroNegocio("O usuário deve ter de 3 a 30 caracteres: letras, números, "
                              "ponto, hífen ou sublinhado.")
        if usuario.perfil not in PERFIS:
            raise ErroNegocio("Selecione o perfil de acesso.")
        existente = self.repo.buscar_por_usuario(usuario.usuario)
        if existente is not None and existente.id != usuario.id:
            raise ErroNegocio("Já existe um usuário com este login.")

        if usuario.id is None:
            self._validar_senha(senha, obrigatoria=True)
            usuario.senha = senha
            return self.repo.criar(usuario)

        atual = self.repo.buscar_por_id(usuario.id)
        if atual is None:
            raise ErroNegocio("Usuário não encontrado.")
        self._validar_mudanca_de_acesso(atual, usuario.perfil, usuario.ativo)
        if senha:
            self._validar_senha(senha)
        self.repo.atualizar(usuario)
        if senha:
            self.repo.atualizar_senha(usuario.id, senha)
        self._atualizar_sessao(usuario)
        return usuario

    def definir_ativo(self, usuario_id, ativo):
        """Ativa ou desativa um usuário (em vez de apagar, para manter o histórico)."""
        Sessao.exigir("usuarios.gerenciar")
        atual = self.repo.buscar_por_id(usuario_id)
        if atual is None:
            raise ErroNegocio("Usuário não encontrado.")
        self._validar_mudanca_de_acesso(atual, atual.perfil, ativo)
        atual.ativo = ativo
        self.repo.atualizar(atual)

    # ---------- qualquer usuário logado ----------
    def alterar_propria_senha(self, senha_atual, nova_senha, confirmacao):
        logado = Sessao.usuario
        if logado is None:
            raise ErroPermissao("Faça login para continuar.")
        usuario = self.repo.buscar_por_id(logado.id)
        if usuario is None or not self.repo.conferir_senha(senha_atual or "", usuario.senha):
            raise ErroNegocio("A senha atual está incorreta.")
        if nova_senha != confirmacao:
            raise ErroNegocio("A nova senha e a confirmação não conferem.")
        self._validar_senha(nova_senha, obrigatoria=True)
        if nova_senha == senha_atual:
            raise ErroNegocio("A nova senha deve ser diferente da atual.")
        self.repo.atualizar_senha(usuario.id, nova_senha)

    # ---------- regras internas ----------
    @staticmethod
    def _validar_senha(senha, obrigatoria=False):
        if not senha:
            if obrigatoria:
                raise ErroNegocio("Informe uma senha.")
            return
        if len(senha) < TAMANHO_MINIMO_SENHA:
            raise ErroNegocio(f"A senha deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres.")

    def _validar_mudanca_de_acesso(self, atual, novo_perfil, novo_ativo):
        """Impede que o sistema fique sem administrador ou que alguém se tranque para fora."""
        mudou_acesso = novo_perfil != atual.perfil or novo_ativo != atual.ativo
        logado = Sessao.usuario
        if mudou_acesso and logado is not None and logado.id == atual.id:
            raise ErroNegocio("Você não pode alterar o seu próprio perfil nem desativar "
                              "a sua conta.")
        era_admin_ativo = atual.perfil == ADMIN and atual.ativo
        deixa_de_ser = novo_perfil != ADMIN or not novo_ativo
        if era_admin_ativo and deixa_de_ser and self.repo.contar_admins_ativos() <= 1:
            raise ErroNegocio("O sistema precisa de pelo menos um administrador ativo.")

    @staticmethod
    def _atualizar_sessao(usuario):
        logado = Sessao.usuario
        if logado is not None and logado.id == usuario.id:
            logado.nome, logado.usuario = usuario.nome, usuario.usuario

