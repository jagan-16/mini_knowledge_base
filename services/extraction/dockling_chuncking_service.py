import hashlib

from transformers import AutoTokenizer

from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import (
    HuggingFaceTokenizer,
)
import logging


from internal_models.chunk_model import ChunkData


class ChunkingService:
    
    logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
    logger = logging.getLogger(__name__)
    EMBEDDING_MODEL_ID = "BAAI/bge-base-en-v1.5"

    def __init__(
        self,
        max_tokens: int = 250,
        merge_peers: bool = True,
    ):

        # Load the SAME tokenizer used by the embedding model.
        hf_tokenizer = AutoTokenizer.from_pretrained(
            self.EMBEDDING_MODEL_ID
        )

        self.tokenizer = HuggingFaceTokenizer(
            tokenizer=hf_tokenizer,
            max_tokens=max_tokens,
        )

        self.chunker = HybridChunker(
            tokenizer=self.tokenizer,
            merge_peers=merge_peers,
        )

    def _generate_chunk_hash(
        self,
        text: str,
    ) -> str:

        return hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest()

    def _get_page_numbers(
        self,
        chunk,
    ) -> list[int]:

        pages = set()

        if not chunk.meta.doc_items:
            return []

        for item in chunk.meta.doc_items:

            if not item.prov:
                continue

            for provenance in item.prov:

                if provenance.page_no is not None:
                    pages.add(
                        provenance.page_no
                    )

        return sorted(pages)

    def chunk_document(
        self,
        document,
    ) -> list[ChunkData]:

        chunks: list[ChunkData] = []
        
        for chunk_index, chunk in enumerate(
            self.chunker.chunk(
                dl_doc=document
            )
        ):

            # This is the representation that should
            # normally be sent to the embedding model.
            chunk_text = self.chunker.contextualize(
                chunk
            ).strip()
         
            if not chunk_text:
                continue

            token_count = self.tokenizer.count_tokens(
                chunk_text
            )

            page_numbers = self._get_page_numbers(
                chunk
            )

            chunk_hash = self._generate_chunk_hash(
                chunk_text
            )
            self.logger.info(
                                "Chunk created | index=%s pages=%s tokens=%s",
                                chunk_index,
                                page_numbers,
                                token_count,
                            )

            chunks.append(
                ChunkData(
                    chunk_index=chunk_index,
                    page_numbers=page_numbers,
                    chunk_text=chunk_text,
                    token_count=token_count,
                    chunk_hash=chunk_hash,
                )
            )
           

        return chunks