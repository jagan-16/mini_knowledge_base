from typing import Any, Callable

from sqlalchemy import Integer, Numeric, and_, or_

from database_model import Document

from internal_models.retrieval_filter import (
    MetadataCondition,
    MetadataFilterGroup,
)


class MetadataFilterQueryBuilder:

    def __init__(self):

        # -----------------------------------------
        # Metadata condition operators
        # -----------------------------------------

        self.operator_builders: dict[
            str,
            Callable[
                [Any, Any],
                Any,
            ],
        ] = {
            "eq": self._build_eq,
            "neq": self._build_neq,
            "in": self._build_in,
            "not_in": self._build_not_in,
            "gt": self._build_gt,
            "lt": self._build_lt,
            "gte": self._build_gte,
            "lte": self._build_lte,
        }

        # -----------------------------------------
        # Group operators
        # -----------------------------------------

        self.group_operators: dict[
            str,
            Callable[..., Any],
        ] = {
            "and": and_,
            "or": or_,
        }

    def build(
        self,
        group: MetadataFilterGroup,
    ):
        """
        Convert a MetadataFilterGroup into
        a SQLAlchemy boolean expression.
        """

        return self._build_group(group)

    def _build_group(
        self,
        group: MetadataFilterGroup,
    ):
        """
        Recursively build a SQLAlchemy expression
        for a metadata filter group.
        """

        expressions = []

        for node in group.conditions:

            expression = self._build_node(node)

            if expression is not None:
                expressions.append(expression)

        if not expressions:
            return None

        try:
            group_operator = self.group_operators[
                group.operator
            ]

        except KeyError as exc:
            raise ValueError(
                f"Unsupported group operator: "
                f"{group.operator}"
            ) from exc

        return group_operator(*expressions)

    def _build_node(
        self,
        node: (
            MetadataCondition
            | MetadataFilterGroup
        ),
    ):
        """
        Build an expression for either:

        - one MetadataCondition
        - one nested MetadataFilterGroup
        """

        if isinstance(node, MetadataCondition):
            return self._build_condition(node)

        if isinstance(node, MetadataFilterGroup):
            return self._build_group(node)

        raise TypeError(
            "Unsupported metadata filter node: "
            f"{type(node).__name__}"
        )

    def _build_condition(
        self,
        condition: MetadataCondition,
    ):
        """
        Convert one MetadataCondition into
        a SQLAlchemy expression.
        """

        metadata_value = (
            Document
            .doc_metadata[
                condition.field
            ]
            .astext
        )

        try:
            operator_builder = self.operator_builders[
                condition.operator
            ]

        except KeyError as exc:
            raise ValueError(
                f"Unsupported metadata operator: "
                f"{condition.operator}"
            ) from exc

        return operator_builder(
            metadata_value,
            condition.value,
        )

    # =================================================
    # Operator implementations
    # =================================================

    def _build_eq(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field = value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "eq",
        )

        return metadata_value == value

    def _build_neq(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field != value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "neq",
        )

        return metadata_value != value

    def _build_in(
        self,
        metadata_value,
        value: list[str],
    ):
        """
        field IN (value1, value2, ...)
        """

        self._require_list(
            value,
            "in",
        )

        return metadata_value.in_(value)

    def _build_not_in(
        self,
        metadata_value,
        value: list[str],
    ):
        """
        field NOT IN (value1, value2, ...)
        """

        self._require_list(
            value,
            "not_in",
        )

        return metadata_value.notin_(value)

    def _build_gt(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field > value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "gt",
        )

        return metadata_value > value

    def _build_lt(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field < value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "lt",
        )

        return metadata_value < value

    def _build_gte(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field >= value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "gte",
        )

        return metadata_value >= value

    def _build_lte(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        field <= value
        """

        metadata_value = self._prepare_metadata_value(
            metadata_value,
            value,
        )

        self._require_scalar(
            value,
            "lte",
        )

        return metadata_value <= value

    # =================================================
    # Metadata type handling
    # =================================================

    def _prepare_metadata_value(
        self,
        metadata_value,
        value: str | int | float,
    ):
        """
        Prepare the JSONB value for comparison.

        Strings are compared as text.

        Integers are compared as integers.

        Floats are compared as numeric values.
        """

        if isinstance(value, bool):
            raise ValueError(
                "Boolean values are not supported "
                "for metadata comparisons."
            )

        if isinstance(value, int):
            return metadata_value.cast(Integer)

        if isinstance(value, float):
            return metadata_value.cast(Numeric)

        if isinstance(value, str):
            return metadata_value

        raise ValueError(
            f"Unsupported metadata value type: "
            f"{type(value).__name__}"
        )

    # =================================================
    # Value validation
    # =================================================

    def _require_scalar(
        self,
        value: Any,
        operator: str,
    ) -> None:

        if isinstance(value, bool):
            raise ValueError(
                f"Operator '{operator}' "
                f"does not accept boolean values."
            )

        if not isinstance(
            value,
            (str, int, float),
        ):
            raise ValueError(
                f"Operator '{operator}' "
                f"requires a string or numeric value."
            )

    def _require_list(
        self,
        value: Any,
        operator: str,
    ) -> None:

        if not isinstance(
            value,
            list,
        ):
            raise ValueError(
                f"Operator '{operator}' "
                f"requires a list of values."
            )

        if not value:
            raise ValueError(
                f"Operator '{operator}' "
                f"requires at least one value."
            )

        if not all(
            isinstance(item, str)
            for item in value
        ):
            raise ValueError(
                f"Operator '{operator}' "
                f"requires a list of strings."
            )