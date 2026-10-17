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
                  CHECK (situacao IN ('Confirmada', 'Hospedada', 'Finalizada', 'Cancelada')),
    CHECK (data_saida > data_entrada)
);
