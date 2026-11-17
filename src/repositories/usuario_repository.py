import hashlib
import hmac
import os

from database.conexao import consultar_todos, consultar_um, executar, inserir
from src.models.usuario import Usuario
from src.utils.permissoes import ADMIN

ITERACOES = 200_000


class UsuarioRepository:
    def _para_objeto(self, linha):
        if linha is None:
            return None
        return Usuario(
            id=linha["id"],
            nome=linha["nome"],
            usuario=linha["usuario"],
            senha=linha["senha"],
            perfil=linha["perfil"],
            ativo=bool(linha["ativo"]),
        )

    def _gerar_hash(self, senha: str) -> str:
        """Gera 'salt$hash' com PBKDF2-HMAC-SHA256 e salt aleatório."""
        salt = os.urandom(16)
        h = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, ITERACOES)
        return f"{salt.hex()}${h.hex()}"

    def conferir_senha(self, senha_digitada: str, armazenado: str) -> bool:
        try:
            salt_hex, hash_hex = armazenado.split("$")
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        novo = hashlib.pbkdf2_hmac("sha256", senha_digitada.encode(), salt, ITERACOES)
        return hmac.compare_digest(novo.hex(), hash_hex)

    def criar(self, usuario: Usuario):
        usuario.senha = self._gerar_hash(usuario.senha)
        usuario.id = inserir(
            "INSERT INTO usuarios (nome, usuario, senha, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
            (usuario.nome, usuario.usuario.strip(), usuario.senha, usuario.perfil,
             1 if usuario.ativo else 0),
        )
        return usuario

    def listar(self):
        linhas = consultar_todos("SELECT * FROM usuarios ORDER BY nome COLLATE NOCASE")
        return [self._para_objeto(linha) for linha in linhas]

    def buscar_por_id(self, usuario_id):
        return self._para_objeto(
            consultar_um("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)))

    def buscar_por_usuario(self, usuario: str):
        linha = consultar_um("SELECT * FROM usuarios WHERE usuario = ?", (usuario.strip(),))
        return self._para_objeto(linha)

    def atualizar(self, usuario: Usuario):
        """Atualiza nome, login, perfil e situação (a senha tem método próprio)."""
        executar(
            "UPDATE usuarios SET nome = ?, usuario = ?, perfil = ?, ativo = ? WHERE id = ?",
            (usuario.nome, usuario.usuario.strip(), usuario.perfil,
             1 if usuario.ativo else 0, usuario.id),
        )

    def atualizar_senha(self, usuario_id, nova_senha: str):
        executar("UPDATE usuarios SET senha = ? WHERE id = ?",
                 (self._gerar_hash(nova_senha), usuario_id))

    def contar_admins_ativos(self):
        linha = consultar_um(
            "SELECT COUNT(*) AS total FROM usuarios WHERE perfil = ? AND ativo = 1", (ADMIN,))
        return linha["total"]

    def validar_login(self, usuario: str, senha_digitada: str):
        """Confere usuário e senha. Quem decide se o usuário ativo pode entrar é o service."""
        encontrado = self.buscar_por_usuario(usuario)
        if encontrado and self.conferir_senha(senha_digitada, encontrado.senha):
            return encontrado
        return None

    def garantir_admin(self):
        """Cria o administrador inicial se ainda não houver nenhum usuário."""
        if not consultar_um("SELECT 1 FROM usuarios LIMIT 1", ()):
            self.criar(Usuario(nome="Administrador", usuario="admin", senha="admin123",
                               perfil=ADMIN))
