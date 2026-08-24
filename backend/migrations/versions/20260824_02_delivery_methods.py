"""Add desk and home delivery pricing and order snapshots."""
from alembic import op
from sqlalchemy import inspect

revision = "20260824_02"
down_revision = "20260824_01"
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()
    tables = set(inspect(connection).get_table_names())
    if "products" in tables:
        columns = {column["name"] for column in inspect(connection).get_columns("products")}
        if "delivery_desk" not in columns:
            op.execute("ALTER TABLE products ADD COLUMN delivery_desk NUMERIC(12,2)")
        if "delivery_home" not in columns:
            op.execute("ALTER TABLE products ADD COLUMN delivery_home NUMERIC(12,2)")
        op.execute("UPDATE products SET delivery_desk = delivery WHERE delivery_desk IS NULL")
        op.execute("UPDATE products SET delivery_home = delivery WHERE delivery_home IS NULL")
    if "orders" in tables:
        columns = {column["name"] for column in inspect(connection).get_columns("orders")}
        if "delivery_method" not in columns:
            op.execute("ALTER TABLE orders ADD COLUMN delivery_method VARCHAR(20)")
        if "delivery_price" not in columns:
            op.execute("ALTER TABLE orders ADD COLUMN delivery_price NUMERIC(12,2)")

def downgrade():
    pass
