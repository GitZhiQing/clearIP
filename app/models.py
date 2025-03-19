from sqlalchemy import BigInteger, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class IPData(db.Model):
    __tablename__ = "ip_data"
    id: Mapped[int] = mapped_column(primary_key=True)
    ip_start_num: Mapped[int] = mapped_column(BigInteger, index=True)
    ip_end_num: Mapped[int] = mapped_column(BigInteger, index=True)
    location: Mapped[str] = mapped_column(String(128))
    info: Mapped[str] = mapped_column(String(128))

    __table_args__ = (Index("idx_ip_range", "ip_start_num", "ip_end_num"),)
