from __future__ import annotations

import datetime as dt
import os
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except Exception:  # mysql opcional em ambiente sem driver
    mysql = None
    MySQLError = Exception

try:
    import speech_recognition as sr
except Exception:  # speech_recognition opcional
    sr = None


def _validate_runtime() -> None:
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 13):
        raise RuntimeError(
            "Versão de Python não suportada para esta build do Kivy. "
            "Use Python 3.10, 3.11 ou 3.12."
        )


KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex

<FinanceRoot>:
    orientation: 'vertical'
    padding: dp(14)
    spacing: dp(10)

    canvas.before:
        Color:
            rgba: get_color_from_hex('#0F172A')
        Rectangle:
            pos: self.pos
            size: self.size

    BoxLayout:
        size_hint_y: None
        height: dp(54)
        padding: dp(12), 0
        canvas.before:
            Color:
                rgba: get_color_from_hex('#1E293B')
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]
        Label:
            text: '💸 Finance AI'
            color: get_color_from_hex('#F8FAFC')
            bold: True
            font_size: '22sp'

    BoxLayout:
        size_hint_y: 0.5
        spacing: dp(10)

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(8)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: get_color_from_hex('#1E293B')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12,]

            Label:
                text: 'Chat inteligente'
                color: get_color_from_hex('#38BDF8')
                size_hint_y: None
                height: dp(24)
                bold: True

            TextInput:
                id: chat_history
                text: root.chat_history
                readonly: True
                multiline: True
                background_color: get_color_from_hex('#0B1220')
                foreground_color: get_color_from_hex('#E2E8F0')
                cursor_color: get_color_from_hex('#E2E8F0')

            TextInput:
                id: user_input
                hint_text: 'Pergunte sobre saúde financeira, gastos ou projeções...'
                multiline: False
                size_hint_y: None
                height: dp(40)
                background_color: get_color_from_hex('#0B1220')
                foreground_color: get_color_from_hex('#E2E8F0')
                cursor_color: get_color_from_hex('#E2E8F0')
                hint_text_color: get_color_from_hex('#94A3B8')
                on_text_validate: root.send_chat()

            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: 'Enviar'
                    background_normal: ''
                    background_color: get_color_from_hex('#0EA5E9')
                    color: 1, 1, 1, 1
                    on_release: root.send_chat()
                Button:
                    text: 'Falar (voz)'
                    background_normal: ''
                    background_color: get_color_from_hex('#22C55E')
                    color: 1, 1, 1, 1
                    on_release: root.capture_voice()

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(8)
            padding: dp(10)
            canvas.before:
                Color:
                    rgba: get_color_from_hex('#1E293B')
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [12,]

            Label:
                text: 'Novo lançamento'
                color: get_color_from_hex('#F59E0B')
                size_hint_y: None
                height: dp(24)
                bold: True

            TextInput:
                id: descricao
                hint_text: 'Descrição (ex: mercado, salário)'
                multiline: False
                background_color: get_color_from_hex('#0B1220')
                foreground_color: get_color_from_hex('#E2E8F0')
                hint_text_color: get_color_from_hex('#94A3B8')

            Spinner:
                id: categoria
                text: 'Categoria'
                values: ['Moradia', 'Alimentação', 'Transporte', 'Saúde', 'Lazer', 'Renda', 'Outros']
                background_color: get_color_from_hex('#0B1220')
                color: get_color_from_hex('#E2E8F0')

            Spinner:
                id: tipo
                text: 'Tipo'
                values: ['despesa', 'renda']
                background_color: get_color_from_hex('#0B1220')
                color: get_color_from_hex('#E2E8F0')

            TextInput:
                id: valor
                hint_text: 'Valor (ex: 120.50)'
                multiline: False
                input_filter: 'float'
                background_color: get_color_from_hex('#0B1220')
                foreground_color: get_color_from_hex('#E2E8F0')
                hint_text_color: get_color_from_hex('#94A3B8')

            Button:
                text: 'Salvar no MySQL'
                size_hint_y: None
                height: dp(40)
                background_normal: ''
                background_color: get_color_from_hex('#F97316')
                color: 1, 1, 1, 1
                on_release: root.add_entry()

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(8)
        padding: dp(10)
        canvas.before:
            Color:
                rgba: get_color_from_hex('#1E293B')
            RoundedRectangle:
                pos: self.pos
                size: self.size
                radius: [12,]

        Label:
            text: 'Análise de saúde financeira'
            size_hint_y: None
            height: dp(24)
            color: get_color_from_hex('#A78BFA')
            bold: True

        Label:
            text: root.health_summary
            color: get_color_from_hex('#E2E8F0')
            halign: 'left'
            text_size: self.width, None

        Label:
            text: root.storage_summary
            color: get_color_from_hex('#94A3B8')
            halign: 'left'
            text_size: self.width, None

        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: 'Atualizar saúde financeira'
                background_normal: ''
                background_color: get_color_from_hex('#8B5CF6')
                color: 1, 1, 1, 1
                on_release: root.refresh_health()
            Button:
                text: 'Gerar gráficos'
                background_normal: ''
                background_color: get_color_from_hex('#14B8A6')
                color: 1, 1, 1, 1
                on_release: root.generate_graphs()
