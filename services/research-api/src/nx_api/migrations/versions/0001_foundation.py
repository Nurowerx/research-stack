"""Initial immutable provenance and evaluation schema."""

from alembic import op
from nx_trace.db import Base, install_guards

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    Base.metadata.create_all(op.get_bind())
    install_guards(op.get_bind())


def downgrade():
    raise RuntimeError(
        "Destructive downgrade is disabled. Restore an explicit database backup instead."
    )
