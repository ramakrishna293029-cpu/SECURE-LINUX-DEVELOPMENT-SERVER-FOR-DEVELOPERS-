from pathlib import Path
import pypdf

ROOT = Path(__file__).resolve().parent.parent


def test_generate_ppt_creates_15_mandatory_slides() -> None:
    """Validate the 15-slide presentation deck PDF artifact in docs/."""
    deck_pdf = ROOT / "docs" / "Linux_Hackathon_Presentation.pdf"
    assert deck_pdf.is_file(), f"Missing presentation PDF: {deck_pdf}"
    assert deck_pdf.stat().st_size > 500_000, "Presentation PDF is too small or corrupt"

    reader = pypdf.PdfReader(str(deck_pdf))
    assert len(reader.pages) == 15, f"Expected 15 slides, got {len(reader.pages)}"


def test_report_artifact_present_and_valid() -> None:
    """Validate the 24-page formal project report PDF artifact in docs/."""
    report_pdf = ROOT / "docs" / "Linux_Hackathon_Report.pdf"
    assert report_pdf.is_file(), f"Missing report PDF: {report_pdf}"
    assert report_pdf.stat().st_size > 500_000, "Report PDF is too small or corrupt"

    reader = pypdf.PdfReader(str(report_pdf))
    assert len(reader.pages) == 24, f"Expected 24 report pages, got {len(reader.pages)}"
