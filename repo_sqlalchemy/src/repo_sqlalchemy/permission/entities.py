from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core_contracts.permission import models
from core_contracts.metainfo import get_metainfo

from repo_sqlalchemy.schema import Base, IntPK, BoolFlag, TBL


class Role(Base):
    __tablename__ = TBL.ROLE.value
    
    id: Mapped[IntPK]
    name: Mapped[str] = mapped_column(
        String(get_metainfo(models.Role, models.RoleFields.NAME).max_length)
    )
    description: Mapped[str] = mapped_column(
        String(get_metainfo(models.Role, models.RoleFields.DESCRIPTION).max_length)
    )


class ApplicationResource(Base):
    __tablename__ = TBL.APPLICATION_RESOURCE.value

    id: Mapped[IntPK]
    name: Mapped[str] = mapped_column(
        String(get_metainfo(models.ApplicationResource, models.ApplicationResourceFields.NAME).max_length)
    )
    description: Mapped[str] = mapped_column(
        String(get_metainfo(models.ApplicationResource, models.ApplicationResourceFields.DESCRIPTION).max_length)
    )


class RolesPermissions(Base):
    __tablename__ = TBL.ROLE_PERMISSION.value

    id: Mapped[IntPK]
    role_id: Mapped[int|None] = mapped_column(
        ForeignKey(f'{TBL.ROLE.value}.id')
        , index=True
        , nullable=True
    )
    resource_id: Mapped[int|None] = mapped_column(
        ForeignKey(f'{TBL.APPLICATION_RESOURCE.value}.id')
        , index=True
        , nullable=True
    )

    mode: Mapped[str|None] = mapped_column(String(6), nullable=True)
    allow_enumerate: Mapped[BoolFlag]
    allow_read: Mapped[BoolFlag]
    allow_create: Mapped[BoolFlag]
    allow_edit: Mapped[BoolFlag]
    allow_delete: Mapped[BoolFlag]
