from abc import ABC
from dataclasses import dataclass, asdict
from datetime import date, datetime
from typing import Any, Optional


@dataclass
class AbstractModel(ABC):
    """Base model, from which any domain model should be inherited."""

    async def to_dict(
        self,
        include: Optional[dict[str, Any]] = None,
        exclude: Optional[set[str]] = None,
    ) -> dict[str, Any]:
        """
        Create a dictionary representation of the model.

        :param exclude: set of model fields,
         which should be excluded from dictionary representation.
        :param include: set of model fields,
         which should be included into dictionary representation.

        :return: dictionary representation of the model.
        """

        data: dict[str, Any] = asdict(self)
        if exclude:
            for key in exclude:
                try:
                    del data[key]
                except KeyError:
                    pass
        if include:
            data.update(include)
        return data


@dataclass
class Instrument(AbstractModel):
    """Model which represents an instrument."""

    exchange_product_id: str
    exchange_product_name: str
    oil_id: str
    delivery_basis_id: str
    delivery_basis_name: str
    delivery_type_id: str
    volume: float
    total: float
    count: float
    date: date
    created_on: datetime
    updated_on: Optional[datetime]
    id: int = 0
