from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID
from typing import Literal



@dataclass
class MetadataCondition:

    field: str

    operator: Literal[       
        "eq",
        "neq",
        "in",
        "not_in",
        "lte" ,
        "lt",
        "gte",
        "gt"
]

    value: str | list[str]


@dataclass
class MetadataFilterGroup:

    operator: Literal["and", "or"]

    conditions: list[
        MetadataCondition | MetadataFilterGroup
    ]


@dataclass
class RetrievalFilter:

    top_k: int = 20

    document_id: UUID | None = None

    metadata_filters: MetadataFilterGroup | None = None