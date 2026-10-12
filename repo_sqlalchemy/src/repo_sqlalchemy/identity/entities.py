from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core_contracts.identity import models
from core_contracts.metainfo import get_metainfo

from repo_sqlalchemy.schema import Base, IntPK, BoolFlag, TBL


class Identity(Base):
    __tablename__ = TBL.IDENTITY.value

    id: Mapped[IntPK]
    fname: Mapped[str|None] = mapped_column(
        String(get_metainfo(models.IdentitySubject, models.IdentityFields.FNAME).max_length)
        , nullable=True
    )
    lname: Mapped[str|None] = mapped_column(
        String(get_metainfo(models.Identity, models.IdentityFields.LNAME).max_length)
        , nullable=True
    )
    email: Mapped[str] = mapped_column(
        String(get_metainfo(models.Identity, models.IdentityFields.EMAIL).max_length)
    )
    email_verified: Mapped[BoolFlag]
    created_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=False)
    )
    is_activated: Mapped[BoolFlag]


class User(Base):
    __tablename__ = TBL.USER.value

    id: Mapped[IntPK]
    identity_id: Mapped[int] = mapped_column(
        ForeignKey(f'{TBL.IDENTITY.value}.id'),
        index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey(f'{TBL.ROLE.value}.id'),
        index=True
    )
    username: Mapped[str] = mapped_column(
        String(get_metainfo(models.UserSubject, models.UserFields.USERNAME).max_length),
        index=True,
        unique=True
    )
    pwd: Mapped[str] = mapped_column(
        String(get_metainfo(models.UserSubject, models.UserFields.PWD).max_length)
    )
    email_2fa_enabled: Mapped[BoolFlag]
    deleted_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
        , nullable=True
    )
