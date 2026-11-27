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
4. Structured Outputs: Uses Pydantic schema validation for guaranteed response shapes.
"""

import os
import json
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load local environment variables from .env if present
load_dotenv()


class TakeawayItem(BaseModel):
    icon: str = Field(description="A single relevant emoji, e.g. 🎯, 📈, ⚡, 📍")
    title: str = Field(description="3-5 word executive takeaway title")
    body: str = Field(description="1-2 concise, high-impact data-backed analytical sentences")


class RecommendationItem(BaseModel):
    tag: str = Field(description="Formatted priority category, e.g. '1. Regional Scale'")
    title: str = Field(description="Concise action-oriented strategic initiative title")
    body: str = Field(description="Specific actionable commercial instruction (1-2 sentences)")
    accent: str = Field(description="Hex color from #6366F1, #34D399, #F87171, #FBBF24")


class SpeakerNotes(BaseModel):
    slide_1: str = Field(description="Warm boardroom welcome and executive agenda")
    slide_2: str = Field(description="Commentary on bottom-line figures and efficiency")
    slide_3: str = Field(description="Seasonal momentum, peak window, and trough hedging")
    slide_4: str = Field(description="Category and channel contribution analysis")
    slide_5: str = Field(description="Four strategic executive action items")


class ExecutiveNarrativeSchema(BaseModel):
    executive_summary: str = Field(description="2-3 sentence strategic executive briefing grounded in verified numbers")
    takeaways: list[TakeawayItem] = Field(description="Exactly 3 key takeaways")
    recommendations: list[RecommendationItem] = Field(description="Exactly 4 strategic recommendations")
    speaker_notes: SpeakerNotes = Field(description="Presenter scripts for slides 1 to 5")


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


def get_deterministic_fallback(
    report_data: dict,
    report_title: str = "Executive Report",
    report_mode: str = None,
    currency_symbol: str = "$",
    **kwargs
) -> dict:
    """
    Deterministic template fallback when Gemini API key is missing or calls fail.
    Dynamically adapts boardroom narrative tone to the selected Report Mode and currency.
    """
    kpis = report_data.get("kpis", {})
    ins = report_data.get("insights", {})
    mode = report_mode or report_data.get("report_mode", "Sales & Retail Performance")
    curr = currency_symbol or report_data.get("meta", {}).get("currency_symbol", "$")

    total_revenue = kpis.get("total_revenue", 0.0)
    profit_margin = kpis.get("profit_margin")
    avg_order_val = kpis.get("avg_order_value", 0.0)
    total_orders = kpis.get("total_orders", 0)
    best_month = ins.get("best_month", "Peak Period")
    worst_month = ins.get("worst_month", "Off-Peak Period")
    top_cat = ins.get("top_category", "Core Vertical")
    top_region = ins.get("top_region", "Primary Market")
    basis = ins.get("top_basis", "highest revenue")

    anom_list = ins.get("anomalies", [])
    anom_phrase = f" Notably, {anom_list[0]['period']} recorded an abnormal {anom_list[0]['type'].lower()} ({anom_list[0]['pct_diff_mean']:+.1f}% vs. baseline)." if anom_list else ""

    rev_str = f"{curr}{total_revenue:,.0f}" if total_revenue else f"{curr}0"
    aov_str = f"{curr}{avg_order_val:,.2f}" if avg_order_val else "N/A"

    eff_display = kpis.get("efficiency_display")
    if not eff_display:
        margin_str = f"{profit_margin:.1f}%" if profit_margin is not None else "healthy"
    else:
        margin_str = eff_display

    if "Marketing" in mode:
        return {
            "status": "fallback",
            "report_mode": mode,
            "executive_summary": (
                f"During this campaign cycle, total ad spend reached {rev_str} recording {total_orders:,} conversions. "
                f"{top_cat} received the {basis} among channels/campaigns, and {top_region} the {basis} among markets.{anom_phrase}"
            ),
            "takeaways": [
                {
                    "icon": "🎯",
                    "title": "Peak Spend Period",
                    "body": f"{best_month} was the period of highest ad spend. Review whether results in that window justified the investment."
                },
                {
                    "icon": "🚀",
                    "title": "Largest Channel by Spend",
                    "body": f"{top_cat} took the {basis}. Compare its cost per conversion with other channels before shifting more budget."
                },
                {
                    "icon": "📍",
                    "title": "Primary Geography",
                    "body": f"{top_region} took the {basis} among markets. Check its return against spend before scaling."
                }
            ],
            "recommendations": [
                {
                    "tag": "1. Scale Top Funnel",
                    "title": f"Expand Media Spend in {top_region}",
                    "body": f"Test incremental budget in {top_region} and track cost per acquisition to confirm returns hold.",
                    "accent": "#6366F1"
                },
                {
                    "tag": "2. CAC Optimization",
                    "title": "Refine Audience Thresholds",
                    "body": f"Maintain disciplined bid caps to keep return efficiency ({margin_str}) at or above target across channels.",
                    "accent": "#34D399"
                },
                {
                    "tag": "3. Off-Peak Pacing",
                    "title": f"Mitigate {worst_month} Contraction",
                    "body": f"Plan targeted promotions to support volume during the {worst_month} low-spend period.",
                    "accent": "#F87171"
                },
                {
                    "tag": "4. Conversion Lift",
                    "title": "Optimize Funnel Unit Economics",
                    "body": f"A/B test landing page value propositions to improve cost per acquisition (currently {aov_str}).",
                    "accent": "#FBBF24"
                }
            ],
            "speaker_notes": {
                "slide_1": f"Welcome everyone. Today we are presenting our marketing performance review for {report_title}. We will cover overall ad spend, channel conversion efficiency, geographic response, and our scaling roadmap.",
                "slide_2": f"On slide 2, total ad spend closed at {rev_str} delivering {total_orders:,} total conversions with an average unit cost of {aov_str}. Return efficiency registered at {margin_str}.",
                "slide_3": f"Looking at monthly pacing on slide 3: {best_month} was the peak-spend period. Conversely, {worst_month} was the lowest-spend period, a natural window for creative testing.",
                "slide_4": f"Slide 4 highlights that {top_cat} is our primary volume driver. We recommend concentrating our creative budget here while reviewing lower-performing segments.",
                "slide_5": f"Finally, slide 5 gives four growth priorities: First, scale spend in {top_region}; second, preserve target efficiency benchmarks; third, launch bridging campaigns for {worst_month}; and fourth, optimize funnels to lower acquisition costs."
            }
        }
    elif "Operations" in mode:
        return {
            "status": "fallback",
            "report_mode": mode,
            "executive_summary": (
                f"Across this operational review cycle, managed budget reached {rev_str} processing {total_orders:,} operational work units. "
                f"Resource demand was concentrated in {top_cat}, with {top_region} operating as the primary regional facility anchor.{anom_phrase}"
            ),
            "takeaways": [
                {
                    "icon": "⚡",
                    "title": "Peak Throughput Cycle",
                    "body": f"{best_month} had the largest budget allocation. Make sure staffing and capacity plans cover that cycle."
                },
                {
                    "icon": "⚙️",
                    "title": "Primary Department",
                    "body": f"{top_cat} has the {basis}. Review its spending against plan."
                },
                {
                    "icon": "🏢",
                    "title": "Facility Workload",
                    "body": f"{top_region} has the {basis} among locations. Review whether spending there is on plan."
                }
            ],
            "recommendations": [
                {
                    "tag": "1. Workflow Automation",
                    "title": f"Modernize Operations in {top_region}",
                    "body": f"Standardize expense tracking in {top_region} so variances to budget are visible early.",
                    "accent": "#6366F1"
                },
                {
                    "tag": "2. OPEX Containment",
                    "title": "Defend Budget Utilization",
                    "body": f"Maintain procurement controls to safeguard our {margin_str} budget utilization target across departments.",
                    "accent": "#34D399"
                },
                {
                    "tag": "3. Capacity Balancing",
                    "title": f"Smooth {worst_month} Slack Period",
                    "body": f"Shift non-urgent maintenance, employee training, and audits into the {worst_month} lower-throughput window.",
                    "accent": "#F87171"
                },
                {
                    "tag": "4. Unit Cost Control",
                    "title": "Compress Unit Processing Cost",
                    "body": f"Standardize service vendor agreements to reduce average processing cost below the current benchmark of {aov_str}.",
                    "accent": "#FBBF24"
                }
            ],
            "speaker_notes": {
                "slide_1": f"Good morning. Today we are walking through our operations and expense performance review for {report_title}. We will examine budget allocations, departmental throughput, seasonal peaks, and operational efficiency initiatives.",
                "slide_2": f"On slide 2, total managed budget reached {rev_str} across {total_orders:,} completed tasks, with an average unit cost of {aov_str}. Budget utilization registered at {margin_str}.",
                "slide_3": f"Examining seasonal throughput on slide 3: {best_month} saw our heaviest operational volume. In contrast, {worst_month} showed lower volume, offering an ideal window for system maintenance.",
                "slide_4": f"Slide 4 breaks down our primary departments. {top_cat} commands the majority of resource allocation. We recommend standardizing processes here to unlock operational leverage.",
                "slide_5": f"Finally, slide 5 presents four operational action items: First, streamline logistics in {top_region}; second, reinforce vendor spend limits; third, balance {worst_month} downtime; and fourth, reduce average unit fulfillment costs."
            }
        }
    else:  # Sales & Retail Performance
        return {
            "status": "fallback",
            "report_mode": mode,
            "executive_summary": (
                f"During this performance cycle, gross revenue reached {rev_str} across {total_orders:,} transactions. "
                f"Portfolio velocity was led by {top_cat}, while {top_region} remained the primary regional demand anchor.{anom_phrase}"
            ),
            "takeaways": [
                {
                    "icon": "📈",
                    "title": "Peak Cycle Discovery",
                    "body": f"{best_month} drove the highest revenue velocity. Align promotional schedules and inventory readiness ahead of this window."
                },
                {
                    "icon": "🏆",
                    "title": "Core Growth Driver",
                    "body": f"{top_cat} outperforms all other categories in revenue contribution. Maintain stock depth in top units."
                },
                {
                    "icon": "📍",
                    "title": "Geographic Density",
                    "body": f"{top_region} commands highest market share. Evaluate localized fulfillment and distribution partnerships in this region."
                }
            ],
            "recommendations": [
                {
                    "tag": "1. Regional Scale",
                    "title": f"Expand Distribution in {top_region}",
                    "body": f"Prioritize marketing and regional fulfillment in {top_region} to maximize market capture.",
                    "accent": "#6366F1"
                },
                {
                    "tag": "2. Margin Defense",
                    "title": "Protect Margin Thresholds",
                    "body": f"Maintain disciplined pricing to defend our {margin_str} margin tier across key product lines.",
                    "accent": "#34D399"
                },
                {
                    "tag": "3. Seasonality Bridge",
                    "title": f"Mitigate {worst_month} Contraction",
                    "body": f"Deploy targeted incentives and bundle releases to lift volume during the {worst_month} trough.",
                    "accent": "#F87171"
                },
                {
                    "tag": "4. Basket Optimization",
                    "title": "Elevate Average Order Value",
                    "body": f"Introduce bundle recommendations to expand transaction values beyond current benchmark ({aov_str}).",
                    "accent": "#FBBF24"
                }
            ],
            "speaker_notes": {
                "slide_1": f"Welcome everyone. Today we are reviewing our executive performance report for {report_title}. We will walk through our high-level KPIs, seasonal trends, category margin health, and strategic growth priorities.",
                "slide_2": f"Slide 2 outlines our bottom-line numbers. Gross revenue closed at {rev_str} across {total_orders:,} orders with an average order value of {aov_str}. Margins remain at {margin_str}, giving us solid runway for reinvestment.",
                "slide_3": f"Looking at seasonality on slide 3: our peak performance hit in {best_month}. Conversely, {worst_month} showed our seasonal trough. We recommend timing promotional flights to hedge this slow period.",
                "slide_4": f"On slide 4, {top_cat} is our clear anchor category. Our recommendation is to prioritize inventory depth for our top items while reviewing cost structures for trailing categories.",
                "slide_5": f"Finally, slide 5 gives leadership four immediate action items: First, capture more market share in {top_region}; second, protect our margins; third, launch campaigns to lift {worst_month}; and fourth, test bundle add-ons to increase order size."
            }
        }


def validate_and_merge_narrative(narrative_dict: dict, fallback_dict: dict) -> dict:
    """
    Validates the structure of the LLM output.
    If any key or element is malformed, smoothly merges the fallback version so the app never crashes.
    """
    if not isinstance(narrative_dict, dict):
        return fallback_dict

    validated = dict(fallback_dict)

    if isinstance(narrative_dict.get("executive_summary"), str) and narrative_dict["executive_summary"].strip():
        validated["executive_summary"] = narrative_dict["executive_summary"].strip()

    if isinstance(narrative_dict.get("takeaways"), list) and len(narrative_dict["takeaways"]) >= 3:
        clean_takeaways = []
        for t in narrative_dict["takeaways"][:3]:
            if isinstance(t, dict) and "icon" in t and "title" in t and "body" in t:
                clean_takeaways.append(t)
        if len(clean_takeaways) == 3:
            validated["takeaways"] = clean_takeaways

    if isinstance(narrative_dict.get("recommendations"), list) and len(narrative_dict["recommendations"]) >= 4:
        clean_recs = []
        for r in narrative_dict["recommendations"][:4]:
            if isinstance(r, dict) and "title" in r and "body" in r:
                import re as _re
                if not _re.fullmatch(r"#[0-9A-Fa-f]{6}", str(r.get("accent", ""))):
                    r["accent"] = "#6366F1"
                clean_recs.append(r)
        if len(clean_recs) == 4:
            validated["recommendations"] = clean_recs

    if isinstance(narrative_dict.get("speaker_notes"), dict):
        sn = narrative_dict["speaker_notes"]
        for slide in ("slide_1", "slide_2", "slide_3", "slide_4", "slide_5"):
            if slide in sn and isinstance(sn[slide], str) and sn[slide].strip():
                validated["speaker_notes"][slide] = sn[slide].strip()

    validated["status"] = narrative_dict.get("status", "ai_generated")
    validated["report_mode"] = fallback_dict.get("report_mode")
    return validated


def generate_narrative(
    report_data: dict,
    report_title: str = "Executive Report",
    report_mode: str = None,
    api_key: str = None,
    currency_symbol: str = "$",
    **kwargs
) -> dict:
    """
    Calls the Gemini API using structured output with ExecutiveNarrativeSchema.
    Returns a dictionary with executive_summary, takeaways, recommendations, and speaker_notes.
    Falls back gracefully if the API key is not present or an error occurs.
    """
    mode = report_mode or report_data.get("report_mode", "Sales & Retail Performance")
    curr = currency_symbol or report_data.get("meta", {}).get("currency_symbol", "$")
    resolved_key = api_key or get_gemini_api_key()

    fallback = get_deterministic_fallback(report_data, report_title, report_mode=mode, currency_symbol=curr)

    if not resolved_key:
        print(f"ℹ️  No Gemini API key found. Using deterministic template narrative ({mode}).")
        return fallback

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        kpis = report_data.get("kpis", {})
        ins = report_data.get("insights", {})

        payload = {
            "report_title": report_title,
            "report_mode": mode,
            "currency_symbol": curr,
            "total_revenue": kpis.get("total_revenue"),
            "total_profit": kpis.get("total_profit"),
            "profit_margin": kpis.get("profit_margin"),
            "efficiency_display": kpis.get("efficiency_display"),
            "efficiency_metric_name": kpis.get("efficiency_metric_name"),
            "total_orders": kpis.get("total_orders"),
            "avg_order_value": kpis.get("avg_order_value"),
            "cmgr_pct": ins.get("cmgr"),
            "growth_label": ins.get("growth_label"),
            "best_performing_month": ins.get("best_month"),
            "lowest_performing_month": ins.get("worst_month"),
            "partial_months": ins.get("partial_months", []),
            "top_category": ins.get("top_category"),
            "top_region": ins.get("top_region"),
            "top_channel": ins.get("top_channel") if ins.get("has_channel") else None,
            "statistical_anomalies": ins.get("anomalies", []),
            "anomaly_headline": ins.get("anomaly_headline", ""),
        }

        role_personas = {
            "Marketing": "an elite Chief Marketing Officer (CMO) and Growth Strategist focusing strictly on verified ROAS, CPA, ad spend efficiency, and channel performance.",
            "Operations": "an elite Chief Operating Officer (COO) and Systems Strategist focusing strictly on verified OPEX, budget utilization, and departmental variance.",
            "Sales": "an elite Chief Commercial Officer (CCO) and Boardroom Strategist focusing strictly on verified revenue velocity, margin health, product leadership, and geographic density."
        }
        active_persona = role_personas["Marketing"] if "Marketing" in mode else (role_personas["Operations"] if "Operations" in mode else role_personas["Sales"])

        prompt = f"""
