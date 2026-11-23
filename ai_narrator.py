"""
ai_narrator.py
AI Narrative Engine for Analytics AutoPilot.
Integrates with Google Gemini via the official google-genai SDK.

Architecture Principles:
1. Math is Deterministic: Gemini is the executive narrator, NEVER the math engine.
   Only verified KPI and insight dictionaries from analysis_engine.py are passed.
2. Crash-Proof Fallback: Returns structured deterministic template narratives if
   no API key is provided or if network/API calls fail.
3. Clean Token Budget: Feeds compact summary JSON (~250 tokens), avoiding raw row data leaks.
"""

import os
import json
from dotenv import load_dotenv

# Load local environment variables from .env if present
load_dotenv()


def get_gemini_api_key() -> str | None:
    """
    Safely retrieves the Gemini API key from environment variables or Streamlit secrets.
    Does not crash if secrets.toml or environment variables are missing.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key.strip()

    # Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"].strip()
    except Exception:
        pass

    return None


def get_deterministic_fallback(report_data: dict, report_title: str = "Executive Report") -> dict:
    """
    Provides boardroom-ready narrative content deterministically.
    Guarantees the app and slide generator always function smoothly.
    """
    kpis = report_data.get("kpis", {})
    ins = report_data.get("insights", {})

    total_revenue = kpis.get("total_revenue", 0.0)
    profit_margin = kpis.get("profit_margin")
    avg_order_val = kpis.get("avg_order_value", 0.0)
    total_orders = kpis.get("total_orders", 0)
    best_month = ins.get("best_month", "Q4 Peak")
    worst_month = ins.get("worst_month", "Off-Peak")
    top_cat = ins.get("top_category", "Core Offerings")
    top_region = ins.get("top_region", "Primary Market")

    margin_str = f"{profit_margin:.1f}%" if profit_margin is not None else "healthy"
    rev_str = f"${total_revenue:,.0f}" if total_revenue else "$0"
    aov_str = f"${avg_order_val:,.2f}" if avg_order_val else "$0"

    return {
        "status": "fallback",
        "executive_summary": (
            f"During this performance cycle, gross revenue reached {rev_str} across {total_orders:,} transactions. "
            f"Portfolio velocity was led by {top_cat}, while {top_region} remained the primary regional demand anchor."
        ),
        "takeaways": [
            {
                "icon": "📈",
                "title": "Peak Cycle Discovery",
                "body": f"{best_month} drove the highest revenue velocity. Allocate marketing budget and inventory ramp-ups 45 days prior to this window."
            },
            {
                "icon": "🏆",
                "title": "Core Growth Driver",
                "body": f"{top_cat} outperforms all other product lines in revenue generation. Expand unit selection in this vertical."
            },
            {
                "icon": "📍",
                "title": "Geographic Density",
                "body": f"{top_region} commands highest market share. Evaluate localized partnerships and express fulfillment in this region."
            }
        ],
        "recommendations": [
            {
                "tag": "1. Regional Scale",
                "title": f"Expand Distribution in {top_region}",
                "body": f"Prioritize marketing spend and regional fulfillment in {top_region} to maximize market capture.",
                "accent": "#6366F1"
            },
            {
                "tag": "2. Margin Defense",
                "title": "Protect Margin Thresholds",
                "body": f"Maintain disciplined pricing to defend our {margin_str} margin tier across key supply channels.",
                "accent": "#34D399"
            },
            {
                "tag": "3. Seasonality Bridge",
                "title": f"Mitigate {worst_month} Contraction",
                "body": f"Deploy targeted promotional incentives and bundle releases to lift volume during the {worst_month} trough.",
                "accent": "#F87171"
            },
            {
                "tag": "4. Basket Optimization",
                "title": "Elevate Average Order Value",
                "body": f"Introduce cross-sell bundles at checkout to expand order value beyond current benchmark ({aov_str}).",
                "accent": "#FBBF24"
            }
        ],
        "speaker_notes": {
            "slide_1": f"Welcome everyone. Today we are reviewing our executive performance report for {report_title}. We will walk through our high-level KPIs, seasonal trends, category margin health, and strategic growth priorities.",
            "slide_2": f"Slide 2 outlines our bottom-line numbers. Gross revenue closed at {rev_str} across {total_orders:,} orders with an average order value of {aov_str}. Margins remain at {margin_str}, giving us solid runway for reinvestment.",
            "slide_3": f"Looking at seasonality on slide 3: our peak performance hit in {best_month}. Conversely, {worst_month} showed our seasonal trough. We recommend timing next year's promotional budget to hedge this exact slow period.",
            "slide_4": f"On slide 4, {top_cat} is our clear anchor category. Our recommendation here is to double down on inventory depth for our top SKUs while reviewing cost structures for trailing categories.",
            "slide_5": f"Finally, slide 5 gives leadership four immediate action items: First, capture more market share in {top_region}; second, protect our margins; third, launch campaigns to lift {worst_month}; and fourth, test bundle add-ons to increase order size."
        }
    }


def generate_narrative(report_data: dict, report_title: str = "Executive Report", api_key: str = None) -> dict:
    """
    Calls the Gemini API (gemini-2.5-flash) using structured output.
    Returns a dictionary with executive_summary, takeaways, recommendations, and speaker_notes.
    Falls back gracefully if the API key is not present or an error occurs.
    """
    resolved_key = api_key or get_gemini_api_key()
    if not resolved_key:
        print("ℹ️  No Gemini API key found. Using deterministic template narrative.")
        return get_deterministic_fallback(report_data, report_title)

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)

        # Build compact mathematical summary payload
        kpis = report_data.get("kpis", {})
        ins = report_data.get("insights", {})

        payload = {
            "report_title": report_title,
            "total_revenue": kpis.get("total_revenue"),
            "total_profit": kpis.get("total_profit"),
            "profit_margin_pct": kpis.get("profit_margin"),
            "total_orders": kpis.get("total_orders"),
            "avg_order_value": kpis.get("avg_order_value"),
            "best_performing_month": ins.get("best_month"),
            "lowest_performing_month": ins.get("worst_month"),
            "avg_mom_growth_pct": ins.get("avg_mom_growth"),
            "top_category": ins.get("top_category"),
            "top_region": ins.get("top_region"),
            "top_channel": ins.get("top_channel"),
        }

        prompt = f"""
