from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model


class MetadataSchemaService:

    def build_model(
        self,
        categories: dict[str, Any],
    ) -> type[BaseModel]:

        fields = categories["fields"]

        model_fields: dict[str, tuple[Any, Any]] = {}

        for field_name, field_config in fields.items():

            field_type = self._resolve_field_type(
                field_config
            )

            nullable = field_config.get(
                "nullable",
                False,
            )

            description = field_config.get(
                "description"
            )

            if nullable:
                field_type = field_type | None
                default = ...
            else:
                default = ...

            model_fields[field_name] = (
                field_type,
                Field(default=default, description=description ),
            )

        return create_model(
            "DocumentMetadata",
            __config__=ConfigDict(
                extra="forbid",
            ),
            **model_fields,
        )

    def _resolve_field_type(
        self,
        field_config: dict[str, Any],
    ) -> Any:

        
        field_type = field_config["type"]
        allowed_values = field_config.get(
            "allowed_values"
        )

        if allowed_values:
            return Literal[*allowed_values]

        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
        }

        python_type = type_map.get(field_type)

        if python_type is None:
            raise ValueError(
                f"Unsupported metadata type: {field_type}"
            )

        return python_type