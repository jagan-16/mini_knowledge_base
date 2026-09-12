import logging
import json
from pydantic import ValidationError
from docling_core.types.doc.document import DoclingDocument
from internal_models.upload_data import UploadMetadata
from services.llm_service import LLMService
from services.metadata_services.metadata_content_service import MetadataContentService
from services.metadata_services.metadata_config_service import MetadataConfigService
from services.metadata_services.metadata_schema_service import MetadataSchemaService
from services.metadata_services.metadata_prompt import MetadataPromptService


class MetadataClassificationService:

    MAX_CLASSIFICATION_ATTEMPTS = 3
    def __init__(
        self,
        content_service: MetadataContentService,
        category_service: MetadataConfigService,
        schema_service: MetadataSchemaService,
        prompt_service: MetadataPromptService,
        llm_service: LLMService,
    ):
        self.content_service = content_service
        self.category_service = category_service
        self.schema_service = schema_service
        self.prompt_service = prompt_service
        self.llm_service = llm_service

        self.logger = logging.getLogger(__name__)

    def classify(
    self,
    document: DoclingDocument,
) -> UploadMetadata:

        context = self.content_service.build_context(
            document
        )

        if not context:
            raise ValueError(
                "No classification context could be generated."
            )

        categories = self.category_service.get_categories()

        metadata_model = self.schema_service.build_model(
            categories
        )

        prompt = self.prompt_service.build_prompt(
            document_text=context,
        )

        response_format = {
            "type": "json_schema",
            "json_schema": {
                "name": "document_metadata",
                "strict": True,
                "schema": metadata_model.model_json_schema(),
            },
        }
       

        for attempt in range(
            1,
            self.MAX_CLASSIFICATION_ATTEMPTS + 1,
        ):
            try:
                raw_response = self.llm_service.complete(
                    prompt=prompt,
                    history=[],
                    temperature=0.0,
                    response_format=response_format,
                )

                metadata = metadata_model.model_validate_json(
                    raw_response
                )
              
                return UploadMetadata(
                    document_data=metadata.model_dump()
                )

            except ValidationError as exc:

                self.logger.warning(
                    "Metadata classification validation failed "
                    "on attempt %d/%d: %s",
                    attempt,
                    self.MAX_CLASSIFICATION_ATTEMPTS,
                    exc,
                )

                if attempt == self.MAX_CLASSIFICATION_ATTEMPTS:
                    raise ValueError(
                        "Metadata classification failed after "
                        f"{self.MAX_CLASSIFICATION_ATTEMPTS} attempts."
                    ) from exc

        raise RuntimeError(
            "Metadata classification retry loop exited unexpectedly."
        )