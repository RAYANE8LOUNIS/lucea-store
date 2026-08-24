"""Add recoverable order archive timestamps."""
from alembic import op
from sqlalchemy import inspect

revision = "20260824_03"
down_revision = "20260824_02"
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()
    if "orders" not in set(inspect(connection).get_table_names()):
        return
    columns = {column["name"] for column in inspect(connection).get_columns("orders")}
    if "archived_at" not in columns:
        op.execute("ALTER TABLE orders ADD COLUMN archived_at TIMESTAMP")

def downgrade():
    pass
