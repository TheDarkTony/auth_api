from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from core_contracts.identity import models
from core_contracts.metainfo import FieldMetaData, metainfo_int

from repo_sqlalchemy.schema import Base, IntPK, BoolFlag, TBL


_max_length_key = FieldMetaData.max_length.value


class Identity(Base):
    __tablename__ = TBL.IDENTITY.value

    id: Mapped[IntPK]
    fname: Mapped[str|None] = mapped_column(
        String(metainfo_int(models.Identity, models.IdentityFields.FNAME, _max_length_key))
        , nullable=True
    )
    lname: Mapped[str|None] = mapped_column(
        String(metainfo_int(models.Identity, models.IdentityFields.LNAME, _max_length_key))
        , nullable=True
    )
    email: Mapped[str] = mapped_column(
        String(metainfo_int(models.Identity, models.IdentityFields.EMAIL, _max_length_key))
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
        String(metainfo_int(models.UserSubject, models.UserFields.USERNAME, _max_length_key)),
        index=True,
        unique=True
    )
    pwd: Mapped[str] = mapped_column(
        String(metainfo_int(models.UserSubject, models.UserFields.PWD, _max_length_key))
    )
    email_2fa_enabled: Mapped[BoolFlag]
    deleted_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=False)
        , nullable=True
    )
