class ErroNegocio(Exception):
    """Violação de regra de negócio. A mensagem já é própria para mostrar ao usuário."""


class ErroPermissao(ErroNegocio):
    """O perfil do usuário logado não pode fazer esta ação."""
