import hashlib
from database.conexao import inserir, executar, consultar_um, consultar_todos
from src.models.usuario import Usuario

class UsuarioRepository:
    
    def _para_objeto(self, linha):
        """Converte uma linha do banco em um objeto Usuario."""
        if linha is None:
            return None
        return Usuario(
            id=linha["id"],
            nome=linha["nome"],
            email=linha["email"],
            senha=linha["senha"]
        )

    def _gerar_hash(self, senha: str) -> str:
        """Gera o hash SHA-256 da senha."""
        return hashlib.sha256(senha.encode()).hexdigest()

    def criar(self, usuario: Usuario):
        # Garante que a senha seja salva criptografada (hash)
        senha_criptografada = self._gerar_hash(usuario.senha)
        
        usuario.id = inserir(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            (usuario.nome, usuario.email, senha_criptografada),
        )
        return usuario

    def buscar_por_email(self, email: str):
        linha = consultar_um("SELECT * FROM usuarios WHERE email = ?", (email,))
        return self._para_objeto(linha)

    def validar_login(self, email: str, senha_digitada: str):
        usuario = self.buscar_por_email(email)
        if not usuario:
            return None
        
        # Compara o hash da senha digitada com o hash salvo no banco
        if usuario.senha == self._gerar_hash(senha_digitada):
            return usuario
        return None