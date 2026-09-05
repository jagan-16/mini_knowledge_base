from services.metadata_services.metadata_config_service import MetadataConfigService

class MetadataSchemaService:

    def build_output_structure(
        self,
        categories: dict[str, dict ],
    ) -> dict[str, str]:

        return {
            field: "<selected value>"
            for field in categories["fields"]
        }