You are {active_persona}
Analyze the following verified data for this '{mode}' executive presentation and deliver incisive, boardroom-ready commentary:

VERIFIED DATA (Every dollar and unit metric must align with these values; use currency symbol '{curr}'):
{json.dumps(payload, indent=2)}

Requirements:
1. executive_summary: A 2-3 sentence strategic briefing grounded in the verified numbers. If statistical_anomalies are present, explicitly reference the top outlier surge or contraction.
2. takeaways: An array of exactly 3 data-grounded insights (icon, title, body). Do NOT make unsupported assumptions about repeat rates or unmeasured channels.
3. recommendations: An array of exactly 4 prioritized, actionable strategic recommendations (tag like '1. Category', title, body, accent from #6366F1, #34D399, #F87171, #FBBF24).
4. speaker_notes: Slide-by-slide presenter scripts for 5 slides (slide_1 through slide_5).

Tone: Professional, incisive, data-backed, boardroom-ready.
"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExecutiveNarrativeSchema,
                temperature=0.3,
            ),
        )

        parsed_json = json.loads(response.text)
        parsed_json["status"] = "ai_generated"
        return validate_and_merge_narrative(parsed_json, fallback)

    except Exception as e:
        print(f"⚠️  Gemini API call failed ({e}). Falling back to deterministic narrative.")
        fallback["error"] = str(e)
        return fallback


