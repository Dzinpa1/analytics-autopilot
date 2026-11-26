"""
slide_builder.py
Assembles the final PowerPoint deck from charts, KPIs, and AI insights.
Output: output/Analytics_Report.pptx
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Colours (matching chart_engine palette) ───────────────────────────────────
C_BLUE       = RGBColor(0x25, 0x63, 0xEB)
C_PURPLE     = RGBColor(0x7C, 0x3A, 0xED)
C_GREEN      = RGBColor(0x10, 0xB9, 0x81)
C_AMBER      = RGBColor(0xF5, 0x9E, 0x0B)
C_WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK       = RGBColor(0x1E, 0x29, 0x3B)
C_DARK_SLATE = RGBColor(0x0F, 0x17, 0x2A)
C_LIGHT      = RGBColor(0xF8, 0xFA, 0xFC)
C_GRAY       = RGBColor(0x64, 0x74, 0x8B)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def hex_to_rgb(hex_str: str, default=C_BLUE) -> RGBColor:
    """Converts a hex color string like #6366F1 to a python-pptx RGBColor."""
    try:
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return RGBColor(r, g, b)
    except Exception:
        pass
    return default


def get_contrast_color(rgb_color: RGBColor) -> RGBColor:
    """Returns dark slate #0F172A for light backgrounds, or white #FFFFFF for dark backgrounds."""
    if not rgb_color:
        return C_WHITE
    try:
        lum = 0.299 * rgb_color[0] + 0.587 * rgb_color[1] + 0.114 * rgb_color[2]
        return C_DARK_SLATE if lum > 160 else C_WHITE
    except Exception:
        return C_WHITE


