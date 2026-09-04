import json
import logging

from docling_core.types.doc.document import DoclingDocument
from internal_models.upload_data import UploadMetadata
from services.llm_service import LLMService
from services.metadata_services.metadata_content_service import MetadataContentService
from services.metadata_services.metadata_config_service import MetadataConfigService
from services.metadata_services.metadata_schema_service import MetadataSchemaService
from services.metadata_services.metadata_prompt import MetadataPromptService


class MetadataClassificationService:

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

        # 1. Build the classification context
        context = self.content_service.build_context(
            document
        )

        if not context:
            raise ValueError(
                "No classification context could be generated."
            )

        # 2. Load classification configuration
        categories = self.category_service.get_categories()
       
        # 3. Build the dynamic output structure
        output_structure = (
            self.schema_service.build_output_structure(
                categories
            )
        )

        # 4. Build the LLM prompt
        prompt = self.prompt_service.build_prompt(
            document_text=context,
            categories=categories,
            output_structure=output_structure,
        )

        # 5. Call the LLM
        raw_response = self.llm_service.complete(
            prompt=prompt,
            history=[],
            temperature=0.0,
            response_format={
                "type": "json_object"
            },
        )

        # 6. Convert the JSON response into a Python object
        try:
            metadata = json.loads(raw_response)

        except json.JSONDecodeError as exc:

            self.logger.error(
                "Metadata classification returned invalid JSON.",
                exc_info=True,
            )

            raise ValueError(
                "Metadata classification returned invalid JSON."
            ) from exc

        return UploadMetadata(
            document_data= metadata
        )