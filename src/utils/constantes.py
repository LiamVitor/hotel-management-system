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
SITUACOES_RESERVA = [RESERVA_CONFIRMADA, RESERVA_HOSPEDADA, RESERVA_FINALIZADA, RESERVA_CANCELADA]

FORMAS_PAGAMENTO = ["PIX", "Dinheiro", "Cartão de crédito", "Cartão de débito", "Transferência"]

PAGAMENTO_NORMAL = "Pagamento"
PAGAMENTO_REEMBOLSO = "Reembolso"

PAGTO_PENDENTE = "Pendente"
PAGTO_PARCIAL = "Parcial"
PAGTO_PAGO = "Pago"    
