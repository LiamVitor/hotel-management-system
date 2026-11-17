"""Apoio para fechar janelas raiz do CustomTkinter sem mensagens de erro no terminal."""


def cancelar_agendamentos(janela):
    """Cancela os `after` pendentes da janela (os do Tk e os do CustomTkinter).

    Sem isso, ao fechar a janela eles ainda disparam e o terminal mostra
    'invalid command name ...update' e '...check_dpi_scaling'. Chamar antes de `destroy`.
    """
    for agendado in janela.tk.splitlist(janela.tk.call("after", "info")):
        try:
            janela.after_cancel(agendado)
        except Exception:
            pass