You are an elite C-Suite Strategy Consultant and Chief Financial Officer.
Analyze the following verified financial and business performance data and provide strategic boardroom commentary:

VERIFIED DATA (Do NOT invent or alter any numbers):
{json.dumps(payload, indent=2)}

Requirements:
1. executive_summary: A 2-3 sentence strategic executive briefing highlighting financial health, peak performance, and strategic outlook.
2. takeaways: An array of exactly 3 insight items. Each item must have:
   - "icon": an appropriate emoji (e.g., "📈", "🏆", "📍")
   - "title": a 3-5 word executive label
   - "body": 1-2 concise, high-impact analytical sentences
3. recommendations: An array of exactly 4 prioritized, actionable strategic recommendations for leadership. Each item must have:
   - "tag": formatted as "1. Category", "2. Category", etc.
   - "title": concise action-oriented title
   - "body": specific commercial instruction (1-2 sentences)
   - "accent": hex color (choose from #6366F1, #34D399, #F87171, #FBBF24)
4. speaker_notes: An object containing slide-by-slide presenter scripts for 5 slides:
   - "slide_1": Warm boardroom welcome, framing the agenda.
   - "slide_2": Commentary on bottom-line numbers, revenue, margins, and order volume.
   - "slide_3": Momentum, peak month seasonality, and trough mitigation.
   - "slide_4": Product category dominance and SKU mix strategy.
   - "slide_5": Executive call to action detailing the next operational steps.

Tone: Professional, incisive, data-backed, boardroom-ready.
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )

        result = json.loads(response.text)
        result["status"] = "ai_generated"
        return result

    except Exception as e:
        print(f"⚠️  Gemini API call failed ({e}). Falling back to deterministic narrative.")
        fallback = get_deterministic_fallback(report_data, report_title)
        fallback["error"] = str(e)
        return fallback


if __name__ == "__main__":
    from analysis_engine import build_report
    path = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    rep = build_report(path)
    nar = generate_narrative(rep, "2024 Annual Performance Report")
    print(f"\nNarrative Status: {nar['status']}")
    print(f"Executive Summary:\n{nar['executive_summary']}\n")
    print("Recommendations:")
    for r in nar["recommendations"]:
        print(f"  - [{r['tag']}] {r['title']}: {r['body']}")
