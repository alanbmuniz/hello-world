from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

try:
    import speech_recognition as sr
except Exception:  # speech_recognition opcional em alguns ambientes
    sr = None


def _validate_runtime() -> None:
    """
    Evita falhas opacas de provider de janela e orienta a correção do ambiente.
    """
    major, minor = sys.version_info[:2]
    if (major, minor) >= (3, 13):
        raise RuntimeError(
            "Versão de Python não suportada para esta build do Kivy. "
            "Use Python 3.10, 3.11 ou 3.12."
        )


KV = """
<FinanceRoot>:
    orientation: 'vertical'
    padding: dp(12)
    spacing: dp(8)

    BoxLayout:
        size_hint_y: None
        height: dp(40)
        spacing: dp(8)

        Label:
            text: 'Assistente Financeiro IA'
            bold: True
            font_size: '20sp'

    BoxLayout:
        size_hint_y: 0.45
        spacing: dp(8)

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(6)

            Label:
                text: 'Chat'
                size_hint_y: None
                height: dp(24)
                bold: True

            TextInput:
                id: chat_history
                text: root.chat_history
                readonly: True
                multiline: True

            TextInput:
                id: user_input
                hint_text: 'Pergunte sobre sua saúde financeira...'
                multiline: False
                size_hint_y: None
                height: dp(40)
                on_text_validate: root.send_chat()

            BoxLayout:
                size_hint_y: None
                height: dp(40)
                spacing: dp(8)
                Button:
                    text: 'Enviar'
                    on_release: root.send_chat()
                Button:
                    text: 'Falar (voz)'
                    on_release: root.capture_voice()

        BoxLayout:
            orientation: 'vertical'
            spacing: dp(6)

            Label:
                text: 'Novo registro financeiro'
                size_hint_y: None
                height: dp(24)
                bold: True

            TextInput:
                id: descricao
                hint_text: 'Descrição (ex: mercado, salário)'
                multiline: False

            Spinner:
                id: categoria
                text: 'Categoria'
                values: ['Moradia', 'Alimentação', 'Transporte', 'Saúde', 'Lazer', 'Renda', 'Outros']

            Spinner:
                id: tipo
                text: 'Tipo'
                values: ['despesa', 'renda']

            TextInput:
                id: valor
                hint_text: 'Valor (ex: 120.50)'
                multiline: False
                input_filter: 'float'

            Button:
                text: 'Adicionar registro'
                size_hint_y: None
                height: dp(40)
                on_release: root.add_entry()

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(6)

        Label:
            text: 'Análise rápida'
            size_hint_y: None
            height: dp(24)
            bold: True

        Label:
            text: root.health_summary
            halign: 'left'
            text_size: self.width, None

        BoxLayout:
            size_hint_y: None
            height: dp(40)
            spacing: dp(8)
            Button:
                text: 'Atualizar saúde financeira'
                on_release: root.refresh_health()
            Button:
                text: 'Gerar gráficos'
                on_release: root.generate_graphs()
"""


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
            return (
                f"Pode realizar gasto de R$ {amount:.2f}. "
                f"Saldo projetado: R$ {projected_balance:.2f}."
            )
        return (
            f"Melhor evitar gasto de R$ {amount:.2f}. "
            f"Saldo projetado (R$ {projected_balance:.2f}) ficaria abaixo da reserva de segurança "
            f"(R$ {reserve:.2f})."
        )

    def forecast(self, entries: List[Dict], months: int = 3) -> str:
        if not entries:
            return "Sem dados para projeção."

        income = sum(e["value"] for e in entries if e["kind"] == "renda")
        expenses = sum(e["value"] for e in entries if e["kind"] == "despesa")
        monthly_balance = income - expenses
        projections = [monthly_balance * m for m in range(1, months + 1)]
        projection_text = ", ".join(
            f"{i+1} mês(es): R$ {value:.2f}" for i, value in enumerate(projections)
        )
        return f"Projeção de saldo acumulado: {projection_text}."


class FinanceRoot(BoxLayout):
    chat_history = StringProperty("Olá! Eu sou seu assistente financeiro.\n")
    health_summary = StringProperty("Adicione seus registros para começar a análise.")

    data_file = Path("finance_data.json")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ai = FinancialAI()
        self.entries: List[Dict] = self.load_entries()
        Clock.schedule_once(lambda _: self.refresh_health(), 0.2)

    def load_entries(self) -> List[Dict]:
        if not self.data_file.exists():
            return []
        try:
            return json.loads(self.data_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []

    def persist_entries(self) -> None:
        self.data_file.write_text(json.dumps(self.entries, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_entry(self) -> None:
        desc = self.ids.descricao.text.strip()
        category = self.ids.categoria.text
        kind = self.ids.tipo.text
        raw_value = self.ids.valor.text.strip()

        if not desc or category == "Categoria" or kind == "Tipo" or not raw_value:
            self._popup("Dados incompletos", "Preencha descrição, categoria, tipo e valor.")
            return

        value = float(raw_value)
        self.entries.append(
            {
                "description": desc,
                "category": category,
                "kind": kind,
                "value": value,
                "date": dt.date.today().isoformat(),
            }
        )
        self.persist_entries()
        self.ids.descricao.text = ""
        self.ids.valor.text = ""
        self.refresh_health()
        self.chat_history += f"Usuário: registrei {kind} '{desc}' de R$ {value:.2f}.\n"
        self.chat_history += "IA: Registro salvo com sucesso.\n"

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
            if amount is None:
                answer = "Informe o valor da compra na pergunta, ex: 'Posso gastar 300?'."
            else:
                answer = self.ai.can_spend(amount, metrics)
        elif "proje" in lower or "futuro" in lower:
            answer = self.ai.forecast(self.entries, months=6)
        else:
            answer = (
                "Posso ajudar com: saúde financeira, decisão de compra (ex: 'posso gastar 500?') "
                "e projeção futura."
            )

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

        by_category = {}
        income = 0.0
        expenses = 0.0

        for e in self.entries:
            if e["kind"] == "despesa":
                by_category[e["category"]] = by_category.get(e["category"], 0.0) + e["value"]
                expenses += e["value"]
            else:
                income += e["value"]

        fig, axs = plt.subplots(1, 2, figsize=(10, 4))

        if by_category:
            axs[0].pie(by_category.values(), labels=by_category.keys(), autopct="%1.1f%%")
            axs[0].set_title("Despesas por categoria")
        else:
            axs[0].text(0.5, 0.5, "Sem despesas", ha="center", va="center")
            axs[0].set_title("Despesas por categoria")

        axs[1].bar(["Receita", "Despesa"], [income, expenses], color=["green", "red"])
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
        Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.35)).open()


class FinanceApp(App):
    def build(self):
        if Window is None:
            raise RuntimeError(
                "Kivy não encontrou um provider de janela. "
                "Instale dependências gráficas e tente novamente (ex.: pygame e libs SDL2)."
            )
        Window.minimum_width = 360
        Window.minimum_height = 640
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
            "3) execute: python app.py -d"
        )
