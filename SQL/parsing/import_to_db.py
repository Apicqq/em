import asyncio
from datetime import datetime

from sqlalchemy.orm import (
    declarative_base,
    Mapped,
    mapped_column,
    declared_attr,
)
from sqlalchemy import String, Float, Date, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from .db_setup import AsyncSessionLocal, engine
from .parser_stdlib import read_xls_file, REPORTS_DIR


class PreBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, unique=True
    )


Base = declarative_base(cls=PreBase)


class Instrument(Base):  # type: ignore

    __tablename__ = "instruments"

    exchange_product_id: Mapped[str] = mapped_column(String(30))
    exchange_product_name: Mapped[str] = mapped_column(String(300))
    oil_id: Mapped[str] = mapped_column(String(30))
    delivery_basis_id: Mapped[str] = mapped_column(String(30))
    delivery_basis_name: Mapped[str] = mapped_column(String(50))
    delivery_type_id: Mapped[str] = mapped_column(String(30))
    volume: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)
    count: Mapped[float] = mapped_column(Float)
    date: Mapped[datetime] = mapped_column(Date, default=datetime.now().date)
    created_on: Mapped[datetime] = mapped_column(DateTime)
    updated_on = mapped_column(DateTime)


async def create_model() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def import_data_to_db(session: AsyncSession) -> None:
    instruments = read_xls_file(REPORTS_DIR)
    session.add_all(
        [
            Instrument(**await instrument.to_dict(exclude={"id"}))
            for instrument in instruments
        ]
    )
    await session.commit()


async def entrypoint() -> None:
    async with AsyncSessionLocal() as session:
        await create_model()
        await import_data_to_db(session)


if __name__ == "__main__":
    asyncio.run(entrypoint())
