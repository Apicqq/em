import asyncio
import sys
from datetime import datetime

from sqlalchemy.orm import (
    declarative_base,
    Mapped,
    mapped_column,
    declared_attr,
)
from sqlalchemy import String, Float, Date, DateTime, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from db_setup import AsyncSessionLocal, engine
from parser_stdlib import parse_xls_files, REPORTS_DIR


class PreBase:

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = mapped_column(
        Integer, primary_key=True, autoincrement=True, unique=True
    )


Base = declarative_base(cls=PreBase)


class Instrument(Base):  # type: ignore
    """Class which represents Instrument model in SQLAlchemy database."""

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
    """Create database model."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def import_data_to_db(session: AsyncSession) -> None:
    """Add previously-created Instruments to database."""
    instruments = parse_xls_files(REPORTS_DIR)
    session.add_all(
        [
            Instrument(**await instrument.to_dict(exclude={"id"}))
            for instrument in instruments
        ]
    )
    await session.commit()


async def create_model_and_import_data_to_db() -> None:
    """Main entrypoint to DB model creation."""

    async with AsyncSessionLocal() as session:
        sys.stdout.write("Creating model...\n")
        await create_model()

        sys.stdout.write("Importing data...\n")
        await import_data_to_db(session)

        sys.stdout.write("Importing data was successfully done.\n")


if __name__ == "__main__":
    asyncio.run(create_model_and_import_data_to_db())
