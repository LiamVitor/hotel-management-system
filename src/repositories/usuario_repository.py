import hashlib
import hmac
import os

from database.conexao import inserir, consultar_um
from src.models.usuario import Usuario

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
        )

    def _gerar_hash(self, senha: str) -> str:
        """Gera 'salt$hash' com PBKDF2-HMAC-SHA256 e salt aleatório."""
        salt = os.urandom(16)
        h = hashlib.pbkdf2_hmac("sha256", senha.encode(), salt, ITERACOES)
        return f"{salt.hex()}${h.hex()}"

    def _conferir_senha(self, senha_digitada: str, armazenado: str) -> bool:
        try:
            salt_hex, hash_hex = armazenado.split("$")
            salt = bytes.fromhex(salt_hex)
        except ValueError:
            return False
        novo = hashlib.pbkdf2_hmac("sha256", senha_digitada.encode(), salt, ITERACOES)
        return hmac.compare_digest(novo.hex(), hash_hex)

    def criar(self, usuario: Usuario):
        usuario.id = inserir(
            "INSERT INTO usuarios (nome, usuario, senha) VALUES (?, ?, ?)",
            (usuario.nome, usuario.usuario.strip(), self._gerar_hash(usuario.senha)),
        )
        return usuario

    def buscar_por_usuario(self, usuario: str):
        linha = consultar_um("SELECT * FROM usuarios WHERE usuario = ?", (usuario.strip(),))
        return self._para_objeto(linha)

    def validar_login(self, usuario: str, senha_digitada: str):
        encontrado = self.buscar_por_usuario(usuario)
        if encontrado and self._conferir_senha(senha_digitada, encontrado.senha):
            return encontrado
        return None

    def garantir_admin(self):
        """Cria um usuário inicial se a tabela estiver vazia."""
        if not consultar_um("SELECT 1 FROM usuarios LIMIT 1", ()):
            self.criar(Usuario(id=None, nome="Administrador", usuario="admin", senha="admin123"))