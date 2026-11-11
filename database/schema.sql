CREATE TABLE IF NOT EXISTS hospedes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nome      TEXT NOT NULL,
    cpf       TEXT NOT NULL UNIQUE,
    telefone  TEXT,
    email     TEXT
);

CREATE TABLE IF NOT EXISTS quartos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    numero        TEXT NOT NULL UNIQUE,
    tipo          TEXT NOT NULL,
    capacidade    INTEGER NOT NULL CHECK (capacidade > 0),
    preco_diaria  REAL NOT NULL CHECK (preco_diaria >= 0),
    situacao      TEXT NOT NULL DEFAULT 'Disponível'
                  CHECK (situacao IN ('Disponível', 'Ocupado', 'Reservado', 'Manutenção'))
);

CREATE TABLE IF NOT EXISTS reservas (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    hospede_id    INTEGER NOT NULL REFERENCES hospedes(id),
    quarto_id     INTEGER NOT NULL REFERENCES quartos(id),
    data_entrada  TEXT NOT NULL,
    data_saida    TEXT NOT NULL,
    valor_diaria  REAL NOT NULL,
    valor_total   REAL NOT NULL,
    situacao      TEXT NOT NULL DEFAULT 'Confirmada'
                  CHECK (situacao IN ('Confirmada', 'Hospedada', 'Finalizada', 'Cancelada',
                                      'Não compareceu')),
    -- quando a reserva foi lançada no sistema
    criada_em     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),   -- 'AAAA-MM-DD HH:MM:SS'
    -- data_entrada e data_saida são as datas PREVISTAS (não mudam). Os campos abaixo guardam
    -- o que realmente aconteceu: quando o hóspede entrou/saiu e quem fez a operação.
    checkin_em    TEXT,
    checkin_por   INTEGER REFERENCES usuarios(id),
    checkout_em   TEXT,
    checkout_por  INTEGER REFERENCES usuarios(id),
    -- cancelamento (situacao = 'Cancelada'): quando, quem cancelou e por quê
    cancelada_em        TEXT,
    cancelada_por       INTEGER REFERENCES usuarios(id),
    cancelamento_motivo TEXT,
    -- no-show (situacao = 'Não compareceu'): quando foi marcado e quem marcou
    noshow_em     TEXT,
    noshow_por    INTEGER REFERENCES usuarios(id),
    CHECK (data_saida > data_entrada)
);


CREATE TABLE IF NOT EXISTS usuarios (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    nome     TEXT NOT NULL,
    usuario  TEXT NOT NULL UNIQUE COLLATE NOCASE,
    senha    TEXT NOT NULL,
    perfil   TEXT NOT NULL DEFAULT 'recepcionista'
             CHECK (perfil IN ('admin', 'gerente', 'recepcionista')),
    ativo    INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
);


-- Cada linha é um lançamento financeiro de uma reserva: um pagamento do hóspede ou um
-- reembolso (devolução) a ele. Uma reserva pode ter vários. O histórico é preservado:
-- os gatilhos abaixo impedem alterar ou excluir qualquer lançamento.
CREATE TABLE IF NOT EXISTS pagamentos (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    reserva_id           INTEGER NOT NULL REFERENCES reservas(id) ON DELETE RESTRICT,
    data_hora            TEXT NOT NULL,                  -- 'AAAA-MM-DD HH:MM:SS'
    valor                REAL NOT NULL CHECK (valor > 0),
    forma                TEXT NOT NULL,                  -- PIX, Dinheiro, Cartão de crédito...
    tipo                 TEXT NOT NULL DEFAULT 'Pagamento'
                         CHECK (tipo IN ('Pagamento', 'Reembolso')),
    usuario_id           INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    motivo               TEXT,                           -- obrigatório nos reembolsos
    pagamento_origem_id  INTEGER REFERENCES pagamentos(id) ON DELETE RESTRICT
                                                         -- reembolso: pagamento devolvido (opcional)
);

CREATE INDEX IF NOT EXISTS idx_pagamentos_reserva ON pagamentos (reserva_id);

CREATE TRIGGER IF NOT EXISTS trg_pagamentos_nao_excluir
BEFORE DELETE ON pagamentos
BEGIN
    SELECT RAISE(ABORT, 'Lançamentos financeiros não podem ser excluídos.');
END;

CREATE TRIGGER IF NOT EXISTS trg_pagamentos_nao_alterar
BEFORE UPDATE ON pagamentos
BEGIN
    SELECT RAISE(ABORT, 'Lançamentos financeiros não podem ser alterados.');
END;


-- Categorias para classificar as despesas (manutenção, alimentação, limpeza, salários...).
-- Uma categoria nunca é apagada: se não for mais usada, é desativada (ativa = 0), assim
-- as despesas antigas continuam apontando para ela.
CREATE TABLE IF NOT EXISTS categorias_despesa (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    nome   TEXT NOT NULL UNIQUE COLLATE NOCASE,
    ativa  INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1))
);

-- Categorias iniciais: só entram quando a tabela está vazia, então renomear ou desativar
-- uma delas não faz a original voltar na próxima abertura do sistema.
INSERT INTO categorias_despesa (nome)
SELECT column1 FROM (VALUES
    ('Manutenção'), ('Alimentação'), ('Limpeza'), ('Salários'), ('Energia elétrica'),
    ('Água e esgoto'), ('Internet e telefone'), ('Impostos e taxas'), ('Lavanderia'),
    ('Marketing'), ('Outros')
)
WHERE NOT EXISTS (SELECT 1 FROM categorias_despesa);

-- Despesas da pousada. "data" é o dia da despesa; "criada_em" é quando foi lançada no
-- sistema e "usuario_id" quem lançou. Excluir é só marcar (excluida_em): a linha continua
-- no banco para auditoria, mas some das consultas e dos totais.
CREATE TABLE IF NOT EXISTS despesas (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    data           TEXT NOT NULL,                  -- 'AAAA-MM-DD'
    descricao      TEXT NOT NULL,
    valor          REAL NOT NULL CHECK (valor > 0),
    categoria_id   INTEGER NOT NULL REFERENCES categorias_despesa(id) ON DELETE RESTRICT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    criada_em      TEXT NOT NULL,                  -- 'AAAA-MM-DD HH:MM:SS'
    atualizada_em  TEXT,
    atualizada_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    excluida_em    TEXT,
    excluida_por   INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_despesas_data ON despesas (data);
CREATE INDEX IF NOT EXISTS idx_despesas_categoria ON despesas (categoria_id);

-- Períodos em que um quarto fica indisponível para hospedagem (manutenção, reforma...).
-- Cada linha é um registro do histórico: o bloqueio não é apagado, e a situação dele
-- (Agendado / Em andamento / Encerrado) é calculada pela data e hora de início e de término.
CREATE TABLE IF NOT EXISTS bloqueios_quarto (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    quarto_id   INTEGER NOT NULL REFERENCES quartos(id) ON DELETE RESTRICT,
    inicio      TEXT NOT NULL,                  -- 'AAAA-MM-DD HH:MM:SS'
    fim         TEXT NOT NULL,                  -- 'AAAA-MM-DD HH:MM:SS'
    motivo      TEXT NOT NULL,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,   -- quem registrou
    criado_em   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    CHECK (fim > inicio)
);

CREATE INDEX IF NOT EXISTS idx_bloqueios_quarto ON bloqueios_quarto (quarto_id, inicio);
