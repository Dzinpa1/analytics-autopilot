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


def get_deterministic_fallback(report_data: dict, report_title: str = "Executive Report", report_mode: str = None) -> dict:
    """
    Deterministic template fallback when Gemini API key is missing or calls fail.
    Dynamically adapts boardroom narrative tone to the selected Report Mode.
    """
    kpis = report_data.get("kpis", {})
    ins = report_data.get("insights", {})
    mode = report_mode or report_data.get("report_mode", "Sales & Retail Performance")

    total_revenue = kpis.get("total_revenue", 0.0)
    profit_margin = kpis.get("profit_margin")
    avg_order_val = kpis.get("avg_order_value", 0.0)
    total_orders = kpis.get("total_orders", 0)
    best_month = ins.get("best_month", "Q4 Peak")
    worst_month = ins.get("worst_month", "Off-Peak")
    top_cat = ins.get("top_category", "Core Offerings")
    top_region = ins.get("top_region", "Primary Market")

    anom_list = ins.get("anomalies", [])
    anom_phrase = f" Notably, {anom_list[0]['period']} experienced an abnormal {anom_list[0]['type'].lower()} ({anom_list[0]['pct_diff_mean']:+.1f}% vs. mean)." if anom_list else ""

    margin_str = f"{profit_margin:.1f}%" if profit_margin is not None else "healthy"
    rev_str = f"${total_revenue:,.0f}" if total_revenue else "$0"
    aov_str = f"${avg_order_val:,.2f}" if avg_order_val else "$0"

    if "Marketing" in mode:
        return {
            "status": "fallback",
            "report_mode": mode,
            "executive_summary": (
                f"During this campaign cycle, total ad spend reached {rev_str} across {total_orders:,} verified conversions. "
                f"Acquisition velocity was driven by {top_cat}, while {top_region} demonstrated the strongest regional ROAS profile.{anom_phrase}"
            ),
            "takeaways": [
                {
                    "icon": "🎯",
                    "title": "Peak Conversion Window",
                    "body": f"{best_month} generated the highest conversion velocity and lowest CPA. Structure future media flights around this window."
                },
                {
                    "icon": "🚀",
                    "title": "Top-Performing Channel",
                    "body": f"{top_cat} yields the strongest conversion efficiency. Prioritize budget allocation and creative testing in this channel."
                },
                {
                    "icon": "📍",
                    "title": "High-ROAS Geography",
                    "body": f"{top_region} delivers the lowest cost per acquisition. Deploy localized creative messaging and retargeting pools here."
                }
            ],
            "recommendations": [
                {
                    "tag": "1. Scale Top Funnel",
                    "title": f"Expand Media Spend in {top_region}",
                    "body": f"Increase budget allocation in {top_region} to capture compounding conversion demand at favorable acquisition costs.",
                    "accent": "#6366F1"
                },
                {
                    "tag": "2. CAC Optimization",
                    "title": "Refine Bid & Audience Thresholds",
                    "body": f"Maintain disciplined bid caps to safeguard our {margin_str} conversion return tier across primary ad networks.",
                    "accent": "#34D399"
                },
                {
                    "tag": "3. Off-Peak Pacing",
                    "title": f"Counteract {worst_month} Dip",
                    "body": f"Deploy promotional lead-magnet campaigns and retargeting funnels to sustain volume during the {worst_month} slowdown.",
                    "accent": "#F87171"
                },
                {
                    "tag": "4. Conversion Lift",
                    "title": "Optimize Funnel Benchmark",
                    "body": f"A/B test landing page value propositions to compress average acquisition cost below current benchmark ({aov_str}).",
                    "accent": "#FBBF24"
                }
            ],
            "speaker_notes": {
                "slide_1": f"Welcome everyone. Today we are presenting our marketing performance and campaign ROI review for {report_title}. We will cover overall ad spend, channel conversion efficiency, geographic ROAS, and our scaling roadmap.",
                "slide_2": f"On slide 2, total ad spend closed at {rev_str} delivering {total_orders:,} total conversions with an average cost per unit of {aov_str}. Return margins held at {margin_str}, indicating sustainable acquisition unit economics.",
                "slide_3": f"Looking at monthly pacing on slide 3: {best_month} delivered our highest conversion efficiency. Conversely, {worst_month} represents a seasonal lull where we must deploy strategic retargeting to smooth pacing.",
                "slide_4": f"Slide 4 highlights that {top_cat} is our primary growth driver. We recommend concentrating our creative budget here while refining bids in smaller test channels.",
                "slide_5": f"Finally, slide 5 gives four growth priorities: First, scale spend in {top_region}; second, preserve target CAC margins; third, launch bridge campaigns for {worst_month}; and fourth, test new creatives to drive down acquisition costs."
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
                    "body": f"{best_month} recorded peak operational throughput. Schedule preventive maintenance and staffing ramp-ups ahead of this cycle."
                },
                {
                    "icon": "⚙️",
                    "title": "Primary Cost Driver",
                    "body": f"{top_cat} accounts for the largest departmental expenditure. Institute workflow audits and vendor negotiations in this vertical."
                },
                {
                    "icon": "🏢",
                    "title": "Facility Workload",
                    "body": f"{top_region} handles the highest operational load. Evaluate automated tooling and workflow streamlining for this hub."
                }
            ],
            "recommendations": [
                {
                    "tag": "1. Workflow Automation",
                    "title": f"Modernize Operations in {top_region}",
                    "body": f"Implement automated ticketing and inventory tracking across {top_region} to absorb volume without head-count spikes.",
                    "accent": "#6366F1"
                },
                {
                    "tag": "2. OPEX Containment",
                    "title": "Preserve Budget Variance Limits",
                    "body": f"Maintain strict procurement controls to defend our {margin_str} budget efficiency rating across external vendors.",
                    "accent": "#34D399"
                },
                {
                    "tag": "3. Capacity Balancing",
                    "title": f"Smooth {worst_month} Slack Period",
                    "body": f"Shift non-urgent maintenance, employee training, and audits into the {worst_month} lower-throughput window.",
                    "accent": "#F87171"
                },
                {
                    "tag": "4. Unit Cost Reduction",
                    "title": "Compress Cost Per Unit",
                    "body": f"Renegotiate vendor SLA tiers to reduce average processing cost below the current benchmark of {aov_str}.",
                    "accent": "#FBBF24"
                }
            ],
            "speaker_notes": {
                "slide_1": f"Good morning. Today we are walking through our operations and expense performance review for {report_title}. We will examine budget allocations, departmental throughput, seasonal peaks, and operational efficiency initiatives.",
                "slide_2": f"On slide 2, total managed budget reached {rev_str} across {total_orders:,} completed tasks, with an average unit cost of {aov_str}. Our budget efficiency index registered at {margin_str}.",
                "slide_3": f"Examining seasonal throughput on slide 3: {best_month} saw our heaviest operational volume. In contrast, {worst_month} showed lower volume, offering the ideal window for cross-training and system upgrades.",
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


def generate_narrative(report_data: dict, report_title: str = "Executive Report", report_mode: str = None, api_key: str = None) -> dict:
    """
    Calls the Gemini API (gemini-2.5-flash) using structured output.
    Returns a dictionary with executive_summary, takeaways, recommendations, and speaker_notes.
    Falls back gracefully if the API key is not present or an error occurs.
    """
    mode = report_mode or report_data.get("report_mode", "Sales & Retail Performance")
    resolved_key = api_key or get_gemini_api_key()
    if not resolved_key:
        print(f"ℹ️  No Gemini API key found. Using deterministic template narrative ({mode}).")
        return get_deterministic_fallback(report_data, report_title, report_mode=mode)

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
            "statistical_anomalies": ins.get("anomalies", []),
            "anomaly_headline": ins.get("anomaly_headline", ""),
        }

        # Add report mode to payload
        payload["report_mode"] = mode

        role_personas = {
            "Marketing": "an elite Chief Marketing Officer (CMO) and Growth Strategist focusing on ROAS, CAC, ad spend efficiency, conversion funnels, and paid/organic scale.",
            "Operations": "an elite Chief Operating Officer (COO) and Systems Strategist focusing on OPEX, cost containment, vendor efficiency, departmental budget variance, and throughput bottlenecks.",
            "Sales": "an elite Chief Commercial Officer (CCO) and Boardroom Strategist focusing on revenue velocity, margin expansion, product dominance, and regional market share."
        }
        active_persona = role_personas["Marketing"] if "Marketing" in mode else (role_personas["Operations"] if "Operations" in mode else role_personas["Sales"])

        prompt = f"""
You are {active_persona}
Analyze the following verified performance data for this '{mode}' workflow and provide strategic boardroom commentary:

VERIFIED DATA (Do NOT invent or alter any numbers):
{json.dumps(payload, indent=2)}

Requirements:
1. executive_summary: A 2-3 sentence strategic executive briefing tailored to the '{mode}' context, highlighting financial health, peak performance, and strategic outlook. If statistical anomalies are present in 'statistical_anomalies', explicitly reference the primary outlier surge or contraction.
2. takeaways: An array of exactly 3 insight items tailored to this workflow. Each item must have:
   - "icon": an appropriate emoji (e.g., "🎯", "⚡", "📈")
   - "title": a 3-5 word executive label
   - "body": 1-2 concise, high-impact analytical sentences
3. recommendations: An array of exactly 4 prioritized, actionable strategic recommendations for leadership. Each item must have:
   - "tag": formatted as "1. Category", "2. Category", etc.
   - "title": concise action-oriented title
   - "body": specific commercial instruction (1-2 sentences)
   - "accent": hex color (choose from #6366F1, #34D399, #F87171, #FBBF24)
4. speaker_notes: An object containing slide-by-slide presenter scripts for 5 slides:
   - "slide_1": Warm boardroom welcome, framing the agenda for {report_title}.
   - "slide_2": Commentary on bottom-line numbers, volume, and unit efficiency.
   - "slide_3": Momentum, peak month seasonality, and trough mitigation.
   - "slide_4": Category dominance, departmental/channel breakdown, and item performance.
   - "slide_5": Executive call to action detailing the next operational or strategic steps.

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
        result["report_mode"] = mode
        return result

    except Exception as e:
        print(f"⚠️  Gemini API call failed ({e}). Falling back to deterministic narrative.")
        fallback = get_deterministic_fallback(report_data, report_title, report_mode=mode)
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
