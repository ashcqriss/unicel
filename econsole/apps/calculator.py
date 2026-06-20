"""Calculator app: a live expression field with evaluation history."""

from __future__ import annotations

from typing import Any

from ..calc import CalcError, evaluate, format_result
from ..widgets import InputField, truncate
from .base import AppPane


class CalculatorApp(AppPane):
    app_name = "calculator"
    app_label = "Calculator"

    def __init__(self, pane_id: int = 0, context: Any = None, expression: str = ""):
        super().__init__(pane_id, context)
        self.field = InputField(expression, prompt="› ")
        self.history: list[tuple[str, str]] = []
        self.message = ""

    def status_hint(self) -> str:
        return "type expression · Enter=evaluate · Ctrl-U=clear"

    def handle_key(self, key: int) -> bool:
        if key == 21:  # Ctrl-U
            self.field.clear()
            self.message = ""
            return True
        action = self.field.handle_key(key)
        if action is None:
            return False
        kind, text = action
        if kind == "submit":
            self._evaluate(text)
        return True

    def _evaluate(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        try:
            result = format_result(evaluate(text))
            self.history.append((text, result))
            self.message = ""
            self.field.clear()
        except CalcError as exc:
            self.message = f"error: {exc}"

    def render_body(self, surface, focused: bool) -> None:
        surface.text(0, 0, "Expression", role="dim")
        self.field.render(surface, 1, focused=focused)
        surface.hline(2)
        if self.message:
            surface.text(3, 0, truncate(self.message, surface.width), role="error")

        start_row = 4
        capacity = surface.height - start_row
        if capacity > 0 and self.history:
            recent = self.history[-capacity:]
            for i, (expr, result) in enumerate(reversed(recent)):
                row = start_row + i
                line = f"{truncate(expr, surface.width - 12)} = {result}"
                surface.text(row, 0, truncate(line, surface.width),
                             role="text" if i == 0 else "dim")
