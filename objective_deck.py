"""PowerPoint deck for objective-driven analysis: one slide per question plus a data-notes slide."""
import os
import tempfile
from pptx import Presentation
from pptx.util import Inches

from slide_builder import (slide_title, _add_rect, _add_textbox, hex_to_rgb, get_contrast_color,
                           C_BLUE, C_DARK, C_GRAY, C_LIGHT, C_AMBER, C_WHITE)
import objective_charts

CONF_TEXT = {"high": "Confidence: high", "medium": "Confidence: medium", "low": "Confidence: low"}


def _kpi_slide(prs, kpis, title, accent):
    """Render a KPI summary slide that scales cleanly beyond 4 cards (up to 8 per slide)."""
    from pptx.util import Pt
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_rect(slide, 0, 0, 13.33, 1.0, accent)
    tc = get_contrast_color(accent)
    _add_textbox(slide, "Executive Highlights · Key Metrics", 0.5, 0.12, 6, 0.3, size=10, color=tc)
    _add_textbox(slide, f"{_short(title, 65)} — KPI Matrix", 0.5, 0.36, 12.3, 0.55, size=22, bold=True, color=tc)

    cards = list(kpis or [])[:8]
    if not cards:
        return
    n = len(cards)
    cols = 3 if n in (5, 6) else min(4, n)
    rows = (n + cols - 1) // cols
    margin_x, gap_x = 0.5, 0.25
    usable_w = 13.33 - 2 * margin_x
    card_w = (usable_w - gap_x * (cols - 1)) / cols
    start_y, gap_y = 1.35, 0.3
    card_h = 2.4 if rows == 2 else 3.2
    for idx, k in enumerate(cards):
        r, c = divmod(idx, cols)
        x = margin_x + c * (card_w + gap_x)
        y = start_y + r * (card_h + gap_y)
        _add_rect(slide, x, y, card_w, card_h, C_LIGHT)
        _add_rect(slide, x, y, card_w, 0.08, accent)
        _add_textbox(slide, str(k.get("label", "")).upper(), x + 0.18, y + 0.22, card_w - 0.36, 0.4, size=10, bold=True, color=C_GRAY)
        _add_textbox(slide, str(k.get("value", "n/a")), x + 0.18, y + 0.72, card_w - 0.36, 0.8, size=24 if rows == 2 else 28, bold=True, color=C_DARK)
        pill = str(k.get("pill", ""))
        if pill:
            _add_textbox(slide, pill, x + 0.18, y + card_h - 0.55, card_w - 0.36, 0.4, size=10, color=C_GRAY, italic=True)


def _chart_png(finding, tmpdir, idx, brand_color=None, currency=""):
    fig = objective_charts.figure_for(finding, dark=False, brand_color=brand_color, currency=currency)
    if fig is None:
        return None
    path = os.path.join(tmpdir, f"obj_{idx}.png")
    try:
        fig.write_image(path, width=1000, height=520, scale=1.5)
        return path
    except Exception:
        return None          # chart is optional; the slide still carries the answer in words


def _short(text, n):
    text = str(text)
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _bullets(slide, items, l, t, w, h, size=12, color=C_DARK):
    items = [str(i) for i in items if i]
    if not items:
        return
    box = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    from pptx.util import Pt
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = "• " + _short(it, 230)
        r.font.size = Pt(size)
        r.font.color.rgb = color
        p.space_after = Pt(4)


def _answer_slide(prs, result, idx, accent, tmpdir, brand_color=None, currency=""):
    f = result.finding
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_rect(slide, 0, 0, 13.33, 1.2, accent)
    tc = get_contrast_color(accent)
    _add_textbox(slide, f"Question {idx}", 0.5, 0.12, 6, 0.3, size=10, color=tc)
    _add_textbox(slide, _short(result.spec.text, 120), 0.5, 0.38, 12.3, 0.7, size=20, bold=True, color=tc)
    _add_textbox(slide, _short(f.headline, 260), 0.5, 1.4, 12.3, 1.0, size=16, bold=True, color=C_DARK)

    png = _chart_png(f, tmpdir, idx, brand_color=brand_color, currency=currency) if f.status in ("ok", "caution") else None
    if png:
        slide.shapes.add_picture(png, Inches(0.5), Inches(2.5), width=Inches(7.4))
        side_l, side_w = 8.2, 4.7
    else:
        side_l, side_w = 0.5, 12.3
    notes = list(f.details[:4])
    _bullets(slide, notes, side_l, 2.5, side_w, 2.4, size=12)
    cav = list(f.caveats[:3])
    if cav:
        _add_textbox(slide, "Read with care", side_l, 5.0, side_w, 0.3, size=11, bold=True, color=C_AMBER)
        _bullets(slide, cav, side_l, 5.3, side_w, 1.6, size=10, color=C_GRAY)
    if f.status not in ("ok", "caution"):
        _add_textbox(slide, "This question could not be answered from the data as it stands.", 0.5, 2.6, 12.3, 0.5, size=13, color=C_GRAY)
        return
    foot = f"{CONF_TEXT.get(f.confidence, '')}  |  {f.n_rows:,} rows used  |  {f.coverage_pct:.0f}% of rows had the needed values"
    _add_textbox(slide, foot, 0.5, 7.0, 12.3, 0.3, size=9, color=C_GRAY, italic=True)
    try:
        slide.notes_slide.notes_text_frame.text = "Assumptions: " + "; ".join(f.assumptions) if f.assumptions else ""
    except Exception:
        pass


def _notes_slide(prs, results, quality_notes, accent):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _add_rect(slide, 0, 0, 13.33, 1.0, accent)
    _add_textbox(slide, "How this analysis was done", 0.5, 0.25, 12, 0.6, size=22, bold=True, color=get_contrast_color(accent))
    _add_textbox(slide, "Data preparation", 0.5, 1.2, 6, 0.35, size=13, bold=True, color=C_DARK)
    _bullets(slide, quality_notes[:8] or ["No cleaning changes were needed."], 0.5, 1.6, 6.0, 5.2, size=10)
    assumptions = []
    for r in results:
        for a in r.finding.assumptions[:2]:
            assumptions.append(f"Q: {_short(r.spec.text, 40)} — {a}")
    _add_textbox(slide, "Assumptions made", 6.9, 1.2, 6, 0.35, size=13, bold=True, color=C_DARK)
    _bullets(slide, assumptions[:8] or ["No assumptions were needed."], 6.9, 1.6, 6.0, 5.2, size=10)


def build_objective_deck(results, title="Analysis Report", quality_notes=None, brand_color=None,
                         brand_name=None, logo_path=None, output_dir=None, kpis=None, currency="") -> str:
    """results: list of ObjectiveResult. Returns the saved .pptx path."""
    accent = hex_to_rgb(brand_color) if brand_color else C_BLUE
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.33), Inches(7.5)
    n_ok = sum(1 for r in results if r.finding.status in ("ok", "caution"))
    slide_title(prs, report_name=title, subtitle=f"{n_ok} of {len(results)} question(s) answered",
                accent_color=accent, logo_path=logo_path, brand_name=brand_name)
    if kpis:
        _kpi_slide(prs, kpis, title, accent)
    with tempfile.TemporaryDirectory() as tmp:
        for i, r in enumerate(results, 1):
            _answer_slide(prs, r, i, accent, tmp, brand_color=brand_color, currency=currency)
        _notes_slide(prs, results, list(quality_notes or []), accent)
        out_dir = output_dir or tempfile.mkdtemp(prefix="deck_")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "Analysis_Report.pptx")
        prs.save(path)
    return path
