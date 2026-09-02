from pydantic_validation import (
    MetadataConditionRequest,
    MetadataFilterGroupRequest,
)

from internal_models.retrieval_filter import (
    MetadataCondition,
    MetadataFilterGroup,
)


class MetadataFilterMapper:

    def to_internal(
        self,
        group: MetadataFilterGroupRequest,
    ) -> MetadataFilterGroup:
        return MetadataFilterGroup(
            operator=group.operator,
            conditions=[
                self._to_node(node)
                for node in group.conditions
            ],
        )

    def _to_node(
        self,
        node: MetadataConditionRequest | MetadataFilterGroupRequest,
    ) -> MetadataCondition | MetadataFilterGroup:

        if isinstance(node, MetadataConditionRequest):
            return MetadataCondition(
                field=node.field,
                operator=node.operator,
                value=node.value,
            )

        if isinstance(node, MetadataFilterGroupRequest):
            return self.to_internal(node)

        raise TypeError(
            f"Unsupported metadata filter node: {type(node).__name__}"
        )