from datetime import datetime

from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from repo_sqlalchemy.schema import Base, TBL, IntPK


class EventsLog(Base):
    __tablename__ = TBL.EVENTS_LOG.value

    id: Mapped[IntPK]
    level: Mapped[str] = mapped_column(String(10))
    correlation_id: Mapped[str] = mapped_column(String(100), nullable=True)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    message: Mapped[str] = mapped_column(String(5000), nullable=True)
    traceback: Mapped[str] = mapped_column(String(5000), nullable=True)
    demand_args: Mapped[str] = mapped_column(String(5000), nullable=True)
    application: Mapped[str] = mapped_column(String(50), nullable=True)

    