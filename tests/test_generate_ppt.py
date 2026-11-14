import subprocess
import sys
from pathlib import Path

from pptx import Presentation

ROOT = Path(__file__).resolve().parent.parent
GEN_SCRIPT = ROOT / "docs" / "generate_ppt.py"

EXPECTED_SLIDE_KEYWORDS = [
    "Software Development Company Infrastructure",
    "Problem Statement",
    "Objectives",
    "Proposed Solution",
    "System Architecture",
    "Tools, Technologies",
    "Linux Commands",
    "Storage Management",
    "Automation",
    "Security",
    "Live Demonstration",
    "Testing",
    "Challenges",
    "Conclusion",
    "References",
]


def test_generate_ppt_creates_15_mandatory_slides(tmp_path: Path) -> None:
    assert GEN_SCRIPT.is_file(), f"Missing generator script: {GEN_SCRIPT}"
    out_pptx = tmp_path / "test_deck.pptx"

    proc = subprocess.run(
        [sys.executable, str(GEN_SCRIPT), "--output", str(out_pptx)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, f"generate_ppt.py failed: {proc.stderr}\n{proc.stdout}"
    assert out_pptx.is_file(), "Output PPTX file was not created"

    prs = Presentation(str(out_pptx))
    assert len(prs.slides) == 15, f"Expected 15 slides, got {len(prs.slides)}"

    for idx, slide in enumerate(prs.slides):
        all_text = "\n".join(
            shape.text_frame.text.strip()
            for shape in slide.shapes
            if shape.has_text_frame and shape.text_frame.text.strip()
        )
        assert all_text, f"Slide {idx + 1} has no text content"
        for forbidden in ("TODO", "FIXME", "TBD", "lorem ipsum"):
            assert forbidden.lower() not in all_text.lower(), (
                f"Forbidden placeholder '{forbidden}' found on slide {idx + 1}"
            )
        keyword = EXPECTED_SLIDE_KEYWORDS[idx]
        assert keyword.lower() in all_text.lower(), (
            f"Slide {idx + 1} missing expected topic keyword '{keyword}'. Got:\n{all_text[:200]}"
        )
        assert slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip(), (
            f"Slide {idx + 1} missing speaker notes"
        )
