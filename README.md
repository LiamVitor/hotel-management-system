# Hotel Management System

Sistema desktop de gestão para hotéis e pousadas, desenvolvido em **Python** com interface em **CustomTkinter** e banco de dados **SQLite**. Cobre o ciclo completo da hospedagem: cadastro de hóspedes e quartos, reservas, check-in/check-out, pagamentos, despesas, caixa e relatórios exportáveis em PDF e Excel.

> Projeto em grupo desenvolvido na faculdade, seguindo a metodologia RAD e organizado em etapas (planejamento, prototipação, MVP, iterações e produto final).

---

## Funcionalidades

### Operação
- **Início** – painel com indicadores, gráfico de barras e lista de alertas, com atalhos para as demais telas.
- **Hóspedes** – cadastro com máscara de CPF e telefone, validação de e-mail e pesquisa por nome, CPF, telefone ou e-mail.
- **Quartos** – cadastro por tipo (Solteiro, Casal, Suíte, Família), filtros por capacidade, faixa de valor (mínimo/máximo), situação e número. Inclui **bloqueio de quartos** por período (manutenção, por exemplo).
- **Reservas** – seletor de hóspede e quarto, calendário com digitação de data (`dd/mm/aaaa`), detalhes da reserva e controle de situação: *Confirmada, Hospedada, Finalizada, Cancelada* e *Não compareceu* (no-show).
- **Check-in / Check-out** – registra data, hora e usuário responsáveis pela operação real, mantendo separadas as datas previstas e as reais.
- **Histórico de hospedagem** – consulta das estadias anteriores de cada hóspede.

### Financeiro
- **Pagamentos** – pagamentos integrais, parciais e múltiplos por reserva (PIX, dinheiro, cartão de crédito/débito e transferência), com histórico preservado.
- **Reembolsos** – registrados sem apagar o pagamento original.
- **Cancelamento e no-show** – política de retenção configurável pela administração (dias de antecedência e percentuais retidos).
- **Despesas** – lançamento por categoria, com filtros por período e categoria.
- **Caixa** – movimentações de entrada e saída vindas de pagamentos, reembolsos e despesas, com saldo inicial configurável.
- **Contas a receber** – situação de cada reserva (Quitada, A vencer, Vencida) e controle de vencimento.

### Relatórios
Todos exportáveis em **PDF** e **Excel**, com cabeçalho padrão da pousada (nome e logotipo):

1. Ocupação (por dia e por quarto)
2. Reservas por período
3. Check-ins e check-outs
4. Demonstrativo de receitas
5. Demonstrativo financeiro
6. Contas a receber
7. Histórico de hospedagem
8. Cancelamentos e no-show

### Segurança e perfis
- Tela de login com usuário e senha; senhas armazenadas com **PBKDF2-HMAC-SHA256** e salt aleatório.
- Três perfis de acesso, com permissões centralizadas em `src/utils/permissoes.py`:

| Recurso | Recepcionista | Gerente | Administrador |
|---|:---:|:---:|:---:|
| Hóspedes | ✅ | ✅ | ✅ |
| Quartos e bloqueios | ✅ | ✅ | ✅ |
| Reservas, check-in e no-show | ✅ | ✅ | ✅ |
| Registrar pagamentos | ✅ | ✅ | ✅ |
| Excluir hóspedes/quartos, gerenciar bloqueios | ❌ | ✅ | ✅ |
| Cancelar reservas e reembolsar | ❌ | ✅ | ✅ |
| Despesas, caixa e relatórios | ❌ | ✅ | ✅ |
| Gerenciar usuários e política de retenção | ❌ | ❌ | ✅ |

O menu lateral mostra apenas as telas permitidas ao perfil logado.

---

## Arquitetura

O projeto é organizado em camadas, isolando o SQL da lógica de negócio e da interface:

```
hotel-management-system/
├── assets/                # Logotipo usado nos relatórios
├── database/
│   ├── conexao.py         # Conexão SQLite e funções utilitárias
│   ├── schema.sql         # Definição das tabelas
│   └── seed.py            # Dados de exemplo
├── src/
│   ├── main.py            # Ponto de entrada
│   ├── models/            # Entidades (Reserva, Hospede, Quarto, Pagamento...)
│   ├── repositories/      # Acesso a dados (Repository Pattern)
│   ├── services/          # Regras de negócio e exportação PDF/Excel
│   └── utils/             # Constantes, permissões, sessão, validação, formatação
├── ui/
│   ├── app.py             # Janela principal
│   ├── telas/             # Telas do sistema
│   ├── componentes/       # Componentes reutilizáveis (tabelas, painéis, janelas)
│   └── servicos.py        # Ponte entre a interface e os services
└── requirements.txt
```

**Fluxo:** `UI (telas)` → `services (regras)` → `repositories (SQL)` → `SQLite`

---

## Tecnologias

- [Python 3](https://www.python.org/)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) – interface gráfica
- SQLite (módulo `sqlite3` da biblioteca padrão) – banco de dados
- [openpyxl](https://openpyxl.readthedocs.io/) – exportação para Excel
- [ReportLab](https://www.reportlab.com/) – exportação para PDF

---

## Como executar

### Pré-requisitos
- Python 3.10 ou superior (o projeto foi desenvolvido com Python 3.14)
- Tkinter disponível na instalação do Python (já vem por padrão no Windows e no macOS; no Linux, instale `python3-tk`)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/LiamVitor/hotel-management-system.git
cd hotel-management-system

# 2. Crie e ative o ambiente virtual
python -m venv .venv
# Windows
venv\Scripts\activate.bat
# Linux / macOS
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. (Opcional) Popule o banco com dados de exemplo
python -m database.seed

# 5. Execute o sistema
python -m src.main
```

O banco de dados (`data/hotel.db`) é criado automaticamente na primeira execução.

### Acesso inicial

Se o banco estiver vazio, o sistema cria um administrador padrão:

| Usuário | Senha | Perfil |
|---|---|---|
| `admin` | `admin123` | Administrador |

Ao popular o banco com `python -m database.seed`, também são criados usuários de exemplo para os perfis **gerente** e **recepcionista** (veja a lista em `database/seed.py`).

>  **Troque a senha do administrador** (menu lateral → alterar senha) antes de usar o sistema com dados reais.

---

## Banco de dados

Principais tabelas definidas em `database/schema.sql`:

| Tabela | Descrição |
|---|---|
| `hospedes` | Dados dos hóspedes |
| `quartos` | Quartos, tipos, capacidade e valores |
| `reservas` | Reservas, datas previstas e reais, cancelamento |
| `usuarios` | Usuários, perfis e senhas com hash |
| `pagamentos` | Pagamentos e reembolsos ligados às reservas |
| `categorias_despesa` / `despesas` | Despesas da pousada por categoria |
| `bloqueios_quarto` | Períodos de bloqueio de quartos |
| `caixa_saldo_inicial` | Saldo inicial do caixa |
| `politica_retencao` | Regras de retenção em cancelamento e no-show |

---

## Personalização

O nome e o logotipo exibidos nos relatórios ficam em `src/utils/pousada.py`:

```python
NOME_POUSADA = "Pousada"
ARQUIVO_LOGO = ... / "assets" / "logo.png"
```

Para alterar o que cada perfil pode fazer, edite as listas em `src/utils/permissoes.py`.

---