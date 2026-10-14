"""Формирование DOCX технологической карты по шаблону брендбука."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from app.core.config import settings
from app.shared.schemas import MaintenanceType

MAINTENANCE_LABELS_RU: dict[str, str] = {
    MaintenanceType.ANNUAL.value: "Годовое ТО",
    MaintenanceType.SEMI_ANNUAL.value: "Полугодовое ТО",
    MaintenanceType.QUARTERLY.value: "Квартальное ТО",
    MaintenanceType.MONTHLY.value: "Месячное ТО",
    MaintenanceType.WEEKLY.value: "Недельное ТО",
    MaintenanceType.DAILY.value: "Ежедневное ТО",
}

BRAND_PRIMARY = RGBColor(0x1A, 0x56, 0x8E)
REL_TEMPLATE_PATH = "templates/brandbook/tech_card_ru.docx"


def default_template_path() -> Path:
    return Path(settings.storage_local_path_resolved) / REL_TEMPLATE_PATH


def ensure_default_tech_card_template() -> Path:
    path = default_template_path()
    if path.is_file():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_template_file(path)
    return path


def _write_template_file(path: Path) -> None:
    """Корпоративный шаблон брендбука (базовая вёрстка Base To)."""
    doc = Document()
    title = doc.add_heading("Технологическая карта", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = BRAND_PRIMARY

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.LEFT
    meta.add_run("Оборудование: ").bold = True
    meta.add_run("{{EQUIPMENT_NAME}}")
    meta.add_run("\nВид ТО: ").bold = True
    meta.add_run("{{MAINTENANCE_TYPE}}")
    meta.add_run("\nНаименование: ").bold = True
    meta.add_run("{{TITLE}}")
    meta.add_run("\nДата: ").bold = True
    meta.add_run("{{GENERATED_AT}}")

    doc.add_heading("Перечень работ", level=1)
    table = doc.add_table(rows=1, cols=8)
    table.style = "Table Grid"
    headers = [
        "№",
        "Вид работ",
        "Место работ",
        "Описание работ",
        "Количество",
        "Инструменты",
        "Безопасность",
        "Контроль",
    ]
    for i, text in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = text
        for p in cell.paragraphs:
            for run in p.runs:
                run.bold = True
                run.font.size = Pt(10)

    doc.add_paragraph("{{WORK_ITEMS_TABLE}}")
    doc.add_paragraph("")
    footer = doc.add_paragraph("Документ сформирован системой Base To")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.save(str(path))


def build_sample_tech_card_template() -> bytes:
    """Образец DOCX-шаблона технологической карты с полями подстановки."""
    doc = Document()
    title = doc.add_heading(settings.APP_NAME, level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title.runs:
        run.font.color.rgb = BRAND_PRIMARY

    subtitle = doc.add_paragraph("Корпоративный бланк")
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph("{{GENERATED_AT}}").alignment = WD_ALIGN_PARAGRAPH.RIGHT

    heading = doc.add_heading("Технологическая карта", level=1)
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

    equipment = doc.add_paragraph()
    equipment.add_run("Оборудование: ").bold = True
    equipment.add_run("{{EQUIPMENT_NAME}}")

    name = doc.add_paragraph()
    name.add_run("Наименование: ").bold = True
    name.add_run("{{TITLE}}")

    kind = doc.add_paragraph()
    kind.add_run("Вид ТО: ").bold = True
    kind.add_run("{{MAINTENANCE_TYPE}}")

    doc.add_heading("Перечень работ", level=2)
    doc.add_paragraph("{{WORK_ITEMS_BLOCK}}")

    footer = doc.add_paragraph("Документ сформирован системой Base To")
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in footer.runs:
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def _work_items_plain(work_items: list[dict[str, Any]]) -> str:
    if not work_items:
        return "Не указаны"
    lines: list[str] = []
    for index, item in enumerate(work_items, start=1):
        order = item.get("order") or index
        description = str(item.get("description") or "—").strip()
        tools = ", ".join(item.get("tools") or []) or "—"
        safety = "; ".join(item.get("safety") or []) or "—"
        control = item.get("control_params") or {}
        control_text = "; ".join(f"{k}: {v}" for k, v in control.items()) if control else "—"
        lines.append(
            f"{order}. {description}. Вид работ: {item.get('work_type') or '—'}. "
            f"Место: {item.get('location') or '—'}. Количество: {item.get('quantity') or '—'}. "
            f"Инструменты: {tools}. Безопасность: {safety}. Контроль: {control_text}"
        )
    return "\n".join(lines)


def _unique_cells(row):
    seen: set[int] = set()
    cells = []
    for cell in row.cells:
        marker = id(cell._tc)
        if marker in seen:
            continue
        seen.add(marker)
        cells.append(cell)
    return cells


def _iter_tables(container):
    for table in container.tables:
        yield table
        seen: set[int] = set()
        for row in table.rows:
            for cell in row.cells:
                marker = id(cell._tc)
                if marker in seen:
                    continue
                seen.add(marker)
                yield from _iter_tables(cell)


def _norm(text: str) -> str:
    return " ".join((text or "").replace(":", " ").split()).lower()


def _item_fields(item: dict[str, Any], index: int) -> dict[str, str]:
    tools = ", ".join(item.get("tools") or [])
    safety = "; ".join(item.get("safety") or [])
    control = item.get("control_params") or {}
    control_text = "; ".join(f"{key}: {value}" for key, value in control.items()) if control else ""
    work_type = str(item.get("work_type") or "").strip()
    location = str(item.get("location") or "").strip()
    description = str(item.get("description") or "").strip()
    operation = ", ".join(part for part in (work_type, location) if part)
    return {
        "order": str(item.get("order") or index),
        "work_type": work_type,
        "location": location,
        "description": description,
        "operation": operation,
        "quantity": str(item.get("quantity") or "").strip(),
        "tools": tools,
        "safety": safety,
        "control": control_text,
    }


def _column_value(header: str, fields: dict[str, str], headers: list[str]) -> str | None:
    name = _norm(header)
    has_place = any("место" in _norm(item) for item in headers)
    has_safety = any("безопас" in _norm(item) for item in headers)
    if "№" in header or name in {"п/п", "n"} or name.startswith("п/п"):
        return fields["order"]
    if "место" in name:
        return fields["location"]
    if "вид работ" in name or "операц" in name:
        return fields["work_type"] if has_place else fields["operation"]
    if "содержан" in name or "описан" in name:
        return fields["description"]
    if "кол" in name or "колич" in name:
        return fields["quantity"]
    if "инструмент" in name or "техника" in name:
        return fields["tools"]
    if "безопас" in name:
        return fields["safety"]
    if "контрол" in name or "измер" in name or "показател" in name:
        return fields["control"]
    if "коммент" in name:
        return "" if has_safety else fields["safety"]
    if "продолж" in name or "материаль" in name or "трудо" in name or "владел" in name:
        return ""
    return None


def _is_work_table(table) -> bool:
    if len(table.rows) < 1 or len(table.columns) < 3:
        return False
    header_cells = _unique_cells(table.rows[0])
    if any(len(cell.text.strip()) > 80 for cell in header_cells):
        return False
    headers = " ".join(_norm(cell.text) for cell in header_cells)
    has_number = any("№" in cell.text or "п/п" in _norm(cell.text) for cell in header_cells)
    has_body = any(token in headers for token in ("содержан", "описан", "операц", "вид работ"))
    return has_number and has_body


def _fill_labeled_values(doc, values: dict[str, str]) -> None:
    for table in _iter_tables(doc):
        for row in table.rows:
            cells = _unique_cells(row)
            for index, cell in enumerate(cells[:-1]):
                label = _norm(cell.text)
                if label not in values or cells[index + 1].text.strip():
                    continue
                cells[index + 1].text = values[label]


def _fill_work_table(doc, work_items: list[dict[str, Any]]) -> bool:
    tables = [table for table in _iter_tables(doc) if _is_work_table(table)]
    if not tables:
        return False
    table = max(tables, key=lambda item: len(item.columns))
    headers = [cell.text for cell in _unique_cells(table.rows[0])]
    blank_rows = [
        row
        for row in table.rows[1:]
        if all(not cell.text.strip() for cell in _unique_cells(row))
    ]
    for index, item in enumerate(work_items, start=1):
        row = blank_rows.pop(0) if blank_rows else table.add_row()
        fields = _item_fields(item, index)
        for cell, header in zip(_unique_cells(row), headers):
            value = _column_value(header, fields, headers)
            if value is not None:
                cell.text = value
    return True


def _content_width_twips(doc) -> int:
    section = doc.sections[0]
    usable = int(section.page_width - section.left_margin - section.right_margin)
    return max(usable // 635, 1000)


def _scale_widths(values: list[int], target: int) -> list[int]:
    total = sum(values) or 1
    scaled = [max(int(value * target / total), 1) for value in values]
    drift = target - sum(scaled)
    index = 0
    guard = 0
    while drift != 0 and scaled and guard < 10000:
        step = 1 if drift > 0 else -1
        if scaled[index] + step >= 1:
            scaled[index] += step
            drift -= step
        index = (index + 1) % len(scaled)
        guard += 1
    return scaled


def _cell_is_empty(cell) -> bool:
    if cell.find(qn("w:tbl")) is not None:
        return False
    if any(True for _ in cell.iter(qn("w:drawing"))):
        return False
    text = "".join(node.text or "" for node in cell.iter(qn("w:t")))
    return not text.strip()


def _drop_empty_columns(table) -> None:
    rows = table.findall(qn("w:tr"))
    if not rows:
        return
    for row in rows:
        for cell in row.findall(qn("w:tc")):
            props = cell.find(qn("w:tcPr"))
            if props is None:
                continue
            if props.find(qn("w:gridSpan")) is not None or props.find(qn("w:vMerge")) is not None:
                return
    width = len(rows[0].findall(qn("w:tc")))
    if width < 2 or any(len(row.findall(qn("w:tc"))) != width for row in rows):
        return
    empty = [
        index
        for index in range(width)
        if all(_cell_is_empty(row.findall(qn("w:tc"))[index]) for row in rows)
    ]
    if not empty or len(empty) == width:
        return
    for row in rows:
        cells = row.findall(qn("w:tc"))
        for index in reversed(empty):
            row.remove(cells[index])
    grid = table.find(qn("w:tblGrid"))
    if grid is None:
        return
    columns = grid.findall(qn("w:gridCol"))
    if len(columns) != width:
        return
    for index in reversed(empty):
        grid.remove(columns[index])


def _column_widths(table) -> list[int]:
    grid = table.find(qn("w:tblGrid"))
    if grid is not None:
        widths = [int(column.get(qn("w:w")) or 0) for column in grid.findall(qn("w:gridCol"))]
        if widths and sum(widths) > 0:
            return widths
    row = table.find(qn("w:tr"))
    if row is None:
        return []
    return [1 for _ in row.findall(qn("w:tc"))]


def _set_fixed_width(table, widths: list[int]) -> None:
    props = table.find(qn("w:tblPr"))
    if props is None:
        props = OxmlElement("w:tblPr")
        table.insert(0, props)
    table_width = props.find(qn("w:tblW"))
    if table_width is None:
        table_width = OxmlElement("w:tblW")
        props.append(table_width)
    table_width.set(qn("w:type"), "dxa")
    table_width.set(qn("w:w"), str(sum(widths)))
    layout = props.find(qn("w:tblLayout"))
    if layout is None:
        layout = OxmlElement("w:tblLayout")
        props.append(layout)
    layout.set(qn("w:type"), "fixed")
    grid = table.find(qn("w:tblGrid"))
    if grid is None:
        grid = OxmlElement("w:tblGrid")
        props.addnext(grid)
    for column in list(grid.findall(qn("w:gridCol"))):
        grid.remove(column)
    for width in widths:
        column = OxmlElement("w:gridCol")
        column.set(qn("w:w"), str(width))
        grid.append(column)
    for row in table.findall(qn("w:tr")):
        index = 0
        for cell in row.findall(qn("w:tc")):
            cell_props = cell.find(qn("w:tcPr"))
            if cell_props is None:
                cell_props = OxmlElement("w:tcPr")
                cell.insert(0, cell_props)
            span_node = cell_props.find(qn("w:gridSpan"))
            span = int(span_node.get(qn("w:val")) or 1) if span_node is not None else 1
            width = sum(widths[index:index + span]) or 1
            index += span
            cell_width = cell_props.find(qn("w:tcW"))
            if cell_width is None:
                cell_width = OxmlElement("w:tcW")
                cell_props.append(cell_width)
            cell_width.set(qn("w:type"), "dxa")
            cell_width.set(qn("w:w"), str(width))
            no_wrap = cell_props.find(qn("w:noWrap"))
            if no_wrap is not None:
                cell_props.remove(no_wrap)


def _inner_width(table, cell, cell_width: int) -> int:
    left = right = 108

    def read(margin) -> tuple[int | None, int | None]:
        if margin is None:
            return None, None
        result = []
        for side in ("left", "right"):
            node = margin.find(qn(f"w:{side}"))
            if node is None or node.get(qn("w:type")) not in (None, "dxa"):
                result.append(None)
            else:
                result.append(int(node.get(qn("w:w")) or 0))
        return result[0], result[1]

    props = table.find(qn("w:tblPr"))
    table_left, table_right = read(props.find(qn("w:tblCellMar")) if props is not None else None)
    cell_props = cell.find(qn("w:tcPr"))
    cell_left, cell_right = read(cell_props.find(qn("w:tcMar")) if cell_props is not None else None)
    if table_left is not None:
        left = table_left
    if table_right is not None:
        right = table_right
    if cell_left is not None:
        left = cell_left
    if cell_right is not None:
        right = cell_right
    return max(cell_width - left - right, 200)


def _fit_table(table, available: int) -> None:
    _drop_empty_columns(table)
    widths = _column_widths(table)
    if not widths:
        return
    indent = 0
    props = table.find(qn("w:tblPr"))
    if props is not None:
        ind = props.find(qn("w:tblInd"))
        if ind is not None and ind.get(qn("w:type")) in (None, "dxa"):
            indent = int(ind.get(qn("w:w")) or 0)
    target = max(available - indent, len(widths))
    scaled = _scale_widths(widths, target)
    _set_fixed_width(table, scaled)
    for row in table.findall(qn("w:tr")):
        index = 0
        for cell in row.findall(qn("w:tc")):
            cell_props = cell.find(qn("w:tcPr"))
            span = 1
            if cell_props is not None and cell_props.find(qn("w:gridSpan")) is not None:
                span = int(cell_props.find(qn("w:gridSpan")).get(qn("w:val")) or 1)
            cell_width = sum(scaled[index:index + span])
            index += span
            inner = _inner_width(table, cell, cell_width)
            for nested in cell.findall(qn("w:tbl")):
                _fit_table(nested, inner)


def _fit_tables_to_page(doc) -> None:
    available = _content_width_twips(doc)
    for table in doc.tables:
        _fit_table(table._tbl, available)


def _render_from_template(
    template_path: Path,
    *,
    equipment_name: str,
    title: str,
    maintenance_type: str,
    work_items: list[dict[str, Any]],
) -> bytes:
    from docx import Document as DocxReader

    doc = DocxReader(str(template_path))
    maintenance_label = MAINTENANCE_LABELS_RU.get(maintenance_type, maintenance_type)
    filled = _fill_work_table(doc, work_items)
    _fill_labeled_values(
        doc,
        {
            "оборудование": equipment_name,
            "период то": maintenance_label,
            "вид то": maintenance_label,
            "наименование": title,
        },
    )
    replacements = {
        "{{EQUIPMENT_NAME}}": equipment_name,
        "{{MAINTENANCE_TYPE}}": maintenance_label,
        "{{TITLE}}": title,
        "{{GENERATED_AT}}": datetime.now(timezone.utc).strftime("%d.%m.%Y"),
        "{{WORK_ITEMS_TABLE}}": "",
        "{{WORK_ITEMS_BLOCK}}": "" if filled else _work_items_plain(work_items),
    }

    def _replace_paragraph(paragraph) -> None:
        for key, value in replacements.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, value)

    for paragraph in doc.paragraphs:
        _replace_paragraph(paragraph)
    for table in _iter_tables(doc):
        for row in table.rows:
            for cell in _unique_cells(row):
                for paragraph in cell.paragraphs:
                    _replace_paragraph(paragraph)

    _fit_tables_to_page(doc)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def render_tech_card_docx(
    template_path: Path,
    *,
    equipment_name: str,
    title: str,
    maintenance_type: str,
    work_items: list[dict[str, Any]],
) -> bytes:
    path = template_path if template_path.is_file() else ensure_default_tech_card_template()
    return _render_from_template(
        path,
        equipment_name=equipment_name,
        title=title,
        maintenance_type=maintenance_type,
        work_items=work_items,
    )
