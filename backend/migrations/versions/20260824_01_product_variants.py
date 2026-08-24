"""Add product galleries, variants, and order selections."""
from alembic import op
from sqlalchemy import inspect

revision = "20260824_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    connection = op.get_bind()
    tables = set(inspect(connection).get_table_names())
    if "products" in tables:
        columns = {column["name"] for column in inspect(connection).get_columns("products")}
        if "images_json" not in columns:
            op.execute("ALTER TABLE products ADD COLUMN images_json TEXT DEFAULT '[]' NOT NULL")
        if "colors_json" not in columns:
            op.execute("ALTER TABLE products ADD COLUMN colors_json TEXT DEFAULT '[]' NOT NULL")
        if "sizes_json" not in columns:
            op.execute("ALTER TABLE products ADD COLUMN sizes_json TEXT DEFAULT '[]' NOT NULL")
    if "orders" in tables:
        columns = {column["name"] for column in inspect(connection).get_columns("orders")}
        if "selected_color" not in columns:
            op.execute("ALTER TABLE orders ADD COLUMN selected_color VARCHAR(80)")
        if "selected_size" not in columns:
            op.execute("ALTER TABLE orders ADD COLUMN selected_size VARCHAR(80)")

def downgrade():
    pass
