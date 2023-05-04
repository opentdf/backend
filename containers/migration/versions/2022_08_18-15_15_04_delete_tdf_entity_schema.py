"""delete tdf_entity schema

Revision ID: ecd8960bcf9d
Revises: f17c4bf35497
Create Date: 2022-08-18 15:15:04.712081

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ecd8960bcf9d"
down_revision = "f17c4bf35497"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("DROP TABLE IF EXISTS tdf_entity")
    op.execute("DROP ROLE IF EXISTS tdf_entity_manager")
    op.execute("DROP ROLE IF EXISTS tdf_entity_manager")
    op.execute("DROP SCHEMA IF EXISTS tdf_entity CASCADE")


def downgrade():
    pass
