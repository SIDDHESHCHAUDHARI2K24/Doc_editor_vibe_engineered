"""seed demo users

Revision ID: d1af4929dffa
Revises: a7c89883aa89
Create Date: 2026-05-02 06:05:09.185852

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d1af4929dffa"
down_revision: Union[str, Sequence[str], None] = "a7c89883aa89"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO users (id, email, username, display_name, password_hash, created_at, updated_at)
        VALUES
            (gen_random_uuid(), 'alice@example.com', 'alice', 'Alice', '$2b$10$dufH0aba2O4ROzKA1uko1OPFLsHFBq/ykg990mbP.5mKfqzJ1gM1C', now(), now()),
            (gen_random_uuid(), 'bob@example.com', 'bob', 'Bob', '$2b$10$jycqy1G9BGcogJD4yfL75e3pJJtSLeJCMXMOpGKYzithrbyplxiT6', now(), now()),
            (gen_random_uuid(), 'carol@example.com', 'carol', 'Carol', '$2b$10$6dLwgjIVmdCFL.kaMrzE6OOCAyPppXLzeWvQHyeNQZi1wCYGp1wwy', now(), now()),
            (gen_random_uuid(), 'dan@example.com', 'dan', 'Dan', '$2b$10$k0PxW4EKSNCLAs4.7mlJBOhFN1YCTWHJnUBk98exbS8KE8gGATb4y', now(), now()),
            (gen_random_uuid(), 'erin@example.com', 'erin', 'Erin', '$2b$10$inj7ArjYzyq.rI/5cE/ud.zIwGTVH56BWuzJFGqc8xw5ne4C9trNi', now(), now())
        ON CONFLICT (email) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        "DELETE FROM users WHERE email IN ('alice@example.com', 'bob@example.com', 'carol@example.com', 'dan@example.com', 'erin@example.com')"
    )
