"""
slide_builder.py
Assembles the final PowerPoint deck from charts, KPIs, and AI insights.
Output: output/Analytics_Report.pptx
"""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import os

# ── Colours (matching chart_engine palette) ───────────────────────────────────
C_BLUE   = RGBColor(0x25, 0x63, 0xEB)
C_PURPLE = RGBColor(0x7C, 0x3A, 0xED)
C_GREEN  = RGBColor(0x10, 0xB9, 0x81)
C_AMBER  = RGBColor(0xF5, 0x9E, 0x0B)
C_WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
C_DARK   = RGBColor(0x1E, 0x29, 0x3B)
C_LIGHT  = RGBColor(0xF8, 0xFA, 0xFC)
C_GRAY   = RGBColor(0x64, 0x74, 0x8B)

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


def _add_rect(slide, l, t, w, h, color):
    shape = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()
    return shape


def _tf(shape, text, size, bold=False, color=C_DARK, align=PP_ALIGN.LEFT, italic=False):
    tf = shape.text_frame
    tf.word_wrap = True
    p  = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.size   = Pt(size)
    run.font.bold   = bold
    run.font.italic = italic
    run.font.color.rgb = color


def _add_textbox(slide, text, l, t, w, h, size=11, bold=False,
                  color=C_DARK, align=PP_ALIGN.LEFT, italic=False):
    txb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    _tf(txb, text, size, bold, color, align, italic)
    return txb


def _kpi_card(slide, label, value, l, t, bg_color=C_BLUE):
    _add_rect(slide, l, t, 2.1, 1.1, bg_color)
    _add_textbox(slide, label, l+0.1, t+0.08, 1.9, 0.35,
                  size=9, color=C_WHITE, bold=False)
    _add_textbox(slide, value, l+0.1, t+0.42, 1.9, 0.55,
                  size=18, bold=True, color=C_WHITE)


# ── Slide 1: Title Slide ──────────────────────────────────────────────────────
def slide_title(prs, report_name="2024 Annual Sales Report", subtitle="Automated Analytics Report", accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])   # blank layout

    # Background
    bg_primary = accent_color if accent_color else C_BLUE
    _add_rect(slide, 0, 0, 13.33, 7.5, bg_primary)
    # Accent strip
    _add_rect(slide, 0, 5.8, 13.33, 1.7, C_DARK)

    _add_textbox(slide, "📊 Analytics AutoPilot",
                 0.5, 1.2, 12, 0.8, size=16, bold=False, color=C_WHITE)
    _add_textbox(slide, report_name,
                 0.5, 2.1, 12, 1.5, size=36, bold=True, color=C_WHITE)
    _add_textbox(slide, subtitle,
                 0.5, 3.8, 12, 0.6, size=16, color=C_WHITE)
    _add_textbox(slide, "Executive Edition  |  Confidential",
                 0.5, 6.2, 8, 0.5, size=11, color=C_WHITE, italic=True)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(10.2), Inches(0.8), height=Inches(1.2))
        except Exception as e:
            print(f"⚠️ Could not stamp logo on title slide: {e}")

    return slide


