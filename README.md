# Assistente Financeiro IA (Python + Kivy + MySQL)

Aplicativo em Python para **controle financeiro pessoal com IA**, com interação por **chat e voz**, análise da saúde financeira, projeções e armazenamento persistente no **MySQL**.

## Funcionalidades

- Chat para responder sobre:
  - saúde financeira;
  - decisão de gastos específicos;
  - projeções futuras.
- Cadastro de receitas e despesas por categoria.
- Entrada por voz (opcional).
- Gráficos de análise financeira.
- Persistência dos lançamentos em MySQL para manter histórico entre execuções.

## Stack

- **Kivy**: interface multiplataforma (Android/iOS/desktop).
- **MySQL**: persistência de dados financeiros.
- **Matplotlib**: gráficos.
- **SpeechRecognition**: voz opcional.

## Executar localmente

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python app.py
```

> Recomendado: **Python 3.10–3.12**.

## Configuração do MySQL (segura)

1. Crie banco e usuário com privilégios mínimos:

```sql
CREATE DATABASE finance_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'finance_app'@'%' IDENTIFIED BY 'SENHA_FORTE_AQUI';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX ON finance_ai.* TO 'finance_app'@'%';
FLUSH PRIVILEGES;
```

2. Defina variáveis de ambiente (não commitar senha no código):

```bash
export FINANCE_DB_HOST=127.0.0.1
export FINANCE_DB_PORT=3306
export FINANCE_DB_NAME=finance_ai
export FINANCE_DB_USER=finance_app
export FINANCE_DB_PASSWORD='SENHA_FORTE_AQUI'
export FINANCE_APP_USER='alan'
# opcional para TLS:
# export FINANCE_DB_SSL_CA=/caminho/ca.pem
```

3. Execute o app:

```bash
python app.py -d
```

A tabela `financial_entries` é criada automaticamente na primeira conexão.

## Segurança recomendada

- Use senha forte e usuário MySQL dedicado ao app.
- Não grave credenciais no código-fonte; use variáveis de ambiente.
- Habilite TLS (`FINANCE_DB_SSL_CA`) quando o banco estiver remoto.
- Faça backup periódico do banco.

## Compatibilidade com lojas (Play Store / App Store)

- **Android**: build com Buildozer.
- **iOS**: build com kivy-ios + Xcode.

## Troubleshooting (Kivy)

Se aparecer:
- `Unable to find any valuable Window provider`
- `ModuleNotFoundError: No module named 'pygame'`

Use Python 3.11 e reinstale dependências:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python app.py -d
```