def _add_rect(slide, l, t, w, h, color):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def _tf(shape, text, size, bold=False, color=C_DARK, align=PP_ALIGN.LEFT, italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def _add_textbox(slide, text, l, t, w, h, size=11, bold=False,
                 color=C_DARK, align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    _tf(txb, text, size, bold, color, align, italic)
    return txb


def _kpi_card(slide, label, value, l, t, bg_color=C_BLUE, text_color=None):
    tc = text_color if text_color else get_contrast_color(bg_color)
    _add_rect(slide, l, t, 2.1, 1.1, bg_color)
    _add_textbox(slide, label, l + 0.1, t + 0.08, 1.9, 0.35,
                 size=9, color=tc, bold=False)
    _add_textbox(slide, value, l + 0.1, t + 0.42, 1.9, 0.55,
                 size=18, bold=True, color=tc)


# ── Slide 1: Title Slide ──────────────────────────────────────────────────────
def slide_title(prs, report_name="2024 Annual Sales Report", subtitle="Automated Analytics Report",
                note: str = None, accent_color=None, logo_path=None, brand_name: str = None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # blank layout

    # Background
    bg_primary = accent_color if accent_color else C_BLUE
    _add_rect(slide, 0, 0, 13.33, 7.5, bg_primary)
    # Accent bottom strip
    _add_rect(slide, 0, 5.8, 13.33, 1.7, C_DARK)

    # Luminance contrast check for title slide content
    text_c = get_contrast_color(bg_primary)

    # Brand header logic: white-label support
    if brand_name:
        brand_header = f"📊 {brand_name}"
    elif logo_path and os.path.exists(logo_path):
        brand_header = ""
    else:
        brand_header = "📊 Analytics AutoPilot"

    if brand_header:
        _add_textbox(slide, brand_header,
                     0.5, 1.2, 12, 0.8, size=16, bold=False, color=text_c)

    _add_textbox(slide, report_name,
                 0.5, 2.1, 12, 1.5, size=36, bold=True, color=text_c)
    _add_textbox(slide, subtitle,
                 0.5, 3.8, 12, 0.6, size=16, color=text_c)
    _add_textbox(slide, "Executive Edition  |  Confidential",
                 0.5, 6.2, 8, 0.5, size=11, color=C_WHITE, italic=True)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(10.2), Inches(0.8), height=Inches(1.2))
        except Exception as e:
            print(f"⚠️ Could not stamp logo on title slide: {e}")

    if note:
        try:
            slide.notes_slide.notes_text_frame.text = str(note)
        except Exception:
            pass

    return slide


# ── Slide 2: KPI Overview ─────────────────────────────────────────────────────
def slide_kpis(prs, kpis, insights, meta: dict = None, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_DARK
    _add_rect(slide, 0, 0, 13.33, 1.1, header_color)

    header_text_color = get_contrast_color(header_color)
    _add_textbox(slide, "Executive KPI Summary",
                 0.4, 0.2, 10, 0.75, size=24, bold=True, color=header_text_color)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.2), height=Inches(0.7))
        except Exception:
            pass

    meta = meta or {}
    sym = meta.get("currency_symbol", "$")
    rev_label = meta.get("rev_label", "Total Revenue")
    profit_label = meta.get("profit_label", "Total Profit")
    margin_label = meta.get("margin_label", "Profit Margin")
    volume_label = meta.get("volume_label", "Total Orders")
    aov_label = meta.get("aov_label", "Avg Order Value")

    def _fmt_kpi(v, prefix="$"):
        if v is None: return "N/A"
        abs_v = abs(v)
        if abs_v >= 1_000_000_000_000:
            return f"{prefix}{v/1_000_000_000_000:.2f}T"
        elif abs_v >= 1_000_000_000:
            return f"{prefix}{v/1_000_000_000:.2f}B"
        elif abs_v >= 100_000_000:
            return f"{prefix}{v/1_000_000:.1f}M"
        return f"{prefix}{v:,.0f}"

    # Row 1 — 4 KPI cards
    profit_display = _fmt_kpi(kpis.get("total_profit"), sym) if kpis.get("total_profit") is not None else "N/A"
    margin_display = kpis.get("efficiency_display") or (f"{kpis['profit_margin']}%" if kpis.get("profit_margin") is not None else "N/A")

    primary_kpi_color = accent_color if accent_color else C_BLUE
    cards_r1 = [
        (rev_label,     _fmt_kpi(kpis.get("total_revenue"), sym),  0.3,  primary_kpi_color),
        (profit_label,  profit_display,                     2.65, C_GREEN),
        (margin_label,  margin_display,                     5.0,  C_PURPLE),
        (volume_label,  f"{kpis['total_orders']:,}",        7.35, C_AMBER),
    ]
    for label, val, left, color in cards_r1:
        _kpi_card(slide, label, val, left, 1.4, color)

    # Row 2 — Dynamic KPI cards (hides Return Rate or Total Units if columns are not mapped)
    has_returns = kpis.get("has_returns", False)
    has_units = kpis.get("has_units", False)

    cards_r2_data = [
        (aov_label, (f"{sym}{kpis['avg_order_value']:,.2f}" if kpis.get("avg_order_value") is not None else "N/A"), primary_kpi_color)
    ]
    if has_returns:
        cards_r2_data.append(("Return Rate", f"{kpis['return_rate']}%", C_AMBER))
    if has_units:
        cards_r2_data.append(("Total Units", f"{kpis['total_units']:,}", C_GREEN))

    # Dynamically space Row 2 cards
    num_r2 = len(cards_r2_data)
    if num_r2 == 1:
        positions_r2 = [5.0]
    elif num_r2 == 2:
        positions_r2 = [3.85, 6.2]
    else:
        positions_r2 = [1.5, 3.85, 6.2]

    for (label, val, color), left in zip(cards_r2_data, positions_r2):
        _kpi_card(slide, label, val, left, 2.75, color)

    # Key highlights section
    _add_rect(slide, 0.3, 4.1, 12.7, 2.9, C_LIGHT)
    _add_textbox(slide, "🔍  Key Highlights",
                 0.5, 4.2, 12, 0.5, size=13, bold=True, color=C_DARK)

    bullets = [
        f"📈  Best performing period: {insights.get('best_month', 'N/A')}",
        f"🏷️   Top vertical ({insights.get('top_basis', 'highest revenue')}): {insights.get('top_category', 'N/A')}  |  Top region: {insights.get('top_region', 'N/A')}",
    ]
    if insights.get("anomaly_headline") and insights.get("has_anomalies"):
        bullets.append(f"⚠️  {insights['anomaly_headline']}")
    if insights.get("top_channel") and insights.get("top_channel") != "N/A":
        bullets.append(f"🛒  Dominant channel: {insights['top_channel']}")

    for i, b in enumerate(bullets):
        _add_textbox(slide, b, 0.6, 4.7 + i * 0.5, 12.4, 0.45, size=12, color=C_DARK)

    if note:
        try:
            slide.notes_slide.notes_text_frame.text = str(note)
        except Exception:
            pass

    return slide


# ── Slide 3: Monthly Trend ────────────────────────────────────────────────────
def slide_trend(prs, chart_path, insights, title: str = None, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_BLUE
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)

    header_text_color = get_contrast_color(header_color)
    slide_title_text = title or insights.get("trend_title", "Performance Trajectory & Trend")
    _add_textbox(slide, slide_title_text,
                 0.4, 0.15, 10, 0.75, size=22, bold=True, color=header_text_color)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    # Pass ONLY width to python-pptx so aspect ratio is preserved without vertical distortion
    slide.shapes.add_picture(chart_path, Inches(0.4), Inches(1.2), width=Inches(12.5))

    # Notes are kept strictly in PowerPoint's native Presenter Notes pane
    if not note:
        horizon_desc = insights.get("horizon_desc", "performance trajectory")
        best_p = insights.get("best_period", insights.get("best_month", "N/A"))
        worst_p = insights.get("worst_period", insights.get("worst_month", "N/A"))
        guidance = insights.get("period_guidance", "We recommend planning resource and operational allocation accordingly.")
        note = (f"This chart displays {horizon_desc}. "
                f"Peak performance was achieved in {best_p}, while {worst_p} "
                f"recorded lowest activity. {guidance}")
    if note:
        try:
            slide.notes_slide.notes_text_frame.text = str(note)
        except Exception:
            pass
    return slide


# ── Slide 4: Category & Product ───────────────────────────────────────────────
def slide_category_products(prs, chart_cat, chart_prod, insights, title: str = None, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_PURPLE
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)

    header_text_color = get_contrast_color(header_color)
    slide_title_text = title or "Vertical Performance & Rankings"
    _add_textbox(slide, slide_title_text,
                 0.4, 0.15, 12, 0.75, size=22, bold=True, color=header_text_color)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    # Pass ONLY width so both category and product charts preserve native aspect ratio (donuts stay circular!)
    slide.shapes.add_picture(chart_cat,  Inches(0.25), Inches(1.2), width=Inches(6.2))
    slide.shapes.add_picture(chart_prod, Inches(6.85), Inches(1.2), width=Inches(6.2))

    # Key takeaways panel under the charts (fills the lower half of the slide)
    _add_rect(slide, 0.3, 4.65, 12.7, 2.5, C_LIGHT)
    _add_textbox(slide, "🔍  Key Takeaways", 0.5, 4.72, 12, 0.45, size=13, bold=True, color=C_DARK)
    basis = insights.get("top_basis", "highest revenue")
    points = [
        f"Top category by {basis}: {insights.get('top_category', 'N/A')}",
        f"Top region by {basis}: {insights.get('top_region', 'N/A')}",
        f"Strongest period: {insights.get('best_month', 'N/A')}  |  Softest period: {insights.get('worst_month', 'N/A')}",
    ]
    for i, pt in enumerate(points):
        _add_textbox(slide, "•  " + pt, 0.6, 5.25 + i * 0.55, 12.2, 0.5, size=12, color=C_DARK)

    # Notes are kept strictly in PowerPoint's native Presenter Notes pane
    if not note:
        note = (f"{insights.get('top_category', 'Top category')} has the {insights.get('top_basis', 'highest revenue')} among categories.")
    if note:
        try:
            slide.notes_slide.notes_text_frame.text = str(note)
        except Exception:
            pass
    return slide


# ── Slide 5: Regional Insights & Recommendations ─────────────────────────────
def slide_region_recommendations(prs, chart_region, insights, title: str = None, recs: list = None, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_GREEN
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)

    header_text_color = get_contrast_color(header_color)
    slide_title_text = title or "Geographic Distribution & Strategic Recommendations"
    _add_textbox(slide, slide_title_text,
                 0.4, 0.15, 12, 0.75, size=20, bold=True, color=header_text_color)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    # Pass ONLY width so donut chart stays a true circle
    slide.shapes.add_picture(chart_region, Inches(0.25), Inches(1.2), width=Inches(5.8))

    if not recs:
        recs = [
            ("📍  Top Region",    f"{insights.get('top_region', 'Primary region')} has the {insights.get('top_basis', 'highest revenue')} — review it first when planning."),
            ("📈  Peak Period",   f"{insights.get('best_month', 'The peak period')} was the strongest period in this data."),
            ("⚠️   Weak Period",  f"{insights.get('worst_month', 'The weakest period')} was the softest period — check what drove it."),
            ("🧭  Next Step",     "Compare these figures with your targets before deciding where to invest."),
        ]
    for i, (title_item, body) in enumerate(recs[:4]):
        top = 1.2 + i * 1.5
        _add_rect(slide, 6.4, top, 6.7, 1.3, C_LIGHT)
        _add_textbox(slide, title_item, 6.6, top + 0.08, 6.4, 0.38, size=11, bold=True, color=C_BLUE)
        _add_textbox(slide, body,  6.6, top + 0.48, 6.4, 0.75, size=10, color=C_DARK)

    if not note:
        note = (f"This slide provides regional distribution and actionable recommendations. "
                f"Top region by {insights.get('top_basis', 'revenue')} is {insights.get('top_region', 'N/A')}.")
    if note:
        try:
            slide.notes_slide.notes_text_frame.text = str(note)
        except Exception:
            pass

    return slide


# ── Master builder ─────────────────────────────────────────────────────────────
def build_presentation(report_data: dict, chart_paths: dict, report_title: str = "Analytics Executive Report",
                       narrative: dict = None, output_dir: str = None, brand_color: str = None,
                       logo_path: str = None, brand_name: str = None) -> str:
    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    kpis = report_data["kpis"]
    ins = report_data["insights"]
    meta = report_data.get("meta", {})
    mode = report_data.get("report_mode", "Sales & Retail Performance")

    notes = narrative.get("speaker_notes", {}) if narrative else {}
    custom_recs = None
    if narrative and "recommendations" in narrative:
        custom_recs = [
            (f"{r.get('tag', '')} · {r.get('title', '')}".strip(' ·'), r.get("body", ""))
            for r in narrative["recommendations"]
        ]

    accent_rgb = hex_to_rgb(brand_color) if brand_color else None

    print(f"📝  Building slide deck ({mode})...")
    subtitle_text = f"Executive Edition  |  {mode}"
    slide_title(prs, report_name=report_title, subtitle=subtitle_text, note=notes.get("slide_1"),
                accent_color=accent_rgb, logo_path=logo_path, brand_name=brand_name)
    slide_kpis(prs, kpis, ins, meta=meta, note=notes.get("slide_2"),
               accent_color=accent_rgb, logo_path=logo_path)

    trend_header = ins.get("trend_title") or meta.get("trend_title", "Monthly Trajectory & Trend")
    slide_trend(prs, chart_paths["monthly_trend"], ins, title=trend_header,
                note=notes.get("slide_3"), accent_color=accent_rgb, logo_path=logo_path)

    cat_header = f"{meta.get('category_title', 'Vertical Performance')} & Rankings"
    slide_category_products(prs, chart_paths["category"], chart_paths["top_products"], ins,
                            title=cat_header, note=notes.get("slide_4"),
                            accent_color=accent_rgb, logo_path=logo_path)

    reg_header = f"{meta.get('region_title', 'Regional Distribution')} & Recommendations"
    slide_region_recommendations(prs, chart_paths["region"], ins, title=reg_header,
                                 recs=custom_recs, note=notes.get("slide_5"),
                                 accent_color=accent_rgb, logo_path=logo_path)

    target_dir = output_dir or OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, "Analytics_Report.pptx")
    prs.save(out_path)
    print(f"  ✅  Deck saved → {out_path}")
    return out_path


if __name__ == "__main__":
    from analysis_engine import build_report
    from chart_engine import generate_all_charts

    path = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    report = build_report(path)
    charts = generate_all_charts(report)
    build_presentation(report, charts)
