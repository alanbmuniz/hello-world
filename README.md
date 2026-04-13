# Assistente Financeiro IA (Python + Kivy)

Aplicativo em Python para **controle financeiro pessoal com IA**, com suporte a interação por **chat e voz**, avaliação de saúde financeira, simulação de gastos, projeções e geração de gráficos.

## Funcionalidades

- Chat inteligente para responder:
  - como está a saúde financeira;
  - se pode realizar um gasto específico;
  - projeções de compras e saldo futuro.
- Cadastro de receitas e despesas por categoria.
- Entrada por voz (quando microfone e dependências estiverem disponíveis).
- Geração de gráficos:
  - pizza de despesas por categoria;
  - barra de receita vs despesa.

## Stack

- **Kivy**: interface multiplataforma (Android/iOS/desktop).
- **Matplotlib**: gráficos financeiros.
- **SpeechRecognition**: transcrição de voz (opcional).

## Executar localmente

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
python app.py
```

## Compatibilidade com App Store (Apple) e Play Store (Google)

A base do app usa Kivy, que permite empacotar para Android e iOS.

### Android (Play Store)

Fluxo típico com **Buildozer**:

1. Instalar dependências do Buildozer e Android SDK/NDK.
2. Gerar configuração:
   ```bash
   buildozer init
   ```
3. Ajustar `buildozer.spec` (nome app, pacote, permissões de microfone etc.).
4. Build APK/AAB:
   ```bash
   buildozer android release
   ```
5. Assinar artefato final e publicar no Google Play Console.

### iOS (App Store)

Fluxo típico com **kivy-ios** (em macOS):

1. Instalar `kivy-ios` e toolchains Apple.
2. Criar projeto Xcode a partir do app Kivy.
3. Configurar permissões (microfone), assinatura/certificados e provisioning profile.
4. Gerar archive e enviar via Xcode para App Store Connect.

## Arquivos principais

- `app.py`: aplicação principal (UI, IA financeira e gráficos).
- `finance_data.json`: base local de lançamentos (gerado em runtime).
- `financial_dashboard.png`: imagem de gráficos (gerada sob demanda).

## Observações importantes

- A lógica de IA financeira no exemplo é local (regras e projeção simples), para facilitar MVP.
- Para IA generativa real (LLM), adicione integração de API (ex.: OpenAI) para respostas contextuais avançadas.
- Para produção mobile, validar desempenho, privacidade de dados e compliance das lojas.
