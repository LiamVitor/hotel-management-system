"""Valores fixos usados pelos services e pela interface."""

TIPOS_QUARTO = ["Solteiro", "Casal", "Suíte", "Família"]

QUARTO_DISPONIVEL = "Disponível"
QUARTO_OCUPADO = "Ocupado"
QUARTO_RESERVADO = "Reservado"
QUARTO_MANUTENCAO = "Manutenção"
SITUACOES_QUARTO = [QUARTO_DISPONIVEL, QUARTO_OCUPADO, QUARTO_RESERVADO, QUARTO_MANUTENCAO]

RESERVA_CONFIRMADA = "Confirmada"
RESERVA_HOSPEDADA = "Hospedada"
RESERVA_FINALIZADA = "Finalizada"
RESERVA_CANCELADA = "Cancelada"
RESERVA_NO_SHOW = "Não compareceu"   # hóspede não apareceu (no-show)
SITUACOES_RESERVA = [RESERVA_CONFIRMADA, RESERVA_HOSPEDADA, RESERVA_FINALIZADA,
                     RESERVA_CANCELADA, RESERVA_NO_SHOW]

MOTIVO_CANCELAMENTO_MIN = 3
MOTIVO_CANCELAMENTO_MAX = 200

# Bloqueio de quarto: a situação é calculada pelas datas (não fica gravada no banco)
BLOQUEIO_AGENDADO = "Agendado"
BLOQUEIO_EM_ANDAMENTO = "Em andamento"
BLOQUEIO_ENCERRADO = "Encerrado"
MOTIVO_BLOQUEIO_MIN = 3
MOTIVO_BLOQUEIO_MAX = 200

FORMAS_PAGAMENTO = ["PIX", "Dinheiro", "Cartão de crédito", "Cartão de débito", "Transferência"]

PAGAMENTO_NORMAL = "Pagamento"
PAGAMENTO_REEMBOLSO = "Reembolso"

PAGTO_PENDENTE = "Pendente"    # nada pago
PAGTO_PARCIAL = "Parcial"      # pagou parte, ainda deve
PAGTO_PAGO = "Pago"            # quitada
PAGTO_CANCELADA = "Cancelada"  # reserva cancelada: não há saldo a cobrar
PAGTO_NO_SHOW = "Não compareceu"  # hóspede não veio: também não há saldo a cobrar

MOTIVO_REEMBOLSO_MIN = 3
MOTIVO_REEMBOLSO_MAX = 200
