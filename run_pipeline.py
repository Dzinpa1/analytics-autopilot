"""
run_pipeline.py
Master runner — executes the full end-to-end pipeline:
  1. Generate synthetic dataset  (or load your own CSV)
  2. Analyse & compute all KPIs
  3. Generate charts
  4. Build PowerPoint deck
"""

import os, time, sys

BASE_DIR   = os.path.dirname(__file__)
CSV_PATH   = os.path.join(BASE_DIR, "sales_data.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

def banner(msg):
    print(f"\n{'='*55}")
    print(f"  {msg}")
    print(f"{'='*55}")


if __name__ == "__main__":
    start = time.time()

    # ── Step 1: Ingest or generate data ─────────────────────────
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        CSV_PATH = sys.argv[1]
        banner(f"STEP 1 of 4 — Using provided dataset: {CSV_PATH}")
    else:
        banner("STEP 1 of 4 — Generating demo dataset")
        from generate_data import generate_sales_data
        df = generate_sales_data()
        df.to_csv(CSV_PATH, index=False)
        print(f"  Dataset: {df.shape[0]} rows × {df.shape[1]} columns → {CSV_PATH}")

    # ── Step 2: Auto-detect columns & compute KPIs ──────────────
    banner("STEP 2 of 4 — Analysing data & computing KPIs")
    from analysis_engine import build_report
    report = build_report(CSV_PATH)
    kpis   = report["kpis"]
    print(f"  Revenue  : ${kpis['total_revenue']:,.2f}")
    if kpis.get("total_profit") is not None:
        print(f"  Profit   : ${kpis['total_profit']:,.2f}  ({kpis.get('efficiency_display', 'N/A')} {kpis.get('efficiency_metric_name', '')})")
    else:
        print("  Profit   : not available (no profit/cost column found)")
    print(f"  Orders   : {kpis['total_orders']:,}")
    print(f"  Best month: {report['insights']['best_month']}")

    # ── Step 3: Charts ─────────────────────────────────────────
    banner("STEP 3 of 4 — Generating charts")
    from chart_engine import generate_all_charts
    chart_paths = generate_all_charts(report)

    # ── Step 4: Slide deck ─────────────────────────────────────
    banner("STEP 4 of 4 — Building PowerPoint deck")
    from slide_builder import build_presentation
    pptx_path = build_presentation(report, chart_paths)

    # ── Done ───────────────────────────────────────────────────
    elapsed = round(time.time() - start, 1)
    banner(f"✅  PIPELINE COMPLETE  ({elapsed}s)")
    print(f"\n  📂  Output folder : {OUTPUT_DIR}")
    print(f"  📊  Charts        : 4 PNG files")
    print(f"  📑  Deck          : Analytics_Report.pptx")
    print(f"\n  Open the .pptx file to see your auto-generated report!\n")
