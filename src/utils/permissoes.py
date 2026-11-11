"""Perfis de usuário e o que cada um pode fazer.

Para mudar o que um perfil pode, basta editar as listas abaixo: a interface e os
services consultam esta tabela (nada fica espalhado pelo código).
"""

ADMIN = "admin"
GERENTE = "gerente"
RECEPCIONISTA = "recepcionista"
PERFIS = [ADMIN, GERENTE, RECEPCIONISTA]

ROTULOS_PERFIL = {
    ADMIN: "Administrador",
    GERENTE: "Gerente",
    RECEPCIONISTA: "Recepcionista",
}

# Ações no formato "area.acao".
_RECEPCAO = frozenset({
    "hospedes.ver", "hospedes.salvar",
    "quartos.ver", "bloqueios.ver",
    "reservas.ver", "reservas.criar", "reservas.checkin", "reservas.noshow",
    "pagamentos.registrar",
})
_GERENCIA = _RECEPCAO | {
    "hospedes.excluir",
    "quartos.salvar", "quartos.excluir", "bloqueios.gerenciar",
    "reservas.cancelar",
    "pagamentos.reembolsar",
    "despesas.gerenciar",
    "relatorios.ver",
}
_ADMINISTRACAO = _GERENCIA | {"usuarios.gerenciar"}

PERMISSOES = {
    ADMIN: _ADMINISTRACAO,
    GERENTE: _GERENCIA,
    RECEPCIONISTA: _RECEPCAO,
}


def pode(perfil, acao):
    """True se o perfil tem permissão para a ação (perfil desconhecido nunca pode)."""
    return acao in PERMISSOES.get(perfil, frozenset())


def rotulo_perfil(perfil):
    return ROTULOS_PERFIL.get(perfil, perfil or "")
