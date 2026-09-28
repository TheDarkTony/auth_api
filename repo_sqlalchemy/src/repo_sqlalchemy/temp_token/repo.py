from datetime import datetime

from sqlalchemy import String, DateTime, Integer, select
from sqlalchemy.orm import Mapped, mapped_column

from core_contracts import issues
from core_contracts.metainfo import metainfo_int
from core_contracts.temp_token import models
from core_contracts.temp_token.repositories import ITempTokenRepository

from repo_sqlalchemy.schema import Base, TBL, Schema, IntPK, SeanceManager


_max_length_key = models.FieldMetaData.max_length.value


class TempToken(Base):
    __tablename__ = TBL.TEMP_TOKEN.value

    id: Mapped[IntPK]
    token: Mapped[str] = mapped_column(
        String(metainfo_int(models.TempToken, models.TempTokenFields.TOKEN, _max_length_key)),
        index=True,
        unique=True
    )
    type: Mapped[int|None] = mapped_column(Integer())
    expired_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    json_data: Mapped[str] = mapped_column(String())


class TempTokenRepository(Schema, ITempTokenRepository):

    def __init__(self, seance_manager: SeanceManager) -> None:
        super().__init__(seance_manager)

    def fetch_by_token(self, token: str) -> models.TempToken|None:
        
        stmt = select(TempToken).where(TempToken.token == token)
        seance = self._seance()
        entry:TempToken|None
        with seance.begin():
            entry = seance.scalar(stmt)

        if entry is None:
            return None

        return models.TempToken(entry.token, entry.type, entry.expired_at, entry.json_data)
        

    def add(self, token: models.TempToken) -> models.TempToken:
        record = TempToken(
            token=token.token,
            type=token.type,
            expired_at=token.expired_at,
            json_data=token.json_data
        )

        seance = self._seance()
        with seance.begin():
            seance.add(record)

        return token


    def edit(self, token: models.TempToken) -> models.TempToken:
        seance = self._seance()
        entry: TempToken|None = next(
            (obj for obj in seance.identity_map.values()
                if isinstance(obj, TempToken) and obj.token == token)
            ,None
        )

        with seance.begin():
            if entry is None:
                stmt = select(TempToken).where(TempToken.token == token.token)
                entry = seance.scalar(stmt)

            if entry is None:
                raise issues.NotFoundEntryIssue("Failed to update session token")

            entry.json_data = token.json_data
            entry.expired_at = token.expired_at
            entry.type = token.type
        
        return token
