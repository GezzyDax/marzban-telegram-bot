"""Support multiple Telegram bindings per Marzban user"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4f3c3b59ce1b"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("users_marzban_username_key", type_="unique")
        batch_op.add_column(
            sa.Column("primary_user", sa.Boolean(), nullable=False, server_default=sa.true())
        )

    op.execute(sa.text("UPDATE users SET primary_user = TRUE"))
    op.alter_column(
        "users",
        "primary_user",
        existing_type=sa.Boolean(),
        server_default=None,
    )
    op.create_index(
        "ix_users_telegram_id_marzban_username",
        "users",
        ["telegram_id", "marzban_username"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_users_telegram_id_marzban_username", table_name="users")
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("primary_user")
        batch_op.create_unique_constraint("users_marzban_username_key", ["marzban_username"])
