from typing import Any, Callable

from sqlalchemy import and_, or_

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
            "gt": self._build_gt ,
            "lt" : self._build_lt ,
            "gte" : self._build_gte,
            "lte" : self._build_lte
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

            expression = self._build_node(
                node
            )

            if expression is not None:
                expressions.append(
                    expression
                )

        if not expressions:
            return None

        try:

            group_operator = (
                self.group_operators[
                    group.operator
                ]
            )

        except KeyError as exc:

            raise ValueError(
                f"Unsupported group operator: "
                f"{group.operator}"
            ) from exc

        return group_operator(
            *expressions
        )

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

        if isinstance(
            node,
            MetadataCondition,
        ):

            return self._build_condition(
                node
            )

        if isinstance(
            node,
            MetadataFilterGroup,
        ):

            return self._build_group(
                node
            )

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

            operator_builder = (
                self.operator_builders[
                    condition.operator
                ]
            )

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
        value: str,
    ):
        """
        field = value
        """

        self._require_string(
            value,
            "eq",
        )

        return (
            metadata_value
            == value
        )

    def _build_neq(
        self,
        metadata_value,
        value: str,
    ):
        """
        field != value
        """

        self._require_string(
            value,
            "neq",
        )

        return (
            metadata_value
            != value
        )

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

        return metadata_value.in_(
            value
        )

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

        return metadata_value.notin_(
            value
        )
    def _build_gt(
        self, 
        metadata_value,
        value: str
    ):
        """field > value"""
        
        self._require_string(
            value , 
            "gt"
        )
        
        return metadata_value > value 
    
    def _build_lt(
        self, 
        metadata_value,
        value: str 
    ):
        """field value"""
        
        self._require_string(
            value ,
            "lt"
        )
        
        return metadata_value < value 
    
    def _build_gte(
        self , 
        metadata_value ,
        value: str 
    ):
        
        """field >= value """
        
        self._require_string(
            value , 
            "gte"
        )
        
        return metadata_value >= value 
    
    def _build_lte(
        self , 
        metadata_value , 
        value 
    ):
        """field <= value """
        
        self. _require_string (
            value ,
            "lte"
        )
        
        return metadata_value <= value 
        
        
    # =================================================
    # Value validation
    # =================================================

    def _require_string(
        self,
        value: Any,
        operator: str,
    ) -> None:

        if not isinstance(
            value,
            str,
        ):

            raise ValueError(
                f"Operator '{operator}' "
                f"requires a string value."
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