class ObjectiveBriefingSchema(BaseModel):
    executive_summary: str = Field(description="2-3 sentence executive briefing synthesizing the verified KPIs and findings")
    takeaways: list[TakeawayItem] = Field(description="Up to 3 concise analytical takeaways grounded in the numbers")


def make_gemini_json_caller(api_key: str):
    """Return a lightweight Callable[[str], str] for schema-only LLM planning using Gemini."""
    if not api_key:
        return None

    def _call(prompt: str) -> str:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        return resp.text or ""

    return _call


def generate_objective_briefing(kpi_cards: list, results: list, report_title: str = "Analysis Report", api_key: str = None) -> dict | None:
    """Synthesize an executive briefing & 3 takeaways from already-computed objective KPIs & Findings.
    Returns None cleanly if no key or if Gemini fails so caller uses deterministic fallback."""
    resolved_key = api_key or get_gemini_api_key()
    if not resolved_key:
        return None
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=resolved_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

        kpi_facts = [{"label": k.get("label"), "value": k.get("value"), "note": k.get("pill")} for k in (kpi_cards or [])]
        finding_facts = [
            {"question": r.spec.text, "headline": r.finding.headline, "details": r.finding.details[:2]}
            for r in (results or []) if r.finding.status in ("ok", "caution")
        ]
        prompt = (
            f"You are an elite executive business analyst writing a concise briefing for '{report_title}'.\n"
            "Synthesize ONLY the verified metrics and findings below into a sharp executive briefing (no fabricated numbers).\n\n"
            f"VERIFIED KPIs:\n{json.dumps(kpi_facts, indent=2)}\n\n"
            f"VERIFIED FINDINGS:\n{json.dumps(finding_facts, indent=2)}\n"
        )
        resp = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ObjectiveBriefingSchema,
                temperature=0.25,
            ),
        )
        data = json.loads(resp.text)
        if isinstance(data, dict) and data.get("executive_summary"):
            return data
    except Exception:
        return None
    return None


if __name__ == "__main__":
    from analysis_engine import build_report
    path = os.path.join(os.path.dirname(__file__), "sales_data.csv")
    rep = build_report(path)
    nar = generate_narrative(rep, "2024 Annual Performance Report", currency_symbol="$")
    print(f"\nNarrative Status: {nar['status']}")
    print(f"Executive Summary:\n{nar['executive_summary']}\n")
    print("Takeaways:")
    for t in nar["takeaways"]:
        print(f"  {t['icon']} {t['title']}: {t['body']}")