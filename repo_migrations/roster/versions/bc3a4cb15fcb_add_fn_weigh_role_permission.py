"""add_fn_weigh_role_permission

Revision ID: bc3a4cb15fcb
Revises: 21a0446b79c9
Create Date: 2026-09-24 13:41:25.149330

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bc3a4cb15fcb'
down_revision: Union[str, Sequence[str], None] = '21a0446b79c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("""
    
    create function weigh_role_permission (_role_id int4, _resource_id int4, _mode varchar(6))
    returns int2
    language plpgsql
    as $$
    declare 
        __weight int2;
    
    begin
        __weight := 9999;
        if _role_id is not null and _resource_id is not null and _mode is not null then --specific
            __weight := 1;
        elsif _role_id is not null and _resource_id is not null and _mode is null then  --specific for all mode
            __weight := 2;
        elsif _role_id is not null and _resource_id is null and _mode is not null then  --role default
            __weight := 3;
        elsif _role_id is not null and _resource_id is null and _mode is null then      --role default for all mode
            __weight := 4;
        elsif _role_id is null and _resource_id is not null and _mode is not null then  --resource default
            __weight := 5;
        elsif _role_id is null and _resource_id is not null and _mode is null then      --resource default for all mode
            __weight := 6;
        end if;
    
        return __weight;
    end;
    $$
    
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP FUNCTION weigh_role_permission(INT, INT, VARCHAR);")
