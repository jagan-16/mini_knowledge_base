# services/picture_semantic_service.py

import logging

from docling_core.types.doc.document import (
    DescriptionMetaField,
    DoclingDocument,
    PictureItem,
    PictureMeta,
)

from services.groq_service import GroqService
from services.extraction.image_link_service import ImageService


class PictureSemanticService:


    SEMANTIC_PROMPT = """You are a document visual understanding system for a RAG pipeline.

Analyze the entire provided image carefully and produce a detailed,
fact-based semantic description of everything that can be reliably
determined from the image.

Your output will be stored as text and later chunked and embedded for
semantic search.

IMPORTANT:
- Accuracy is more important than completeness.
- Do not invent information.
- Do not infer connections, values, labels, or relationships that are
  not visually supported.
- If something cannot be read or determined, explicitly say that it
  is unclear.
- Preserve exact labels, numbers, component references, units,
  categories, and values whenever they are visible.
- Do not merely say what the image looks like. Explain the information
  represented by the image.

First identify the visual type.

==================================================
IF IT IS A CHART OR GRAPH
==================================================

Describe:

1. Chart type
   - bar
   - line
   - pie
   - scatter
   - area
   - other

2. Title.

3. X-axis:
   - label
   - categories/values
   - units

4. Y-axis:
   - label
   - scale
   - units

5. Legend:
   - every series/category
   - exact names

6. Extract ALL visible data values.

For every data point/bar/segment, provide:
- category or x value
- series
- corresponding value
- unit

Do not provide only a general trend.

7. Explain what the chart is showing.

8. Describe important relationships and trends that are directly
   supported by the extracted values.

9. Mention comparisons between categories or series when clearly
   supported.

10. If values are approximate because of the chart scale, explicitly
    state that they are approximate.

==================================================
IF IT IS A FLOWCHART
==================================================

Describe:

1. Starting point.
2. Every processing step in sequence.
3. Every decision condition.
4. Every branch.
5. What happens on each branch.
6. Loops or repeated operations.
7. End points.
8. The complete logical flow from beginning to end.

Preserve the exact text inside nodes whenever readable.

==================================================
IF IT IS AN ELECTRICAL SCHEMATIC
==================================================

Describe:

1. All identifiable components.
2. Component reference designators.
3. Component values and ratings.
4. Input connectors.
5. Output connectors.
6. Power sources and voltage levels.
7. Ground connections.
8. Pin labels/numbers when visible.
9. Connections between components.
10. Signal/current paths when directly supported by the diagram.
11. Series and parallel relationships when clearly visible.
12. Functional sections of the circuit.

Do not invent electrical connections that are not visible.

==================================================
IF IT IS A BLOCK OR SYSTEM DIAGRAM
==================================================

Describe:

1. Every identifiable block.
2. Labels inside each block.
3. Inputs and outputs.
4. Arrows and their direction.
5. Connections between blocks.
6. Data/signal/control flow.
7. Overall system operation represented by the diagram.

==================================================
IF IT IS A PHOTO OR OTHER IMAGE
==================================================

Describe the meaningful information represented by the image,
including identifiable objects, their relationships, labels, and
relevant visual context.

==================================================
OUTPUT FORMAT
==================================================

Use clear Markdown headings and bullet points.

Do not return JSON.

Produce a detailed semantic description suitable for storage,
chunking, embedding, retrieval, and downstream question answering.
"""

    VISION_MODEL_NAME = "qwen/qwen3.8-27b"
    VISION_OUTPUT_TOKEN_BUDGET = 4096

    def __init__(
        self,
        groq_service: GroqService,
        image_service: ImageService,
    ):
        self.groq_service = groq_service
        self.image_service = image_service
        self.logger = logging.getLogger(__name__)

    def enrich_document(
        self,
        document: DoclingDocument,
    ) -> DoclingDocument:
        if not document.pictures:
            self.logger.info("No pictures found. Skipping picture enrichment.")
            return document

        self.logger.info(
            "Found %d pictures. Starting picture enrichment.",
            len(document.pictures),
        )

        for picture in document.pictures:
            self._process_picture(
                document=document,
                picture=picture,
            )

        return document

    def _process_picture(
        self,
        document: DoclingDocument,
        
        picture: PictureItem,
    ) -> None:

        self.logger.info(
            "Processing picture: %s",
            picture.self_ref,
        )

        image = picture.get_image(document)

        if image is None:
            self.logger.warning(
                "Could not obtain image for picture: %s",
                picture.self_ref,
            )
            return
        self.logger.info(
            "Picture dimensions | ref=%s | size=%sx%s",
            picture.self_ref,
            image.width,
            image.height,
        )
        
        image_data_url = self.image_service.to_data_url(
            image
        )

        semantic_description = self.extract_visual_semantics(
            prompt=self.SEMANTIC_PROMPT,
            image_data_url=image_data_url,
        )

        self._store_description(
            picture=picture,
            description=semantic_description,
        )

        self.logger.info(
            "Picture semantic description created: %s",
            picture.self_ref,
        )

    def _store_description(
        self,
        picture: PictureItem,
        description: str,
    ) -> None:

        if picture.meta is None:
            picture.meta = PictureMeta()

        picture.meta.description = DescriptionMetaField(
            text=description,
            created_by=self.VISION_MODEL_NAME,
        )

    def extract_visual_semantics(
        self,
        prompt: str,
        image_data_url: str,
    ) -> str:

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url,
                        },
                    },
                ],
            }
        ]

        return self.groq_service.chat_completion(
            model=self.VISION_MODEL_NAME,
            messages=messages,
            temperature=1.0,
            top_p=0.95,
            reasoning_effort="default",
            reasoning_format="hidden",
            max_completion_tokens=(
                self.VISION_OUTPUT_TOKEN_BUDGET
            ),
        )
