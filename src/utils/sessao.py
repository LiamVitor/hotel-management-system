"""Guarda quem está logado e confere permissões."""
from src.services.erros import ErroPermissao
from src.utils.permissoes import pode, rotulo_perfil


class Sessao:
    usuario = None   # objeto Usuario do login atual (None = ninguém logado)

    @classmethod
    def iniciar(cls, usuario):
        cls.usuario = usuario

    @classmethod
    def encerrar(cls):
        cls.usuario = None

    @classmethod
    def pode(cls, acao):
        return cls.usuario is not None and pode(cls.usuario.perfil, acao)

    @classmethod
    def exigir(cls, acao):
        """Levanta ErroPermissao se o usuário logado não puder fazer a ação."""
        if cls.usuario is None:
            raise ErroPermissao("Faça login para continuar.")
        if not pode(cls.usuario.perfil, acao):
            raise ErroPermissao(f"O perfil {rotulo_perfil(cls.usuario.perfil)} "
                                "não tem permissão para esta ação.")
