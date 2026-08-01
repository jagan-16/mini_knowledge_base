import hashlib
import tiktoken

from langchain_text_splitters import RecursiveCharacterTextSplitter

from internal_models.extracted_document import ExtractedDocument
from internal_models.chunk_model import ChunkData


class ChunkingService:

    def __init__(
        self,
        chunk_size: int = 250,
        chunk_overlap: int = 40,
        encoding_name: str = "cl100k_base",
    ):

        self.encoding = tiktoken.get_encoding(
            encoding_name
        )

        self.splitter = (
            RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                encoding_name=encoding_name,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=[
                    "\n\n",
                    "\n",
                    ". ",
                    " ",
                    ""
                ],
            )
        )

    def _generate_chunk_hash(self, text: str) -> str:
        """
        Generate a SHA-256 hash for the chunk text.
        """

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    def chunk_document(
        self,
        document: ExtractedDocument,
    ) -> list[ChunkData]:

        chunks: list[ChunkData] = []

        chunk_index = 0

        for page in document.pages:

            page_chunks = self.splitter.split_text(
                page.text
            )

            for text in page_chunks:

                text = text.strip()

                if not text:
                    continue

                token_count = len(
                    self.encoding.encode(text)
                )

                chunk_hash = self._generate_chunk_hash(
                    text
                )

                chunks.append(

                    ChunkData(
                        chunk_index=chunk_index,
                        page_number=page.page_number,
                        chunk_text=text,
                        token_count=token_count,
                        chunk_hash=chunk_hash,
                    )

                )

                chunk_index += 1

        return chunks