from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core_contracts.permission import models
from core_contracts.metainfo import metainfo_int

from repo_sqlalchemy.schema import Base, IntPK, BoolFlag, TBL


_max_length_key = models.FieldMetaData.max_length.value

class Role(Base):
    __tablename__ = TBL.ROLE.value
    
    id: Mapped[IntPK]
    name: Mapped[str] = mapped_column(
        String(metainfo_int(models.Role, models.RoleFields.NAME, _max_length_key))
    )
    description: Mapped[str] = mapped_column(
        String(metainfo_int(models.Role, models.RoleFields.DESCRIPTION, _max_length_key))
    )


class ApplicationResource(Base):
    __tablename__ = TBL.APPLICATION_RESOURCE.value

    id: Mapped[IntPK]
    name: Mapped[str] = mapped_column(
        String(metainfo_int(models.ApplicationResource, models.ApplicationResourceFields.NAME, _max_length_key))
    )
    description: Mapped[str] = mapped_column(
        String(metainfo_int(models.ApplicationResource, models.ApplicationResourceFields.DESCRIPTION, _max_length_key))
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
