"""Popula o banco com dados de exemplo (só se ele estiver vazio).

Uso, na raiz do projeto:  python -m database.seed
"""
from datetime import date, datetime, time, timedelta

from database.conexao import inicializar_banco
from src.models.usuario import Usuario
from src.models.hospede import Hospede
from src.models.quarto import Quarto
from src.models.pagamento import Pagamento
from src.models.reserva import Reserva
from src.repositories.usuario_repository import UsuarioRepository
from src.repositories.hospede_repository import HospedeRepository
from src.repositories.quarto_repository import QuartoRepository
from src.repositories.pagamento_repository import PagamentoRepository
from src.repositories.reserva_repository import ReservaRepository

USUARIOS = [  # nome, usuário, senha, perfil
    ("Administrador", "admin", "admin123", "admin"),
    ("Marina Souza", "gerente", "1234123", "gerente"),
    ("Rafael Lima", "recepcao", "123123", "recepcionista"),
]

HOSPEDES = [
    ("Maria Silva Santos", "123.456.789-00", "(86) 99912-3456", "maria.silva@email.com"),
    ("João Pedro Almeida", "234.567.890-11", "(86) 98801-2233", "joao.almeida@email.com"),
    ("Ana Beatriz Costa", "345.678.901-22", "(86) 99655-4421", "ana.costa@email.com"),
    ("Carlos Eduardo Lima", "456.789.012-33", "(86) 98877-1020", "carlos.lima@email.com"),
    ("Fernanda Oliveira Rocha", "567.890.123-44", "(86) 99430-7788", "fernanda.rocha@email.com"),
    ("Ricardo Mendes Souza", "678.901.234-55", "(86) 98122-9090", "ricardo.souza@email.com"),
]

QUARTOS = [  # número, tipo, capacidade, diária, situação
    ("101", "Solteiro", 1, 120.0, "Disponível"),
    ("102", "Casal", 2, 180.0, "Reservado"),
    ("103", "Casal", 2, 180.0, "Ocupado"),
    ("201", "Suíte", 2, 280.0, "Ocupado"),
    ("202", "Família", 4, 350.0, "Reservado"),
    ("203", "Solteiro", 1, 120.0, "Disponível"),
    ("204", "Casal", 2, 190.0, "Manutenção"),
    ("301", "Suíte", 3, 320.0, "Disponível"),
]

RESERVAS = [  # hóspede (posição), quarto (número), dias até entrada, dias até saída, situação
    (0, "102", 0, 3, "Confirmada"),
    (1, "201", -2, 1, "Hospedada"),
    (2, "202", 0, 2, "Confirmada"),
    (3, "103", -1, 0, "Hospedada"),
    (4, "301", 2, 5, "Confirmada"),
    (5, "101", -5, -2, "Finalizada"),
    (0, "203", -10, -8, "Finalizada"),
    (1, "102", 10, 12, "Cancelada"),
    (2, "101", -12, -9, "Finalizada"),
    (3, "102", -4, -1, "Finalizada"),
    (4, "202", -6, -3, "Finalizada"),
]

PAGAMENTOS = [  # posição em RESERVAS, fração do total (None = o que falta), forma, dias a partir de hoje, hora
    (0, 0.3, "PIX", -1, "10:15"),                # sinal de uma reserva confirmada
    (1, 0.5, "PIX", -2, "14:05"),                # hospedado, pagou metade
    (3, 1.0, "Dinheiro", -1, "15:40"),           # hospedado, quitado
    (4, 0.2, "Cartão de crédito", -1, "11:20"),  # sinal
    (5, 0.5, "PIX", -5, "13:00"),                # finalizada paga em duas vezes
    (5, None, "Cartão de débito", -2, "11:30"),
    (6, 1.0, "Dinheiro", -10, "16:20"),
    (8, 1.0, "Cartão de crédito", -12, "09:45"),
    (9, 1.0, "PIX", -4, "12:10"),
    (10, 0.6, "Transferência", -6, "10:00"),     # finalizada paga em duas vezes
    (10, None, "PIX", -3, "11:00"),
    (7, 0.5, "PIX", -3, "16:00"),                # sinal da reserva que depois foi cancelada
]

