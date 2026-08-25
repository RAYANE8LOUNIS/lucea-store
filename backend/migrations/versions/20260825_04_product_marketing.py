"""Add optional product marketing messages."""
from alembic import op
from sqlalchemy import inspect

revision = "20260825_04"
down_revision = "20260824_03"
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()
    if "products" not in set(inspect(connection).get_table_names()):
        return
    columns = {column["name"] for column in inspect(connection).get_columns("products")}
    if "marketing_badge" not in columns:
        op.execute("ALTER TABLE products ADD COLUMN marketing_badge VARCHAR(80)")
    if "urgency_text" not in columns:
        op.execute("ALTER TABLE products ADD COLUMN urgency_text VARCHAR(180)")

def downgrade():
    pass
