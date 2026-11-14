"""Popula o banco com dados de exemplo (só se ele estiver vazio).

Uso, na raiz do projeto:  python -m database.seed
"""
from datetime import date, datetime, time, timedelta

from database.conexao import inicializar_banco
from src.models.usuario import Usuario
from src.models.hospede import Hospede
from src.models.quarto import Quarto
from src.models.bloqueio_quarto import BloqueioQuarto
from src.models.despesa import Despesa
from src.models.pagamento import Pagamento
from src.models.reserva import Reserva
from src.repositories.usuario_repository import UsuarioRepository
from src.repositories.bloqueio_quarto_repository import BloqueioQuartoRepository
from src.repositories.hospede_repository import HospedeRepository
from src.repositories.quarto_repository import QuartoRepository
from src.models.caixa import SaldoInicial
from src.repositories.caixa_repository import CaixaRepository
from src.repositories.categoria_despesa_repository import CategoriaDespesaRepository
from src.repositories.despesa_repository import DespesaRepository
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
    (3, "301", -3, -1, "Não compareceu"),   # nunca chegou: marcada como no-show
]

# Horários REAIS de quem já fez check-in (e check-out). As datas de RESERVAS acima são as
# previstas: aqui alguns hóspedes chegam ou saem em outro dia ou horário.
# posição da reserva em RESERVAS -> (dias de atraso no check-in, hora, dias de atraso no check-out, hora)
HORARIOS_REAIS = {
    1: (0, "16:20", 0, "11:00"),
    3: (0, "15:05", 0, "11:00"),
    5: (0, "14:10", 0, "11:20"),
    6: (0, "13:40", 0, "10:30"),
    8: (1, "19:05", 0, "10:40"),     # chegou um dia depois do previsto
    9: (0, "13:30", 0, "14:20"),     # saiu depois do meio-dia
    10: (0, "15:45", 0, "11:15"),
}

# Cancelamentos e no-shows: quando aconteceu (dias a partir de hoje, hora), quem registrou e,
# no cancelamento, o motivo. posição em RESERVAS -> (dias, hora, usuário, motivo)
CANCELAMENTOS = {
    7: (-2, "10:20", "gerente", "Hóspede desistiu da viagem"),
}
NO_SHOWS = {
    11: (-2, "09:00", "recepcao"),    # marcado na manhã seguinte à data de entrada
}

# Vencimento combinado de algumas reservas (as demais vencem na data de entrada):
# posição em RESERVAS -> (dias a partir de hoje, quem definiu)
VENCIMENTOS = {
    4: (1, "gerente"),     # sinal pago; o restante fica combinado para o dia seguinte
    5: (-4, "recepcao"),   # finalizada, quitada
}

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

BLOQUEIOS = [  # quarto, dias até o início, hora, dias até o término, hora, quem registrou, motivo
    ("203", -30, "08:00", -28, "18:00", "admin", "Troca do ar-condicionado"),            # encerrado
    ("204", -3, "08:00", 4, "18:00", "gerente", "Reforma do banheiro"),                 # em andamento
    ("101", 20, "08:00", 22, "18:00", "gerente", "Dedetização e pintura do quarto"),    # agendado
]

SALDO_INICIAL_CAIXA = 15000.00   # vale desde 60 dias atrás, antes da primeira despesa de exemplo

