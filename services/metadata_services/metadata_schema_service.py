class MetadataSchemaService:

    def build_output_structure(
        self,
        categories: dict[str, list[str]],
    ) -> dict[str, str]:

        return {
            field: "<selected value>"
            for field in categories
        }