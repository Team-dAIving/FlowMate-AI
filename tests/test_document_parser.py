from io import BytesIO
import pytest
from docx import Document
from reportlab.pdfgen import canvas
from fastapi.testclient import TestClient
from app.main import app
from app.services.document_parser import (
    extract_text,
    MAX_FILE_SIZE
)

client = TestClient(app)

@pytest.fixture
def txt_bytes():

    text = (
        "프로젝트명: FlowMate\n"
        "AI 기반 협업 관리 서비스\n"
        "주요 기능: 회의록 분석"
    )

    return text.encode("utf-8")

@pytest.fixture
def pdf_bytes():

    buffer = BytesIO()

    pdf = canvas.Canvas(buffer)

    pdf.drawString(
        100, 750,
        "Project: FlowMate"
    )

    pdf.drawString(
        100, 730,
        "AI Project Management Service"
    )

    pdf.save()

    return buffer.getvalue()

@pytest.fixture
def docx_bytes():

    buffer = BytesIO()

    document = Document()

    document.add_heading(
        "FlowMate 프로젝트 계획서",
        level=1
    )

    document.add_paragraph(
        "AI 기반 협업 관리 서비스 개발"
    )

    document.add_paragraph(
        "회의록 자동 분석 기능 구현"
    )

    table = document.add_table(
        rows=2,
        cols=2
    )

    table.cell(0, 0).text = "담당자"
    table.cell(0, 1).text = "담당 업무"
    table.cell(1, 0).text = "팀원 A"
    table.cell(1, 1).text = "AI 개발"

    document.save(buffer)

    return buffer.getvalue()

def test_extract_txt(txt_bytes):

    result = extract_text(
        "project_plan.txt",
        txt_bytes
    )

    assert "FlowMate" in result
    assert "AI 기반 협업 관리 서비스" in result
    assert "회의록 분석" in result

def test_extract_txt_with_bom():

    content = "FlowMate 프로젝트".encode(
        "utf-8-sig"
    )

    result = extract_text(
        "plan.txt",
        content
    )

    assert result == "FlowMate 프로젝트"
    assert "\ufeff" not in result

def test_extract_pdf(pdf_bytes):

    result = extract_text(
        "project_plan.pdf",
        pdf_bytes
    )

    assert "Project: FlowMate" in result
    assert "AI Project Management Service" in result

def test_extract_docx(docx_bytes):

    result = extract_text(
        "project_plan.docx",
        docx_bytes
    )

    assert "FlowMate 프로젝트 계획서" in result
    assert "AI 기반 협업 관리 서비스 개발" in result
    assert "회의록 자동 분석 기능 구현" in result

def test_extract_docx_table(docx_bytes):

    result = extract_text(
        "project_plan.docx",
        docx_bytes
    )

    assert "담당자 | 담당 업무" in result
    assert "팀원 A | AI 개발" in result

def test_empty_document():

    with pytest.raises(
        ValueError,
        match="추출 가능한 텍스트가 없습니다"
    ):
        extract_text(
            "empty.txt",
            b""
        )

def test_unsupported_extension():

    with pytest.raises(
        ValueError,
        match="지원하지 않는 파일 형식"
    ):
        extract_text(
            "image.png",
            b"invalid data"
        )

def test_file_too_large():

    content = b"a" * (MAX_FILE_SIZE + 1)

    with pytest.raises(
        ValueError,
        match="파일 크기는"
    ):
        extract_text(
            "large.txt",
            content
        )

def test_txt_upload_api(txt_bytes):

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "project_plan.txt",
                txt_bytes,
                "text/plain"
            )
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["filename"] == "project_plan.txt"
    assert "FlowMate" in data["text"]
    assert data["length"] == len(data["text"])

def test_pdf_upload_api(pdf_bytes):

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "project_plan.pdf",
                pdf_bytes,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 200
    assert "FlowMate" in response.json()["text"]

def test_docx_upload_api(docx_bytes):

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "project_plan.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 200
    assert "회의록 자동 분석" in response.json()["text"]

def test_unsupported_upload_api():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "image.png",
                b"invalid data",
                "image/png"
            )
        }
    )

    assert response.status_code == 400

def test_empty_upload_api():

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "empty.txt",
                b"",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400

def test_large_upload_api():

    content = b"a" * (MAX_FILE_SIZE + 1)

    response = client.post(
        "/ai/v1/documents/extract",
        files={
            "file": (
                "large.txt",
                content,
                "text/plain"
            )
        }
    )

    assert response.status_code == 413