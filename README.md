# Hotel Management System

> **README provisório**, escrito para a equipe de desenvolvimento.
> Ele explica como preparar, rodar e testar o projeto e será substituído pelo README final.

Sistema desktop de gerenciamento de hotel/pousada, feito em Python com CustomTkinter e SQLite.

## Requisitos

- Python 3.10 ou superior
- Git
- No Linux, instale também o Tkinter: `sudo apt install python3-tk` (no Windows e no macOS ele já vem com o Python)

## 1. Preparar o ambiente

```bash
git clone https://github.com/LiamVitor/hotel-management-system.git
cd hotel-management-system

python -m venv venv
```

Ative o ambiente virtual:

```powershell
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Windows (CMD)
venv\Scripts\activate.bat

# Linux / macOS
source venv/bin/activate
```

Quando ativar, aparece `(venv)` no início do terminal. Se o PowerShell bloquear o script, rode uma vez:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

Instale as dependências:

```bash
pip install -r requirements.txt
```

## 2. Rodar os testes

Sempre a partir da **raiz do projeto**:

```bash
python -m pytest
```

O resultado esperado é tudo verde (`passed`). Os testes usam um banco temporário, então **não** mexem no `data/hotel.db`.

## 3. Popular o banco com dados de exemplo (opcional)

```bash
python -m database.seed
```

Cria hóspedes, quartos e reservas de exemplo. Só roda se o banco estiver vazio. Sem isso, o app abre sem nenhum dado.

## 4. Rodar o app

```bash
python -m src.main
```

O banco é criado automaticamente em `data/hotel.db` na primeira execução.

> Use sempre `python -m ...` a partir da raiz do projeto. Rodar `python src/main.py` ou entrar em outra pasta causa `ModuleNotFoundError`.

## Recriar o banco do zero

Se o `schema.sql` mudar ou o banco ficar inconsistente, apague o arquivo e deixe o app recriar:

```bash
# Windows (PowerShell)
Remove-Item data\hotel.db
# Linux / macOS
rm data/hotel.db
```

Depois rode `python -m database.seed` se quiser os dados de exemplo de volta.

## Estrutura do projeto

```
hotel-management-system/
├── database/
│   ├── conexao.py        # conexão, transações e funções de consulta
│   ├── schema.sql        # criação das tabelas
│   └── seed.py           # dados de exemplo
├── data/                 # hotel.db (gerado, fora do Git)
├── src/
│   ├── main.py           # ponto de entrada
│   ├── models/           # Hospede, Quarto, Reserva
│   ├── repositories/     # acesso ao banco (um por tabela)
│   ├── services/         # regras de negócio
│   ├── utils/            # constantes e formatação
│   └── ui/               # interface (telas e componentes)
├── tests/
└── requirements.txt
```