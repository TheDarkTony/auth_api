"""populate_db_with_init_data_

Revision ID: 9f48842fe720
Revises: bc3a4cb15fcb
Create Date: 2026-09-24 13:45:24.913852

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f48842fe720'
down_revision: Union[str, Sequence[str], None] = 'bc3a4cb15fcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Inserts init data of roles_permissions, application_resources and roles tables."""
    
    op.execute("""
insert into roles ("name", "description")
values 
('admin', 'a main administrator who handle system access'),
('cook', 'a cook is one who is responsible for food'),
('waiter', 'a waiter greets and serves customers'),
('customer', 'a customer is someone who buys services and goods');

insert into application_resources ("name", "description")
values
('roles_permissions', 'holds permissions for a role on application resources'),
('identities', 'holds info related to an identity'),
('users', 'holds info related to user for an ability of sign in'),

('menu', 'holds info about food'),
('orders', 'holds info about order');
""")

    op.execute("""
with cfg as (
    select 
        (select id from roles r where r."name" = 'admin') as admin_role_id,
        (select id from roles r where r."name" = 'cook') as cook_role_id,
        (select id from roles r where r."name" = 'waiter') as waiter_role_id,
        (select id from roles r where r."name" = 'customer') as customer_role_id,
        
        (select id from application_resources ar where ar."name" = 'roles_permissions') as roles_permissions_id,
        (select id from application_resources ar where ar."name" = 'identities') as identities_id,
        (select id from application_resources ar where ar."name" = 'users') as users_id,
        (select id from application_resources ar where ar."name" = 'menu') as menu_id,
        (select id from application_resources ar where ar."name" = 'orders') as orders_id
)


, data_cte as (
    select cfg.admin_role_id as role_id
    , null as resource_id
    , null as mode
    , true as allow_enumerate
    , true as allow_read
    , true as allow_create
    , true as allow_edit
    , true as allow_delete from cfg
    
    --permissions
    union select null, cfg.roles_permissions_id, null, false, false, false, false, false from cfg
    
    --identities
    union select null, cfg.identities_id, 'own', true, true, false, true, false from cfg
    union select null, cfg.identities_id, 'nonown', true, true, false, false, false from cfg
    
    --users
    union select null, cfg.users_id, 'own', true, true, false, true, true from cfg
    union select null, cfg.users_id, 'nonown', false, false, false, false, false from cfg
    
    --menu
    union select cfg.cook_role_id, cfg.menu_id, 'own', true, true, true, true, true from cfg
    union select null, cfg.menu_id, null, true, true, false, false, false from cfg
    
    --orders
    union select cfg.cook_role_id, cfg.orders_id, 'own', true, true, false, true, false from cfg
    union select null, cfg.orders_id, 'own', true, true, true, true, false from cfg
    union select cfg.cook_role_id, cfg.orders_id, 'nonown', true, true, false, false, false from cfg
    union select cfg.waiter_role_id, cfg.orders_id, 'nonown', true, true, false, true, false from cfg
    union select cfg.customer_role_id, cfg.orders_id, 'nonown', false, false, false, false, false from cfg

)
insert into roles_permissions ("role_id", "resource_id", "mode", "allow_enumerate", "allow_read", "allow_create", "allow_edit", "allow_delete")
select * from data_cte;
""")


def downgrade() -> None:
    """Deletes init data of roles_permissions, application_resources and roles tables."""
    op.execute("""
delete from roles_permissions;
delete from application_resources;
delete from users;
delete from identities;
delete from roles;
""")
