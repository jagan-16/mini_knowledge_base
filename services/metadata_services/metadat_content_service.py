from math import ceil

from docling_core.types.doc.document import DoclingDocument


class MetadataContentService:

    REGION_PERCENTAGE = 0.10

    MIN_PAGES_PER_REGION = 2
    MAX_PAGES_PER_REGION = 10

    def __init__(
        self,
        pages_per_region: int | None = None,
    ):
        if pages_per_region is not None and pages_per_region < 1:
            raise ValueError(
                "pages_per_region must be greater than 0."
            )

        self.pages_per_region = pages_per_region

    def build_context(
        self,
        document: DoclingDocument,
    ) -> str:

        total_pages = self._get_total_pages(
            document
        )

        if total_pages == 0:
            return ""

        page_ranges = self._calculate_page_ranges(
            total_pages
        )

        return self._extract_context(
            document,
            page_ranges,
        )

    def _get_total_pages(
        self,
        document: DoclingDocument,
    ) -> int:

        if not document.pages:
            return 0

        return max(
            page.page_no
            for page in document.pages.values()
        )

    def _calculate_pages_per_region(
        self,
        total_pages: int,
    ) -> int:

        if self.pages_per_region is not None:
            return min(
                self.pages_per_region,
                total_pages,
            )

        calculated = ceil(
            total_pages
            * self.REGION_PERCENTAGE
        )

        return min(
            max(
                calculated,
                self.MIN_PAGES_PER_REGION,
            ),
            self.MAX_PAGES_PER_REGION,
        )

    def _calculate_page_ranges(
        self,
        total_pages: int,
    ) -> list[tuple[int, int]]:

        pages_per_region = (
            self._calculate_pages_per_region(
                total_pages
            )
        )

        # Small documents.
        #
        # If the three regions overlap,
        # use the whole document.
        if total_pages <= pages_per_region * 3:
            return [
                (1, total_pages)
            ]

        # First region
        first_start = 1
        first_end = pages_per_region

        # Middle region
        middle_center = (
            total_pages + 1
        ) // 2

        middle_start = (
            middle_center
            - pages_per_region // 2
        )

        middle_end = (
            middle_start
            + pages_per_region
            - 1
        )

        # Last region
        last_start = (
            total_pages
            - pages_per_region
            + 1
        )

        last_end = total_pages

        return [
            (first_start, first_end),
            (middle_start, middle_end),
            (last_start, last_end),
        ]

    def _extract_context(
        self,
        document: DoclingDocument,
        page_ranges: list[tuple[int, int]],
    ) -> str:

        context_parts = []

        for start_page, end_page in page_ranges:

            for page_number in range(
                start_page,
                end_page + 1,
            ):

                page_text = document.export_to_text(
                    page_no=page_number,
                    page_break_placeholder=None,
                ).strip()

                if not page_text:
                    continue

                context_parts.append(
                    f"[Page {page_number}]\n"
                    f"{page_text}"
                )

        return "\n\n".join(
            context_parts
        ).strip()