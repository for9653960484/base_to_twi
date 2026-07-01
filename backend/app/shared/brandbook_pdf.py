"""Формирование PDF технологической карты (корпоративный стиль брендбука)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fpdf import FPDF
from fpdf.fonts import FontFace

from app.shared.brandbook_export import MAINTENANCE_LABELS_RU

BRAND_RGB = (26, 86, 142)
MUTED_RGB = (102, 102, 102)


def _cyrillic_font_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "assets" / "fonts" / "DejaVuSans.ttf",
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(
        "Не найден шрифт с поддержкой кириллицы для PDF. "
        "Установите DejaVu Sans или используйте Windows."
    )


def _control_text(control: dict[str, Any]) -> str:
    if not control:
        return "—"
    return "; ".join(f"{k}: {v}" for k, v in control.items())


def render_tech_card_pdf(
    *,
    equipment_name: str,
    title: str,
    maintenance_type: str,
    work_items: list[dict[str, Any]],
) -> bytes:
    font_path = _cyrillic_font_path()
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.set_margins(15, 15, 15)
    pdf.add_font("Doc", "", str(font_path))
    pdf.add_page()

    pdf.set_text_color(*BRAND_RGB)
    pdf.set_font("Doc", size=16)
    pdf.cell(0, 10, "Технологическая карта", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Doc", size=10)
    for label, value in (
        ("Оборудование", equipment_name),
        ("Вид ТО", MAINTENANCE_LABELS_RU.get(maintenance_type, maintenance_type)),
        ("Наименование", title),
        ("Дата", datetime.now(timezone.utc).strftime("%d.%m.%Y")),
    ):
        pdf.cell(38, 6, f"{label}:", new_x="RIGHT", new_y="TOP")
        pdf.multi_cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(3)
    pdf.set_text_color(*BRAND_RGB)
    pdf.set_font("Doc", size=12)
    pdf.cell(0, 8, "Перечень работ", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Doc", size=8)

    col_widths = (10, 62, 38, 38, 32)
    with pdf.table(
        width=180,
        col_widths=col_widths,
        line_height=5,
        text_align="LEFT",
        headings_style=FontFace(fill_color=(240, 244, 248)),
    ) as table:
        header = table.row()
        for text in ("№", "Описание работ", "Инструменты", "Безопасность", "Контроль"):
            header.cell(text)
        for item in work_items:
            row = table.row()
            row.cell(str(item.get("order", "")))
            row.cell(str(item.get("description", "")))
            row.cell(", ".join(item.get("tools") or []) or "—")
            row.cell("; ".join(item.get("safety") or []) or "—")
            row.cell(_control_text(item.get("control_params") or {}))

    pdf.set_y(-15)
    pdf.set_text_color(*MUTED_RGB)
    pdf.set_font("Doc", size=8)
    pdf.cell(0, 8, "Документ сформирован системой Base To", align="C")

    return bytes(pdf.output())