"""


@dataclass
class DBConfig:
    host: str = os.getenv("FINANCE_DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("FINANCE_DB_PORT", "3306"))
    database: str = os.getenv("FINANCE_DB_NAME", "finance_ai")
    user: str = os.getenv("FINANCE_DB_USER", "finance_app")
    password: str = os.getenv("FINANCE_DB_PASSWORD", "")
    app_user: str = os.getenv("FINANCE_APP_USER", "default_user")
    ssl_ca: str = os.getenv("FINANCE_DB_SSL_CA", "")


class DatabaseManager:
    def __init__(self, config: DBConfig):
        self.config = config
        self.connection = None

    def connect(self) -> None:
        if mysql is None:
            raise RuntimeError("mysql-connector-python não está instalado.")

        if not self.config.password:
            raise RuntimeError(
                "Defina FINANCE_DB_PASSWORD no ambiente para proteger credenciais de acesso ao banco."
            )

        options = {
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "user": self.config.user,
            "password": self.config.password,
            "autocommit": True,
        }
        if self.config.ssl_ca:
            options["ssl_ca"] = self.config.ssl_ca
            options["ssl_verify_cert"] = True

        self.connection = mysql.connector.connect(**options)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        query = """
        CREATE TABLE IF NOT EXISTS financial_entries (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            app_user VARCHAR(120) NOT NULL,
            description VARCHAR(255) NOT NULL,
            category VARCHAR(60) NOT NULL,
            kind ENUM('despesa','renda') NOT NULL,
            value DECIMAL(12,2) NOT NULL,
            entry_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_date (app_user, entry_date)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        with self.connection.cursor() as cursor:
            cursor.execute(query)

    def load_entries(self) -> List[Dict]:
        query = """
            SELECT description, category, kind, value, entry_date
            FROM financial_entries
            WHERE app_user = %s
            ORDER BY entry_date ASC, id ASC
        """
        with self.connection.cursor(dictionary=True) as cursor:
            cursor.execute(query, (self.config.app_user,))
            rows = cursor.fetchall()

        entries: List[Dict] = []
        for row in rows:
            entries.append(
                {
                    "description": row["description"],
                    "category": row["category"],
                    "kind": row["kind"],
                    "value": float(row["value"]),
                    "date": row["entry_date"].isoformat(),
                }
            )
        return entries

    def add_entry(self, entry: Dict) -> None:
        query = """
            INSERT INTO financial_entries (app_user, description, category, kind, value, entry_date)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            self.config.app_user,
            entry["description"],
            entry["category"],
            entry["kind"],
            Decimal(str(entry["value"])),
            entry["date"],
        )
        with self.connection.cursor() as cursor:
            cursor.execute(query, values)


class FinancialAI:
    def __init__(self, budget_safety_ratio: float = 0.2) -> None:
        self.budget_safety_ratio = budget_safety_ratio

    def evaluate_health(self, entries: List[Dict]) -> Tuple[str, Dict[str, float]]:
        income = sum(e["value"] for e in entries if e["kind"] == "renda")
        expenses = sum(e["value"] for e in entries if e["kind"] == "despesa")
        balance = income - expenses
        savings_rate = (balance / income) if income > 0 else -1.0

        if income <= 0:
            status = "Sem renda registrada: adicione entradas para análise confiável."
        elif savings_rate >= 0.2:
            status = "Saúde financeira boa ✅ (poupança >= 20%)."
        elif savings_rate >= 0.1:
            status = "Saúde financeira moderada ⚠️ (poupança entre 10% e 20%)."
        else:
            status = "Saúde financeira em risco ❌ (poupança < 10%)."

        return status, {
            "income": income,
            "expenses": expenses,
            "balance": balance,
            "savings_rate": savings_rate,
        }

    def can_spend(self, amount: float, metrics: Dict[str, float]) -> str:
        reserve = metrics["income"] * self.budget_safety_ratio
        projected_balance = metrics["balance"] - amount
        if projected_balance >= reserve:
            return f"Pode realizar gasto de R$ {amount:.2f}. Saldo projetado: R$ {projected_balance:.2f}."
        return (
            f"Melhor evitar gasto de R$ {amount:.2f}. Saldo projetado (R$ {projected_balance:.2f}) "
            f"ficaria abaixo da reserva de segurança (R$ {reserve:.2f})."
        )

    def forecast(self, entries: List[Dict], months: int = 3) -> str:
        if not entries:
            return "Sem dados para projeção."
        income = sum(e["value"] for e in entries if e["kind"] == "renda")
        expenses = sum(e["value"] for e in entries if e["kind"] == "despesa")
        monthly_balance = income - expenses
        projections = [monthly_balance * m for m in range(1, months + 1)]
        projection_text = ", ".join(f"{i + 1} mês(es): R$ {value:.2f}" for i, value in enumerate(projections))
        return f"Projeção de saldo acumulado: {projection_text}."


class FinanceRoot(BoxLayout):
    chat_history = StringProperty("Olá! Eu sou seu assistente financeiro.\n")
    health_summary = StringProperty("Adicione seus registros para começar a análise.")
    storage_summary = StringProperty("Conectando ao banco MySQL...")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai = FinancialAI()
        self.db = DatabaseManager(DBConfig())
        self.entries: List[Dict] = []
        Clock.schedule_once(lambda _: self.bootstrap_data(), 0.1)

    def bootstrap_data(self) -> None:
        try:
            self.db.connect()
            self.entries = self.db.load_entries()
            self.storage_summary = (
                f"Banco conectado em {self.db.config.host}:{self.db.config.port}/{self.db.config.database} "
                f"| usuário lógico: {self.db.config.app_user}"
            )
            self.chat_history += "IA: Dados carregados do MySQL com sucesso.\n"
        except (RuntimeError, MySQLError) as exc:
            self.storage_summary = f"Falha no MySQL: {exc}"
            self.chat_history += "IA: Não consegui conectar ao MySQL. Ajuste as variáveis FINANCE_DB_* e reinicie.\n"
        self.refresh_health()

    def add_entry(self) -> None:
        desc = self.ids.descricao.text.strip()
        category = self.ids.categoria.text
        kind = self.ids.tipo.text
        raw_value = self.ids.valor.text.strip()

        if not desc or category == "Categoria" or kind == "Tipo" or not raw_value:
            self._popup("Dados incompletos", "Preencha descrição, categoria, tipo e valor.")
            return

        entry = {
            "description": desc,
            "category": category,
            "kind": kind,
            "value": float(raw_value),
            "date": dt.date.today().isoformat(),
        }

        try:
            self.db.add_entry(entry)
            self.entries.append(entry)
            self.ids.descricao.text = ""
            self.ids.valor.text = ""
            self.refresh_health()
            self.chat_history += f"Usuário: registrei {kind} '{desc}' de R$ {entry['value']:.2f}.\n"
            self.chat_history += "IA: Registro salvo no MySQL com sucesso.\n"
        except (RuntimeError, MySQLError) as exc:
            self._popup("Erro ao salvar", f"Não foi possível salvar no MySQL: {exc}")

    def send_chat(self) -> None:
        prompt = self.ids.user_input.text.strip()
        if not prompt:
            return
        self.ids.user_input.text = ""
        self.chat_history += f"Usuário: {prompt}\n"

        status, metrics = self.ai.evaluate_health(self.entries)
        lower = prompt.lower()
        if "saúde" in lower or "como estou" in lower:
            answer = f"{status} Receita: R$ {metrics['income']:.2f}, despesas: R$ {metrics['expenses']:.2f}."
        elif "posso gastar" in lower or "comprar" in lower:
            amount = self._extract_amount(lower)
            answer = self.ai.can_spend(amount, metrics) if amount is not None else (
                "Informe o valor da compra na pergunta, ex: 'Posso gastar 300?'."
            )
        elif "proje" in lower or "futuro" in lower:
            answer = self.ai.forecast(self.entries, months=6)
        else:
            answer = "Posso ajudar com: saúde financeira, decisão de compra e projeção futura."

        self.chat_history += f"IA: {answer}\n"

    def capture_voice(self) -> None:
        if sr is None:
            self._popup("Voz indisponível", "Instale 'speechrecognition' para habilitar captação de voz.")
            return
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                self._popup("Captura de voz", "Fale agora por alguns segundos...")
                audio = recognizer.listen(source, timeout=4, phrase_time_limit=6)
                text = recognizer.recognize_google(audio, language="pt-BR")
                self.ids.user_input.text = text
                self.send_chat()
        except Exception as exc:
            self._popup("Erro de voz", f"Não foi possível captar áudio: {exc}")

    def refresh_health(self) -> None:
        status, metrics = self.ai.evaluate_health(self.entries)
        self.health_summary = (
            f"{status}\n"
            f"Receita: R$ {metrics['income']:.2f} | Despesas: R$ {metrics['expenses']:.2f} | "
            f"Saldo: R$ {metrics['balance']:.2f}"
        )

    def generate_graphs(self) -> None:
        if not self.entries:
            self._popup("Sem dados", "Adicione dados antes de gerar gráficos.")
            return

        by_category: Dict[str, float] = {}
        income = 0.0
        expenses = 0.0
        for item in self.entries:
            if item["kind"] == "despesa":
                by_category[item["category"]] = by_category.get(item["category"], 0.0) + item["value"]
                expenses += item["value"]
            else:
                income += item["value"]

        plt.style.use("seaborn-v0_8-darkgrid")
        fig, axs = plt.subplots(1, 2, figsize=(10, 4))
        if by_category:
            axs[0].pie(by_category.values(), labels=by_category.keys(), autopct="%1.1f%%")
        else:
            axs[0].text(0.5, 0.5, "Sem despesas", ha="center", va="center")
        axs[0].set_title("Despesas por categoria")

        axs[1].bar(["Receita", "Despesa"], [income, expenses], color=["#22c55e", "#ef4444"])
        axs[1].set_title("Receita x Despesa")
        axs[1].set_ylabel("R$")

        output = Path("financial_dashboard.png")
        plt.tight_layout()
        plt.savefig(output)
        plt.close(fig)
        self._popup("Gráfico gerado", f"Gráficos salvos em: {output.resolve()}")

    @staticmethod
    def _extract_amount(text: str) -> float | None:
        token = "".join(ch if (ch.isdigit() or ch in ",.") else " " for ch in text).split()
        if not token:
            return None
        try:
            return float(token[0].replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _popup(title: str, message: str) -> None:
        Popup(title=title, content=Label(text=message), size_hint=(0.84, 0.36)).open()


class FinanceApp(App):
    def build(self):
        if Window is None:
            raise RuntimeError(
                "Kivy não encontrou um provider de janela. "
                "Instale dependências gráficas e tente novamente (ex.: pygame e libs SDL2)."
            )
        Window.minimum_width = 380
        Window.minimum_height = 680
        Builder.load_string(KV)
        return FinanceRoot()


if __name__ == "__main__":
    try:
        _validate_runtime()
        FinanceApp().run()
    except RuntimeError as exc:
        print(f"Erro de ambiente: {exc}")
        print(
            "Sugestão rápida:\n"
            "1) recrie o ambiente com Python 3.11;\n"
            "2) pip install -r requirements.txt;\n"
            "3) configure variáveis FINANCE_DB_*;\n"
            "4) execute: python app.py -d"
        )
