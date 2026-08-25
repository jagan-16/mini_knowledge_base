"""
test_metadata_content_service.py

Tests the page-region-sampling MetadataContentService end to end:

    PDF
     |
    PDFExtractionService (Docling)
     |
    MetadataContentService.build_context()  -- page-region sampling
     |
    MetadataPromptService.build_prompt()
     |
    LLMService.complete()
     |
    Parsed classification result

IMPORTANT: this strategy (first/middle/last page regions, full raw page
text) is DIFFERENT from the heading + first-paragraph/list-item
structural extraction tested earlier in this project. Run this script
against the SAME test PDFs you already have known-correct answers for
(resume, Docling technical doc, Kalam biography, all-hands report,
list-item stress test) to directly compare this strategy's results
against the previously validated one -- don't trust this blind.

============================================================
THINGS THIS SCRIPT DOES NOT INVENT -- CONFIRM THESE:
============================================================
1. Import path for PDFExtractionService.
2. LLMService's MODEL_NAME is read directly from the class so the
   diagnostic page-range output is accurate to what will actually be
   sent -- no need to hardcode it separately.
"""

import json
import sys
import traceback
from pathlib import Path

from fastapi import UploadFile

# CONFIRM this import path matches your actual project structure
from services.extraction.dockling_extraction import PDFExtractionService

from services.metadata.metadata_content_service import MetadataContentService
from services.metadata.metadata_prompt_service import MetadataPromptService
from services.llm_service import LLMService

from litellm import token_counter


# ============================================================
# CONFIGURATION -- point this at whichever test PDF you want to run
# ============================================================

TEST_PDF_PATH = Path("docling_test_document.pdf")


def line(char="=", width=100):
    print(char * width)


def section(title: str):
    print()
    line()
    print(title)
    line()
    print()


def main():
    try:
        section("METADATA CONTENT SERVICE TEST (page-region sampling)")

        # --------------------------------------------------
        # [1] Extract with Docling (real service)
        # --------------------------------------------------
        print("[1] Extracting PDF with Docling...")

        if not TEST_PDF_PATH.exists():
            raise FileNotFoundError(f"Test PDF not found: {TEST_PDF_PATH}")

        extractor = PDFExtractionService()

        with open(TEST_PDF_PATH, "rb") as f:
            upload = UploadFile(filename=TEST_PDF_PATH.name, file=f)
            docling_document = extractor.extract(upload)

        print("✓ DoclingDocument created")

        total_pages = (
            max(p.page_no for p in docling_document.pages.values())
            if docling_document.pages
            else 0
        )
        print(f"Total pages: {total_pages}")

        # --------------------------------------------------
        # [2] Build context via the real MetadataContentService
        # --------------------------------------------------
        section("[2] BUILDING CONTEXT (page-region sampling)")

        content_service = MetadataContentService()

        # Surface which page ranges actually got selected, since this is
        # the core behavior being tested -- not just the final text.
        pages_per_region = content_service._calculate_pages_per_region(total_pages)
        page_ranges = content_service._calculate_page_ranges(total_pages)

        print(f"Calculated pages per region : {pages_per_region}")
        print(f"Selected page ranges        : {page_ranges}")

        if len(page_ranges) == 1 and page_ranges[0] == (1, total_pages):
            print("(Small document -- using the entire document, no sampling applied)")

        context = content_service.build_context(docling_document)

        print()
        print("EXTRACTED CONTEXT (this is what goes to the classifier)")
        print("-" * 100)
        print(context if context else "<empty -- build_context() returned nothing>")
        print("-" * 100)
        print()
        print(f"Extracted context length: {len(context)} characters")

        # --------------------------------------------------
        # [3] Build the classification prompt (real MetadataPromptService)
        # --------------------------------------------------
        section("[3] BUILDING PROMPT")

        prompt_service = MetadataPromptService()
        prompt = prompt_service.build_prompt(document_text=context)

        print("✓ Prompt built")

        # Report actual token count against the real model + real budget,
        # since this strategy can pull in far more text than the
        # structural heading-based approach did.
        full_token_count = token_counter(
            model=f"groq/{LLMService.MODEL_NAME}",
            messages=[
                {"role": "system", "content": prompt.system_prompt},
                {"role": "user", "content": prompt.user_prompt},
            ],
        )
        print(f"Full prompt token count : {full_token_count}")
        print(f"LLMService budget        : {LLMService.MAX_INPUT_TOKENS}")
        if full_token_count > LLMService.MAX_INPUT_TOKENS:
            print("⚠️  This prompt EXCEEDS the configured token budget -- "
                  "expect a 413 from LLMService below.")

        print()
        print("SYSTEM PROMPT")
        print("-" * 100)
        print(prompt.system_prompt)
        print("-" * 100)
        print()
        print("USER PROMPT")
        print("-" * 100)
        print(prompt.user_prompt)
        print("-" * 100)

        # --------------------------------------------------
        # [4] Call the LLM (real LLMService)
        # --------------------------------------------------
        section("[4] CALLING LLM")

        llm_service = LLMService()

        raw_response = llm_service.complete(
            prompt=prompt,
            history=None,
            temperature=0.0,  # deterministic for classification
        )

        print("RAW LLM RESPONSE")
        print("-" * 100)
        print(raw_response)
        print("-" * 100)

        # --------------------------------------------------
        # [5] Parse the result
        # --------------------------------------------------
        section("[5] PARSED CLASSIFICATION RESULT")

        try:
            result = json.loads(raw_response)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError as exc:
            print(f"⚠️  Could not parse LLM response as JSON: {exc}")

        section("TEST COMPLETE")

    except Exception:
        print()
        print("TEST FAILED -- see traceback below")
        print()
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()