"""adiciona quantidade_recebida em ordens_compra

Revision ID: b2f4d6c8e1a2
Revises: 9f46b60d39e1
Create Date: 2026-05-22 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b2f4d6c8e1a2"
down_revision: Union[str, Sequence[str], None] = "9f46b60d39e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "ordens_compra",
        sa.Column(
            "quantidade_recebida",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.alter_column("ordens_compra", "quantidade_recebida", server_default=None)


def downgrade() -> None:
    op.drop_column("ordens_compra", "quantidade_recebida")
