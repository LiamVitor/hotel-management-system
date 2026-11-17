class Usuario:
    def __init__(self, id=None, nome="", usuario="", senha="", perfil="recepcionista",
                 ativo=True):
        self.id = id
        self.nome = nome
        self.usuario = usuario
        self.senha = senha
        self.perfil = perfil
        self.ativo = ativo
