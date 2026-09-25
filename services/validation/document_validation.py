from fastapi import HTTPException, UploadFile
import pymupdf


class DocumentValidator:

    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MiB
    MAX_PAGES = 50

    def validate_file(
        self,
        file: UploadFile,
    ) -> None:

        # ---------------------------------------------------------
        # 1. Make sure we are starting from the beginning
        # ---------------------------------------------------------
        file.file.seek(0)

        # ---------------------------------------------------------
        # 2. Check file size
        # ---------------------------------------------------------
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        # ---------------------------------------------------------
        # 3. Reject empty file
        # ---------------------------------------------------------
        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        # ---------------------------------------------------------
        # 4. Reject file larger than application limit
        # ---------------------------------------------------------
        if file_size > self.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="PDF exceeds the maximum allowed file size of 20 MiB.",
            )

        # ---------------------------------------------------------
        # 5. Read actual file bytes
        # ---------------------------------------------------------
        pdf_bytes = file.file.read()

        # ---------------------------------------------------------
        # 6. Check PDF file signature
        #
        # A normal PDF begins with:
        # %PDF-
        # ---------------------------------------------------------
        if not pdf_bytes.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is not a PDF.",
            )

        # ---------------------------------------------------------
        # 7. Parse the actual bytes with a PDF parser
        #
        # Do NOT trust:
        #   - filename extension
        #   - client-provided MIME type
        #
        # The parser examines the actual content.
        # ---------------------------------------------------------
        try:
            pdf = pymupdf.open(
                stream=pdf_bytes,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="PDF is corrupted or cannot be opened.",
            ) from exc

        try:

            # -----------------------------------------------------
            # 8. Confirm the opened document is actually a PDF
            # -----------------------------------------------------
            if not pdf.is_pdf:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded file is not a PDF.",
                )

            # -----------------------------------------------------
            # 9. Reject password-protected / encrypted PDF
            # -----------------------------------------------------
            if pdf.needs_pass:
                raise HTTPException(
                    status_code=400,
                    detail="Password-protected PDFs are not supported.",
                )

            # -----------------------------------------------------
            # 10. Reject zero-page PDF
            # -----------------------------------------------------
            if pdf.page_count == 0:
                raise HTTPException(
                    status_code=400,
                    detail="PDF contains no pages.",
                )

            # -----------------------------------------------------
            # 11. Reject PDFs above application page limit
            # -----------------------------------------------------
            if pdf.page_count > self.MAX_PAGES:
                raise HTTPException(
                    status_code=400,
                    detail="PDF exceeds the maximum allowed page count of 50.",
                )

            # -----------------------------------------------------
            # Optional diagnostic:
            #
            # pdf.is_repaired tells us whether PyMuPDF had to repair
            # the PDF while opening it.
            #
            # We are NOT rejecting repaired PDFs here.
            # -----------------------------------------------------
            if pdf.is_repaired:
                raise HTTPException(
                        status_code=400,
                        detail="PDF is structurally damaged and cannot be processed."
                    )

        finally:
            # -----------------------------------------------------
            # 12. Always close the preflight PDF object
            # -----------------------------------------------------
            pdf.close()

        # ---------------------------------------------------------
        # 13. Reset UploadFile pointer
        #
        # Important because the validator already consumed the file.
        # PDFExtractionService must be able to read it again.
        # ---------------------------------------------------------
        file.file.seek(0)