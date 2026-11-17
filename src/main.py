from database.conexao import inicializar_banco
from src.repositories.usuario_repository import UsuarioRepository
from src.utils.sessao import Sessao
from ui.app import App
from ui.telas.tela_login import TelaLogin


def pedir_login():
    """Abre a tela de login. Devolve o usuário, ou None se a janela foi fechada sem entrar."""
    login = TelaLogin()
    login.mainloop()
    return login.usuario_logado


def main():
    inicializar_banco()
    UsuarioRepository().garantir_admin()   # cria o admin inicial se não houver nenhum usuário

    while True:
        usuario = pedir_login()
        if usuario is None:
            break
        Sessao.iniciar(usuario)
        app = App()
        app.run()
        Sessao.encerrar()
        if not app.deslogou:   # fechou a janela: encerra; clicou em "Sair": volta ao login
            break


if __name__ == "__main__":
    main()
