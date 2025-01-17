import datetime
import decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Integer, Numeric, CheckConstraint, Text, BigInteger, Index, DateTime, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


class PydWalletQueryBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    address: str


class PydWalletQuery(PydWalletQueryBase):
    query_id: Optional[int] = None
    created_at: Optional[datetime.datetime] = datetime.datetime.now()
    balance: Optional[decimal.Decimal] = None
    bandwidth: Optional[int] = None
    energy: Optional[int] = None


Base = declarative_base()


class WalletQuery(Base):
    __tablename__ = "wallet"

    query_id: Mapped[Optional[int]] = mapped_column(primary_key=True, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(), default=func.now())
    address: Mapped[str] = mapped_column(Text())
    balance: Mapped[Optional[decimal.Decimal]] = mapped_column(Numeric())
    bandwidth: Mapped[Optional[int]] = mapped_column(Integer())
    energy: Mapped[Optional[int]] = mapped_column(BigInteger())

    __table_args__ = (
        Index("idx_address_hash", address, postgresql_using="hash"),
        CheckConstraint(balance >= 0, name="check_balance_non_negative"),
        CheckConstraint(bandwidth >= 0, name="check_bandwidth_non_negative"),
        CheckConstraint(energy >= 0, name="check_energy_non_negative"),
    )
