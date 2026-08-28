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
        if (
            pages_per_region is not None
            and pages_per_region < 1
        ):
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

        selected_pages = self._expand_page_ranges(
            page_ranges
        )

        selected_page_set = set(
            selected_pages
        )

        page_content = self._extract_page_content(
            document,
            selected_page_set,
        )

        heading_content = self._extract_headings(
            document,
            selected_page_set,
        )

        return self._build_context(
            page_content,
            heading_content,
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

        # Small document.
        #
        # If the three regions overlap,
        # use the entire document.
        if total_pages <= pages_per_region * 3:

            return [
                (1, total_pages)
            ]

        # First region
        first_start = 1

        first_end = (
            pages_per_region
        )

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
            (
                first_start,
                first_end,
            ),
            (
                middle_start,
                middle_end,
            ),
            (
                last_start,
                last_end,
            ),
        ]

    def _expand_page_ranges(
        self,
        page_ranges: list[tuple[int, int]],
    ) -> list[int]:

        pages = set()

        for start_page, end_page in page_ranges:

            pages.update(
                range(
                    start_page,
                    end_page + 1,
                )
            )

        return sorted(pages)

    def _extract_page_content(
        self,
        document: DoclingDocument,
        selected_pages: set[int],
    ) -> dict[int, str]:

        page_content: dict[int, str] = {}

        for page_number in selected_pages:

            text = document.export_to_text(
                page_no=page_number,
                page_break_placeholder=None,
            ).strip()

            if not text:
                continue

            page_content[page_number] = text

        return page_content

    def _extract_headings(
        self,
        document: DoclingDocument,
        selected_pages: set[int],
    ) -> dict[int, list[str]]:

        headings: dict[int, list[str]] = {}

        for item in document.texts:

            label = getattr(
                item,
                "label",
                None,
            )

            if str(label) != "section_header":
                continue

            text = getattr(
                item,
                "text",
                None,
            )

            if not text:
                continue

            text = text.strip()

            if not text:
                continue

            if not item.prov:
                continue

            for provenance in item.prov:

                page_number = (
                    provenance.page_no
                )

                if page_number is None:
                    continue

                # These pages already have their complete
                # content included. Do not duplicate their
                # headings in the structural section.
                if page_number in selected_pages:
                    continue

                headings.setdefault(
                    page_number,
                    [],
                ).append(text)

        return headings

    def _build_context(
        self,
        page_content: dict[int, str],
        headings: dict[int, list[str]],
    ) -> str:

        context_parts = []

        # ---------------------------------------------
        # Representative page content
        # ---------------------------------------------

        if page_content:

            context_parts.append(
                "<representative_content>"
            )

            for page_number in sorted(
                page_content
            ):

                context_parts.append(
                    f"[Page {page_number}]\n"
                    f"{page_content[page_number]}"
                )

            context_parts.append(
                "</representative_content>"
            )

        # ---------------------------------------------
        # Document-wide headings
        # ---------------------------------------------

        if headings:

            context_parts.append(
                "<document_structure>"
            )

            for page_number in sorted(
                headings
            ):

                context_parts.append(
                    f"[Page {page_number}]"
                )

                for heading in headings[
                    page_number
                ]:

                    context_parts.append(
                        f"- {heading}"
                    )

            context_parts.append(
                "</document_structure>"
            )

        return "\n\n".join(
            context_parts
        ).strip()