# ── Slide 2: KPI Overview ─────────────────────────────────────────────────────
def slide_kpis(prs, kpis, insights, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_DARK
    _add_rect(slide, 0, 0, 13.33, 1.1, header_color)
    _add_textbox(slide, "Executive KPI Summary",
                 0.4, 0.2, 10, 0.75, size=24, bold=True, color=C_WHITE)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.2), height=Inches(0.7))
        except Exception:
            pass

    # Row 1 — 4 KPI cards
    profit_display = f"${kpis['total_profit']:,.0f}" if kpis.get("total_profit") is not None else "N/A"
    margin_display = f"{kpis['profit_margin']}%" if kpis.get("profit_margin") is not None else "N/A"

    primary_kpi_color = accent_color if accent_color else C_BLUE
    cards_r1 = [
        ("Total Revenue",   f"${kpis['total_revenue']:,.0f}",  0.3,  primary_kpi_color),
        ("Total Profit",    profit_display,                     2.65, C_GREEN),
        ("Profit Margin",   margin_display,                     5.0,  C_PURPLE),
        ("Total Orders",    f"{kpis['total_orders']:,}",        7.35, C_AMBER),
    ]
    for label, val, left, color in cards_r1:
        _kpi_card(slide, label, val, left, 1.4, color)

    # Row 2 — 3 KPI cards
    cards_r2 = [
        ("Avg Order Value",  f"${kpis['avg_order_value']:,.2f}",  1.5,  primary_kpi_color),
        ("Return Rate",      f"{kpis['return_rate']}%",            3.85, C_AMBER),
        ("Total Units Sold", f"{kpis['total_units']:,}",           6.2,  C_GREEN),
    ]
    for label, val, left, color in cards_r2:
        _kpi_card(slide, label, val, left, 2.75, color)

    # Key highlights section
    _add_rect(slide, 0.3, 4.1, 12.7, 2.9, C_LIGHT)
    _add_textbox(slide, "🔍  Key Highlights",
                 0.5, 4.2, 12, 0.5, size=13, bold=True, color=C_DARK)

    bullets = [
        f"📈  Best performing month: {insights['best_month']}",
        f"🏷️   Top revenue category: {insights['top_category']}  |  Top region: {insights['top_region']}",
        f"🛒  Dominant sales channel: {insights['top_channel']}",
    ]
    for i, b in enumerate(bullets):
        _add_textbox(slide, b, 0.6, 4.75 + i * 0.65, 12.4, 0.5, size=12, color=C_DARK)

    return slide


# ── Slide 3: Monthly Trend ────────────────────────────────────────────────────
def slide_trend(prs, chart_path, insights, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_BLUE
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)
    _add_textbox(slide, "Monthly Revenue & Profit Trend",
                 0.4, 0.15, 10, 0.75, size=22, bold=True, color=C_WHITE)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    slide.shapes.add_picture(chart_path, Inches(0.3), Inches(1.1),
                              Inches(12.7), Inches(4.5))

    _add_rect(slide, 0.3, 5.75, 12.7, 1.55, C_LIGHT)
    _add_textbox(slide, "Speaker Notes:",
                 0.5, 5.82, 12, 0.35, size=9, bold=True, color=C_GRAY)
    if not note:
        note = (f"This chart shows monthly Revenue (blue) and Profit (green) for 2024. "
                f"Our peak revenue month was {insights['best_month']}, while {insights['worst_month']} "
                f"recorded the lowest performance. We should investigate seasonal drivers and ensure "
                f"inventory and campaigns are aligned with our peak months next year.")
    _add_textbox(slide, note, 0.5, 6.15, 12.5, 1.1, size=10, color=C_DARK)
    return slide


# ── Slide 4: Category & Product ───────────────────────────────────────────────
def slide_category_products(prs, chart_cat, chart_prod, insights, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_PURPLE
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)
    _add_textbox(slide, "Category Performance & Top Products",
                 0.4, 0.15, 12, 0.75, size=22, bold=True, color=C_WHITE)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    slide.shapes.add_picture(chart_cat,  Inches(0.15), Inches(1.05), Inches(6.6),  Inches(4.0))
    slide.shapes.add_picture(chart_prod, Inches(6.85), Inches(1.05), Inches(6.3),  Inches(4.0))

    _add_rect(slide, 0.15, 5.2, 12.7, 2.1, C_LIGHT)
    _add_textbox(slide, "Speaker Notes:",
                 0.4, 5.28, 12, 0.35, size=9, bold=True, color=C_GRAY)
    if not note:
        note = (f"{insights['top_category']} leads all categories by revenue. "
                f"Focus on expanding the product range within this category and "
                f"investigate whether lower-margin categories can be optimized on the cost side. "
                f"The top 5 products should be prioritised in restocking and marketing campaigns.")
    _add_textbox(slide, note, 0.4, 5.6, 12.5, 1.5, size=10, color=C_DARK)
    return slide


