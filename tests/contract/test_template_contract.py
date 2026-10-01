import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = ROOT / "templates"


def test_front_selects_image_or_english_and_keeps_answers_off_front():
    front = (TEMPLATES / "front.html").read_text(encoding="utf-8")
    assert "{{#Image}}" in front and "{{/Image}}" in front
    assert "{{^Image}}" in front and "{{/Image}}" in front
    assert "{{Image}}" in front and "{{English}}" in front
    assert "Answer in Bahasa Indonesia" in front
    assert "or Bahasa Melayu" in front
    assert "{{Indonesian}}" not in front
    assert "{{Malaysian}}" not in front


def test_front_back_and_styles_are_html_css_only_and_responsive():
    front = (TEMPLATES / "front.html").read_text(encoding="utf-8").lower()
    back = (TEMPLATES / "back.html").read_text(encoding="utf-8").lower()
    css = (TEMPLATES / "style.css").read_text(encoding="utf-8").lower()
    assert "<script" not in front + back
    assert "http://" not in front + back + css
    assert "https://" not in front + back + css
    assert "bahasa indonesia" in back and "{{indonesian}}" in back
    assert "bahasa melayu" in back and "{{malaysian}}" in back
    assert "{{english}}" in back
    assert "text-transform: uppercase" in css
    cue_size = re.search(r"\.english-cue\s*\{[^}]*font-size:\s*([\d.]+)rem", css)
    prompt_size = re.search(r"\.prompt\s*\{[^}]*font-size:\s*([\d.]+)rem", css)
    assert cue_size and prompt_size
    assert float(cue_size.group(1)) >= 1.5 * float(prompt_size.group(1))
    assert re.search(r"\.english-cue\s*\{[^}]*font-weight:\s*(?:[6-9]00|bold)", css)
    assert "overflow-wrap: anywhere" in css
    assert "max-width: 100%" in css