DESPESAS = [  # dias atrás, categoria, descrição, valor, quem lançou
    (58, "Salários", "Folha de pagamento — setembro", 4200.00, "gerente"),
    (55, "Energia elétrica", "Conta de energia — setembro", 1280.40, "admin"),
    (52, "Água e esgoto", "Conta de água — setembro", 412.75, "admin"),
    (47, "Impostos e taxas", "Taxa de licença de funcionamento", 350.00, "admin"),
    (41, "Manutenção", "Conserto do ar-condicionado do quarto 103", 380.00, "gerente"),
    (33, "Alimentação", "Frutas, pães e frios do café da manhã", 296.90, "gerente"),
    (28, "Marketing", "Impulsionamento de anúncios", 150.00, "gerente"),
    (27, "Salários", "Folha de pagamento — outubro", 4200.00, "gerente"),
    (24, "Energia elétrica", "Conta de energia — outubro", 1195.10, "admin"),
    (22, "Lavanderia", "Lavagem de enxoval (lençóis e toalhas)", 240.00, "gerente"),
    (18, "Limpeza", "Produtos de limpeza e descartáveis", 187.35, "gerente"),
    (12, "Internet e telefone", "Plano de internet fibra", 129.90, "admin"),
    (9, "Alimentação", "Café, leite e açúcar", 84.50, "gerente"),
    (6, "Manutenção", "Troca de lâmpadas dos corredores", 96.00, "gerente"),
    (3, "Limpeza", "Reposição de papel higiênico e sabonete", 112.80, "gerente"),
    (1, "Outros", "Material de escritório", 58.00, "gerente"),
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
    recepcao, gerencia = repo_u.buscar_por_usuario("recepcao"), repo_u.buscar_por_usuario("gerente")
    reservas = []
    for indice, (pos, numero, ini, fim, situacao) in enumerate(RESERVAS):
        quarto = quartos[numero]
        entrada, saida = hoje + timedelta(days=ini), hoje + timedelta(days=fim)
        reais = {}
        if situacao in ("Hospedada", "Finalizada"):
            atraso_in, hora_in, atraso_out, hora_out = HORARIOS_REAIS[indice]
            reais = dict(checkin_em=datetime.combine(entrada + timedelta(days=atraso_in),
                                                     time.fromisoformat(hora_in)),
                         checkin_por=recepcao.id)
            if situacao == "Finalizada":
                reais.update(checkout_em=datetime.combine(saida + timedelta(days=atraso_out),
                                                          time.fromisoformat(hora_out)),
                             checkout_por=(gerencia if indice % 2 else recepcao).id)
        if indice in CANCELAMENTOS:
            dias, hora, quem, motivo = CANCELAMENTOS[indice]
            reais.update(cancelada_em=datetime.combine(hoje + timedelta(days=dias),
                                                       time.fromisoformat(hora)),
                         cancelada_por=repo_u.buscar_por_usuario(quem).id,
                         cancelamento_motivo=motivo)
        if indice in NO_SHOWS:
            dias, hora, quem = NO_SHOWS[indice]
            reais.update(noshow_em=datetime.combine(hoje + timedelta(days=dias),
                                                    time.fromisoformat(hora)),
                         noshow_por=repo_u.buscar_por_usuario(quem).id)
        if indice in VENCIMENTOS:
            dias, quem = VENCIMENTOS[indice]
            reais.update(data_vencimento=hoje + timedelta(days=dias),
                         vencimento_alterado_em=datetime.combine(min(entrada, hoje)
                                                                 - timedelta(days=4), time(11, 0)),
                         vencimento_alterado_por=repo_u.buscar_por_usuario(quem).id)
        reservas.append(repo_r.criar(Reserva(
            hospede_id=hospedes[pos].id, quarto_id=quarto.id,
            data_entrada=entrada, data_saida=saida,
            valor_diaria=quarto.preco_diaria,
            valor_total=(saida - entrada).days * quarto.preco_diaria,
            situacao=situacao,
            criada_em=datetime.combine(min(entrada, hoje) - timedelta(days=5), time(10, 0)),
            **reais)))

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

    # bloqueios de exemplo (histórico de manutenção): nenhum encosta nas reservas acima
    repo_b = BloqueioQuartoRepository()
    for numero, d_ini, h_ini, d_fim, h_fim, quem, motivo in BLOQUEIOS:
        inicio = datetime.combine(hoje + timedelta(days=d_ini), time.fromisoformat(h_ini))
        repo_b.criar(BloqueioQuarto(
            quarto_id=quartos[numero].id, inicio=inicio,
            fim=datetime.combine(hoje + timedelta(days=d_fim), time.fromisoformat(h_fim)),
            motivo=motivo, usuario_id=repo_u.buscar_por_usuario(quem).id,
            # registrado alguns dias antes de começar (e nunca depois de hoje)
            criado_em=datetime.combine(min(inicio.date(), hoje) - timedelta(days=3), time(8, 0))))

    # despesas de exemplo (as categorias já vêm criadas junto com o banco)
    categorias = {c.nome: c.id for c in CategoriaDespesaRepository().listar()}
    repo_d = DespesaRepository()
    for dias, categoria, descricao, valor, quem in DESPESAS:
        dia = hoje - timedelta(days=dias)
        repo_d.criar(Despesa(
            data=dia, descricao=descricao, valor=valor, categoria_id=categorias[categoria],
            usuario_id=repo_u.buscar_por_usuario(quem).id,
            criada_em=datetime.combine(dia, time(9, 0))))
    # saldo inicial do caixa: o que a pousada tinha no começo do período dos exemplos
    CaixaRepository().definir_saldo_inicial(SaldoInicial(
        valor=SALDO_INICIAL_CAIXA, data_referencia=hoje - timedelta(days=60),
        usuario_id=repo_u.buscar_por_usuario("admin").id,
        definido_em=datetime.combine(hoje - timedelta(days=60), time(8, 0))))
    print(f"Banco populado: {len(hospedes)} hóspedes, {len(quartos)} quartos, "
          f"{len(RESERVAS)} reservas, {len(PAGAMENTOS)} pagamentos, {len(REEMBOLSOS)} reembolso(s), "
          f"{len(BLOQUEIOS)} bloqueios, {len(DESPESAS)} despesas e {len(USUARIOS)} usuários.")


if __name__ == "__main__":
    popular()
