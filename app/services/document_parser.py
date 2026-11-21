from io import BytesIO
from pathlib import Path
from pypdf import PdfReader
from docx import Document

MAX_FILE_SIZE = 10 * 1024 * 1024

def extract_text(
    filename: str,
    file_bytes: bytes
) -> str:

    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError("파일 크기는 10MB 이하여야 합니다.")

    extension = Path(filename).suffix.lower()

    if extension == ".txt":
        text = file_bytes.decode("utf-8-sig")

    elif extension == ".pdf":
        reader = PdfReader(BytesIO(file_bytes))

        text = "\n".join(
            page.extract_text() or ""
            for page in reader.pages
        )

    elif extension == ".docx":
        document = Document(BytesIO(file_bytes))

        paragraphs = [
            p.text for p in document.paragraphs
            if p.text.strip()
        ]

        # Word 표의 내용도 추출
        for table in document.tables:
            for row in table.rows:
                paragraphs.append(
                    " | ".join(
                        cell.text for cell in row.cells
                    )
                )

        text = "\n".join(paragraphs)

    else:
        raise ValueError("지원하지 않는 파일 형식입니다.")

    text = text.strip()

    if not text:
        raise ValueError("추출 가능한 텍스트가 없습니다.")

    return text