# ── Slide 5: Regional Insights & Recommendations ─────────────────────────────
def slide_region_recommendations(prs, chart_region, insights, recs: list = None, note: str = None, accent_color=None, logo_path=None):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    header_color = accent_color if accent_color else C_GREEN
    _add_rect(slide, 0, 0, 13.33, 1.0, header_color)
    _add_textbox(slide, "Regional Revenue & Strategic Recommendations",
                 0.4, 0.15, 12, 0.75, size=20, bold=True, color=C_WHITE)

    if logo_path and os.path.exists(logo_path):
        try:
            slide.shapes.add_picture(logo_path, Inches(11.8), Inches(0.18), height=Inches(0.64))
        except Exception:
            pass

    slide.shapes.add_picture(chart_region, Inches(0.2), Inches(1.1),
                              Inches(5.8), Inches(5.5))

    if not recs:
        recs = [
            ("📍  Top Region",    f"{insights['top_region']} leads in revenue — prioritize this region for new product launches."),
            ("🛒  Best Channel",  f"{insights['top_channel']} is the dominant sales channel. Invest in UX/conversion optimization here."),
            ("📈  Growth Driver", f"Focus on upsell campaigns during peak months ({insights['best_month']}) for maximum impact."),
            ("⚠️   Weak Period",  f"Revenue dips in {insights['worst_month']}. Consider targeted promotions or bundle deals during this period."),
        ]
    for i, (title, body) in enumerate(recs[:4]):
        top = 1.2 + i * 1.5
        _add_rect(slide, 6.4, top, 6.7, 1.3, C_LIGHT)
        _add_textbox(slide, title, 6.6, top + 0.08, 6.4, 0.38, size=11, bold=True, color=C_BLUE)
        _add_textbox(slide, body,  6.6, top + 0.48, 6.4, 0.75, size=10, color=C_DARK)

    return slide


# ── Master builder ─────────────────────────────────────────────────────────────
def build_presentation(report_data: dict, chart_paths: dict, report_title: str = "Analytics Executive Report", narrative: dict = None, output_dir: str = None, brand_color: str = None, logo_path: str = None) -> str:
    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    kpis    = report_data["kpis"]
    ins     = report_data["insights"]

    notes = narrative.get("speaker_notes", {}) if narrative else {}
    custom_recs = None
    if narrative and "recommendations" in narrative:
        custom_recs = [
            (f"{r.get('tag', '')} · {r.get('title', '')}".strip(' ·'), r.get("body", ""))
            for r in narrative["recommendations"]
        ]

    accent_rgb = hex_to_rgb(brand_color) if brand_color else None

    print("📝  Building slide deck...")
    slide_title(prs, report_name=report_title, accent_color=accent_rgb, logo_path=logo_path)
    slide_kpis(prs, kpis, ins, accent_color=accent_rgb, logo_path=logo_path)
    slide_trend(prs, chart_paths["monthly_trend"], ins, note=notes.get("slide_3"), accent_color=accent_rgb, logo_path=logo_path)
    slide_category_products(prs, chart_paths["category"], chart_paths["top_products"], ins, note=notes.get("slide_4"), accent_color=accent_rgb, logo_path=logo_path)
    slide_region_recommendations(prs, chart_paths["region"], ins, recs=custom_recs, note=notes.get("slide_5"), accent_color=accent_rgb, logo_path=logo_path)

    target_dir = output_dir or OUTPUT_DIR
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, "Analytics_Report.pptx")
    prs.save(out_path)
    print(f"  ✅  Deck saved → {out_path}")
    return out_path


if __name__ == "__main__":
    from analysis_engine import build_report
    from chart_engine     import generate_all_charts
    import os

    path   = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    report = build_report(path)
    charts = generate_all_charts(report)
    build_presentation(report, charts)
