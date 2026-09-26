"""add levels and branches tables + subject scope columns

Revision ID: c4f1a2b8d3e5
Revises: ed3b002797bb
Create Date: 2026-09-27 00:00:00.000000

المرحلة الأولى من نظام المستويات والشعب:
- جداول جديدة فارغة (levels / branches) — بلا أي بيانات seed.
- عمودا subjects.level_id / subjects.branch_id (nullable) — بلا أي تغيير سلوكي:
  NULL = محتوى عام يظهر للجميع (بما فيه كل المحتوى القديم).

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c4f1a2b8d3e5'
down_revision: Union[str, None] = 'ed3b002797bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'levels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_levels_name'),
    )
    with op.batch_alter_table('levels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_levels_id'), ['id'], unique=False)

    op.create_table(
        'branches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['level_id'], ['levels.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('level_id', 'name', name='uq_branches_level_name'),
    )
    with op.batch_alter_table('branches', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_branches_id'), ['id'], unique=False)
        batch_op.create_index(batch_op.f('ix_branches_level_id'), ['level_id'], unique=False)

    with op.batch_alter_table('subjects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('level_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('branch_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_subjects_level_id', 'levels', ['level_id'], ['id'], ondelete='SET NULL')
        batch_op.create_foreign_key('fk_subjects_branch_id', 'branches', ['branch_id'], ['id'], ondelete='SET NULL')
        batch_op.create_index(batch_op.f('ix_subjects_level_id'), ['level_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_subjects_branch_id'), ['branch_id'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('subjects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_subjects_branch_id'))
        batch_op.drop_index(batch_op.f('ix_subjects_level_id'))
        batch_op.drop_constraint('fk_subjects_branch_id', type_='foreignkey')
        batch_op.drop_constraint('fk_subjects_level_id', type_='foreignkey')
        batch_op.drop_column('branch_id')
        batch_op.drop_column('level_id')

    op.drop_table('branches')
    op.drop_table('levels')
