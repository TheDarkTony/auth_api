"""populate_ident_tbl_

Revision ID: 57050f901a22
Revises: 9f48842fe720
Create Date: 2026-09-24 18:04:28.921099

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '57050f901a22'
down_revision: Union[str, Sequence[str], None] = '9f48842fe720'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
"""
insert into identities (fname, lname, email, email_verified, created_date, is_activated)
values 
('admin', 'root', 'admin@localhost', true, now(), true),
('tony', 'waiter', 'tony@localhost', true, now(), true),
('ivan1', 'ivanov1', 'test1@localhost', true, now(), true),
('ivan2', 'ivanov2', 'test2@localhost', true, now(), true),
('ivan3', 'ivanov3', 'test3@localhost', true, now(), true),
('ivan4', 'ivanov4', 'test4@localhost', true, now(), true),
('ivan5', 'ivanov5', 'test5@localhost', true, now(), true),
('ivan6', 'ivanov6', 'test6@localhost', true, now(), true),
('ivan7', 'ivanov7', 'test7@localhost', true, now(), true),
('ivan8', 'ivanov8', 'test8@localhost', true, now(), true),
('ivan9', 'ivanov9', 'test9@localhost', true, now(), true),
('ivan10', 'ivanov10', 'test10@localhost', true, now(), true),
('ivan11', 'ivanov11', 'test11@localhost', true, now(), true),
('ivan12', 'ivanov12', 'test12@localhost', true, now(), true),
('ivan13', 'ivanov13', 'test13@localhost', true, now(), true),
('ivan14', 'ivanov14', 'test14@localhost', true, now(), true),
('ivan15', 'ivanov15', 'test15@localhost', true, now(), true);

insert into users (identity_id, role_id, username, pwd, email_2fa_enabled, deleted_date)
select 
		i.id as identity_id, 
		u.role_id as role_id,
		i.email as username,
		u.pwd,
		u.email_2fa_enabled,
		u.deleted_date
	from identities i
	join (
		select * from (
			values 
			('admin@localhost', '$2b$10$FNw5M7XaSr5/dry6gBuK5..hpT5hIS9hIwVsTnZfuB.TzFzLzdHjO', false, 1, null::timestamp),
			('tony@localhost', '$2b$10$A4cuxOV6znIb1IoorAd1.O6KXHXQA3UkhNrHgyvDctX2uITijJEi6', false, 3, null::timestamp)
		) as u(username, pwd, email_2fa_enabled, role_id, deleted_date)
	
	) as u on i.email = u.username;
"""
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
"""
delete from users;
delete from identities;
"""
)
