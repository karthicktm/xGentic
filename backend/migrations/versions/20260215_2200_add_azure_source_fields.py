"""Add agent_source and azure_foundry_agent_id to agents

Revision ID: 8b3c4d5e6f7a
Revises: 1af2e738728e
Create Date: 2026-02-15 22:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8b3c4d5e6f7a"
down_revision: Union[str, None] = "1af2e738728e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "agents",
        sa.Column(
            "agent_source",
            sa.String(length=50),
            nullable=False,
            server_default="local",
            comment="Origin: local or azure_foundry",
        ),
    )
    op.add_column(
        "agents",
        sa.Column(
            "azure_foundry_agent_id",
            sa.String(length=200),
            nullable=True,
            comment="External Azure Foundry agent ID for imported agents",
        ),
    )


def downgrade() -> None:
    op.drop_column("agents", "azure_foundry_agent_id")
    op.drop_column("agents", "agent_source")
