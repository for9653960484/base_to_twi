#!/usr/bin/env python3
"""Создать шаблон брендбука и согласованные технологические карты по всем видам ТО."""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.brandbook import BrandbookTemplate
from app.models.equipment import Equipment
from app.models.tech_card import TechCard
from app.shared.brandbook_export import REL_TEMPLATE_PATH, ensure_default_tech_card_template

MAINTENANCE_TYPES = (
    "daily",
    "weekly",
    "monthly",
    "quarterly",
    "semi_annual",
    "annual",
)

CARD_TEMPLATES: dict[str, dict] = {
    "daily": {
        "title": "Ежедневный осмотр",
        "work_items": [
            {
                "order": 1,
                "description": "Проверить отсутствие посторонних шумов и вибрации при работе",
                "tools": [],
                "safety": ["Не приближаться к движущимся частям"],
                "control_params": {},
            },
            {
                "order": 2,
                "description": "Убедиться в исправности аварийной остановки",
                "tools": [],
                "safety": ["Проверку выполнять без нагрузки"],
                "control_params": {"результат": "срабатывает"},
            },
        ],
    },
    "weekly": {
        "title": "Еженедельное обслуживание",
        "work_items": [
            {
                "order": 1,
                "description": "Очистить корпус и зону вокруг оборудования",
                "tools": ["ветошь", "пылесос"],
                "safety": ["Отключить питание при необходимости"],
                "control_params": {},
            },
        ],
    },
    "monthly": {
        "title": "Ежемесячный осмотр",
        "work_items": [
            {
                "order": 1,
                "description": "Визуальный осмотр корпуса, ограждений и маркировок",
                "tools": ["фонарь"],
                "safety": ["Убедиться в отсутствии персонала в зоне"],
                "control_params": {},
            },
            {
                "order": 2,
                "description": "Проверить уровень смазки в контрольных точках",
                "tools": ["щуп"],
                "safety": ["Использовать СИЗ"],
                "control_params": {"уровень": "между min и max"},
            },
        ],
    },
    "quarterly": {
        "title": "Квартальное техническое обслуживание",
        "work_items": [
            {
                "order": 1,
                "description": "Проверить состояние приводных ремней и цепей",
                "tools": ["набор ключей", "динамометр"],
                "safety": ["Блокировать пуск"],
                "control_params": {"натяжение": "по паспорту"},
            },
        ],
    },
    "semi_annual": {
        "title": "Полугодовое техническое обслуживание",
        "work_items": [
            {
                "order": 1,
                "description": "Проверить электрические соединения и заземление",
                "tools": ["мультиметр", "отвёртка"],
                "safety": ["Работы только квалифицированным персоналом"],
                "control_params": {"сопротивление": "≤ 4 Ом"},
            },
        ],
    },
    "annual": {
        "title": "Годовое техническое обслуживание",
        "work_items": [
            {
                "order": 1,
                "description": "Проверить крепления и затяжку резьбовых соединений",
                "tools": ["набор ключей", "динамометрический ключ"],
                "safety": ["Отключить питание перед началом работ"],
                "control_params": {"момент": "по паспорту"},
            },
            {
                "order": 2,
                "description": "Осмотреть износ подшипников и смазочные точки",
                "tools": ["фонарь", "смазка"],
                "safety": ["Использовать СИЗ"],
                "control_params": {},
            },
        ],
    },
}


async def main() -> int:
    template_file = ensure_default_tech_card_template()
    print(f"Template file: {template_file}")

    async with async_session_factory() as db:
        existing = await db.execute(
            select(BrandbookTemplate).where(
                BrandbookTemplate.template_type == "tech_card",
                BrandbookTemplate.is_active.is_(True),
            )
        )
        if not existing.scalar_one_or_none():
            db.add(
                BrandbookTemplate(
                    title="Технологическая карта (корпоративный шаблон)",
                    template_type="tech_card",
                    file_path=REL_TEMPLATE_PATH,
                    version=1,
                    is_active=True,
                )
            )
            print("  -> brandbook_templates: tech_card template registered")

        equipment_rows = (
            await db.execute(select(Equipment).order_by(Equipment.name))
        ).scalars().all()
        if not equipment_rows:
            print("No equipment in DB — skip sample tech cards")
            await db.commit()
            return 0

        created = 0
        for equipment in equipment_rows:
            for mtype in MAINTENANCE_TYPES:
                template = CARD_TEMPLATES[mtype]
                exists = await db.execute(
                    select(TechCard.id).where(
                        TechCard.equipment_id == equipment.id,
                        TechCard.maintenance_type == mtype,
                    )
                )
                if exists.scalar_one_or_none():
                    continue
                db.add(
                    TechCard(
                        equipment_id=equipment.id,
                        maintenance_type=mtype,
                        title=template["title"],
                        work_items=template["work_items"],
                        status="published",
                    )
                )
                created += 1
                print(f"  -> {equipment.name}: {template['title']}")

        await db.commit()
    print(f"Done. Created {created} tech cards.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
