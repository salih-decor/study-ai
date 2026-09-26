"""seed official levels and branches (data only, idempotent)

Revision ID: d5e6f7a8b9c0
Revises: c4f1a2b8d3e5
Create Date: 2026-09-27 00:00:00.000000

القائمة الرسمية المعتمدة (نصوص حرفية — لا تخمين):
- لا تمس بنية الجداول (أنشأتها c4f1a2b8d3e5).
- Idempotent: تتخطى أي صف موجود (حسب UNIQUE name / UNIQUE level+name).
- لا تمس subjects إطلاقًا — كل المواد الحالية تبقى NULL (عامة).
- ملاحظة: "علوم" (الأولى) كيان مختلف عن "علوم تجريبية" (الثانية/الثالثة).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'c4f1a2b8d3e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (المستوى, [الشعب]) — الترتيب للعرض فقط، والربط عبر level_id دائمًا
DATA: list[tuple[str, list[str]]] = [
    ("السنة الأولى ثانوي", [
        "آداب وفلسفة",
        "علوم",
    ]),
    ("السنة الثانية ثانوي", [
        "علوم تجريبية",
        "آداب وفلسفة",
        "رياضيات",
        "تقني رياضي",
        "تسيير واقتصاد",
        "لغات أجنبية",
    ]),
    ("السنة الثالثة ثانوي", [
        "علوم تجريبية",
        "آداب وفلسفة",
        "رياضيات",
        "تقني رياضي",
        "تسيير واقتصاد",
        "لغات أجنبية",
    ]),
]


def _level_id(conn, name: str):
    row = conn.execute(
        sa.text("SELECT id FROM levels WHERE name = :name"),
        {"name": name},
    ).first()
    return row[0] if row else None


def upgrade() -> None:
    conn = op.get_bind()
    for level_name, branch_names in DATA:
        level_id = _level_id(conn, level_name)
        if level_id is None:
            conn.execute(
                sa.text("INSERT INTO levels (name) VALUES (:name)"),
                {"name": level_name},
            )
            level_id = _level_id(conn, level_name)
        for branch_name in branch_names:
            exists = conn.execute(
                sa.text("SELECT id FROM branches WHERE level_id = :lid AND name = :name"),
                {"lid": level_id, "name": branch_name},
            ).first()
            if exists is None:
                conn.execute(
                    sa.text("INSERT INTO branches (level_id, name) VALUES (:lid, :name)"),
                    {"lid": level_id, "name": branch_name},
                )


def downgrade() -> None:
    conn = op.get_bind()
    for level_name, branch_names in DATA:
        for branch_name in branch_names:
            conn.execute(
                sa.text(
                    "DELETE FROM branches WHERE name = :bname AND level_id IN "
                    "(SELECT id FROM levels WHERE name = :lname)"
                ),
                {"bname": branch_name, "lname": level_name},
            )
    for level_name, _ in DATA:
        conn.execute(
            sa.text("DELETE FROM levels WHERE name = :name"),
            {"name": level_name},
        )