REEMBOLSOS = [  # posição em RESERVAS, posição em PAGAMENTOS (ou None), valor, forma, dias, hora, motivo
    (7, 11, 100.0, "PIX", -2, "10:30", "Cancelamento da reserva (devolução parcial do sinal)"),
]


def popular():
    inicializar_banco()
    repo_h, repo_q, repo_r, repo_u = HospedeRepository(), QuartoRepository(), ReservaRepository(), UsuarioRepository()
    repo_p = PagamentoRepository()

    # usuários de exemplo: cria só os que ainda não existem (não duplica nem apaga nada)
    for nome, usuario, senha, perfil in USUARIOS:
        if repo_u.buscar_por_usuario(usuario) is None:
            repo_u.criar(Usuario(nome=nome, usuario=usuario, senha=senha, perfil=perfil))

    if repo_h.listar() or repo_q.listar() or repo_r.listar():
        print("O banco já tem dados. Nada foi alterado.")
        return

    hospedes = [repo_h.criar(Hospede(nome=n, cpf=c, telefone=t, email=e))
                for n, c, t, e in HOSPEDES]

    quartos = {numero: repo_q.criar(Quarto(numero=numero, tipo=tipo, capacidade=cap,
                                           preco_diaria=preco, situacao=situacao))
               for numero, tipo, cap, preco, situacao in QUARTOS}

    hoje = date.today()
    reservas = []
    for pos, numero, ini, fim, situacao in RESERVAS:
        quarto = quartos[numero]
        entrada, saida = hoje + timedelta(days=ini), hoje + timedelta(days=fim)
        reservas.append(repo_r.criar(Reserva(
            hospede_id=hospedes[pos].id, quarto_id=quarto.id,
            data_entrada=entrada, data_saida=saida,
            valor_diaria=quarto.preco_diaria,
            valor_total=(saida - entrada).days * quarto.preco_diaria,
            situacao=situacao)))

    # pagamentos de exemplo, lançados pelo administrador e pela recepção
    lancadores = [repo_u.buscar_por_usuario("admin"), repo_u.buscar_por_usuario("recepcao")]
    pago = {}
    criados = []                       # na ordem de PAGAMENTOS, usada pelos reembolsos
    for pos, fracao, forma, dias, hora in PAGAMENTOS:
        reserva = reservas[pos]
        valor = (round(reserva.valor_total * fracao, 2) if fracao is not None
                 else round(reserva.valor_total - pago.get(pos, 0.0), 2))
        pago[pos] = round(pago.get(pos, 0.0) + valor, 2)
        criados.append(repo_p.criar(Pagamento(
            reserva_id=reserva.id, valor=valor, forma=forma,
            usuario_id=lancadores[pos % 2].id,
            data_hora=datetime.combine(hoje + timedelta(days=dias), time.fromisoformat(hora)))))

    # reembolsos de exemplo, lançados pela gerência; o pagamento original continua no histórico
    gerente = repo_u.buscar_por_usuario("gerente")
    for pos, pos_pagamento, valor, forma, dias, hora, motivo in REEMBOLSOS:
        origem = criados[pos_pagamento] if pos_pagamento is not None else None
        repo_p.criar(Pagamento(
            reserva_id=reservas[pos].id, valor=valor, forma=forma, tipo="Reembolso", motivo=motivo,
            pagamento_origem_id=origem.id if origem else None, usuario_id=gerente.id,
            data_hora=datetime.combine(hoje + timedelta(days=dias), time.fromisoformat(hora))))
    print(f"Banco populado: {len(hospedes)} hóspedes, {len(quartos)} quartos, "
          f"{len(RESERVAS)} reservas, {len(PAGAMENTOS)} pagamentos, {len(REEMBOLSOS)} reembolso(s) "
          f"e {len(USUARIOS)} usuários.")


if __name__ == "__main__":
    popular()
