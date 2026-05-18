"""
ai_insights.py
--------------
Placement: app/services/ai_insights.py

Generates executive-level supply chain insights using the OpenAI API.
Builds a structured prompt from forecast + inventory + risk data and
returns a parsed InsightsResponse.

The response is split into five sections so the frontend can render
each independently:
  - urgent_actions      : immediate replenishment needs
  - fastest_growing     : top growth products analysis
  - optimization_recs   : inventory optimisation recommendations
  - risk_summary        : consolidated risk narrative
  - executive_summary   : 3–4 sentence C-suite summary

Fallback behaviour: if the OpenAI call fails, a degraded response is
returned instead of raising an exception, so the main endpoint still
returns useful forecast and inventory data.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
import openai

logger = logging.getLogger(__name__)
load_dotenv()

# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

@dataclass
class InsightsResponse:
    urgent_actions: list[str] = field(default_factory=list)
    fastest_growing: list[str] = field(default_factory=list)
    optimization_recs: list[str] = field(default_factory=list)
    risk_summary: list[str] = field(default_factory=list)
    executive_summary: str = ""
    raw_response: str = ""
    error: str | None = None


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

def _build_prompt(
    top_products: list[dict],
    inventory_metrics: list[dict],
    risk_alerts: list[dict],
    total_products: int,
    total_skipped: int,
) -> str:
    # Summarise top 10 products for the prompt (keep token count manageable)
    top10 = top_products[:10]
    inv_index = {m["product_id"]: m for m in inventory_metrics[:20]}

    product_lines: list[str] = []
    for p in top10:
        inv = inv_index.get(p["product_id"], {})
        line = (
            f"- {p['product_name']} (ID: {p['product_id']}): "
            f"avg daily demand {p['avg_daily_demand']:.1f} units, "
            f"7-day projection {p['total_projected_7d']:.0f} units, "
            f"growth {p['demand_growth_pct']:+.1f}%, "
            f"safety stock {inv.get('safety_stock', 'N/A')}, "
            f"reorder point {inv.get('reorder_point', 'N/A')}"
        )
        if inv.get("days_of_inventory") is not None:
            line += f", days on hand {inv['days_of_inventory']:.0f}"
        product_lines.append(line)

    # Summarise risk alerts
    critical_alerts = [a for a in risk_alerts if a.get("severity") == "critical"]
    high_alerts = [a for a in risk_alerts if a.get("severity") == "high"]
    risk_lines: list[str] = []
    for a in (critical_alerts + high_alerts)[:8]:
        risk_lines.append(
            f"- [{a['severity'].upper()}] {a['product_name']}: "
            f"{a['risk_type']} — {a['message']}"
        )

    prompt = f"""You are an expert supply chain analyst. Analyse the following demand forecast and inventory data and provide actionable business insights.

DATASET SUMMARY
- Total products analysed: {total_products}
- Products skipped (insufficient data): {total_skipped}
- High/critical risk alerts: {len(critical_alerts + high_alerts)}

TOP PRODUCTS BY PROJECTED DEMAND GROWTH
{chr(10).join(product_lines) if product_lines else "No product data available."}

RISK ALERTS (CRITICAL & HIGH)
{chr(10).join(risk_lines) if risk_lines else "No critical or high risk alerts."}

Please respond with a JSON object containing EXACTLY these keys:
{{
  "urgent_actions": ["action 1", "action 2", ...],
  "fastest_growing": ["insight about top growers 1", "insight 2", ...],
  "optimization_recs": ["recommendation 1", "recommendation 2", ...],
  "risk_summary": ["risk narrative 1", "risk narrative 2", ...],
  "executive_summary": "3-4 sentence paragraph for C-suite executives summarising the overall supply chain situation, key opportunities, and risks."
}}

Requirements:
- urgent_actions: 3–5 specific, actionable items for today/this week
- fastest_growing: 3–4 insights about top-growing products
- optimization_recs: 4–6 inventory optimisation recommendations
- risk_summary: 3–5 risk narrative bullets
- executive_summary: exactly one paragraph, 3–4 sentences, suitable for a board report
- Use specific product names and numbers from the data where possible
- Be direct and business-focused; avoid generic statements
- Return ONLY valid JSON, no markdown, no preamble"""

    return prompt


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_ai_insights(
    top_products: list[dict],
    inventory_metrics: list[dict],
    risk_alerts: list[dict],
    total_products: int = 0,
    total_skipped: int = 0,
  model: str = "gpt-4.1-mini",
    max_tokens: int = 1200,
) -> InsightsResponse:
    """
    Call OpenAI to generate supply chain insights.

    Falls back to a degraded response with an error message if the API
    call fails, so the calling endpoint is never blocked.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; returning degraded insights.")
        return InsightsResponse(
            error="OpenAI API key not configured.",
            executive_summary=(
                f"Analysis processed {total_products} products. "
                f"{len([a for a in risk_alerts if a.get('severity') in ('critical','high')])} "
                "high-priority risk alerts detected. Configure OPENAI_API_KEY for detailed AI insights."
            ),
        )

    prompt = _build_prompt(
        top_products=top_products,
        inventory_metrics=inventory_metrics,
        risk_alerts=risk_alerts,
        total_products=total_products,
        total_skipped=total_skipped,
    )

    import time

# Retry up to 3 times for transient server errors
    try:
        client = openai.OpenAI(api_key=api_key)

        # Retry up to 3 times for temporary OpenAI server errors
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are a world-class supply chain analytics expert. "
                                "Always respond with valid JSON only."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3,
                )
                break
            except openai.OpenAIError as exc:
                if "internal_error" in str(exc).lower() and attempt < 2:
                    print(f"OpenAI internal error, retrying ({attempt + 1}/3)...")
                    time.sleep(2)
                    continue
                raise

        raw = response.choices[0].message.content or ""
        logger.debug("OpenAI raw response: %s", raw[:200])

        # Remove markdown fences if the model returns ```json ... ```
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        parsed = json.loads(cleaned)

        print("\n" + "=" * 80)
        print("✅ OPENAI API CALL SUCCESSFUL")
        print("Executive Summary:")
        print(parsed.get("executive_summary", "")[:300])
        print("=" * 80 + "\n")        

        return InsightsResponse(
            urgent_actions=parsed.get("urgent_actions", []),
            fastest_growing=parsed.get("fastest_growing", []),
            optimization_recs=parsed.get("optimization_recs", []),
            risk_summary=parsed.get("risk_summary", []),
            executive_summary=parsed.get("executive_summary", ""),
            raw_response=raw,
        )

    except json.JSONDecodeError as exc:
        logger.error("Failed to parse OpenAI JSON response: %s", exc)
        return InsightsResponse(
            error=f"JSON parse error: {exc}",
            raw_response=raw if "raw" in locals() else "",
            executive_summary="AI insights could not be parsed. Raw response attached.",
        )

    except openai.OpenAIError as exc:
        print(str(exc))
        print("=" * 80 + "\n")

        logger.error("OpenAI API error: %s", exc)

        # Return meaningful fallback insights instead of exposing technical errors
        return InsightsResponse(
            urgent_actions=[
                "Review products with rising forecasted demand and confirm replenishment plans.",
                "Validate supplier capacity for high-growth SKUs.",
                "Monitor inventory positions daily during the forecast horizon.",
            ],
            fastest_growing=[
                "Several products show positive demand momentum and may require increased procurement.",
                "High-growth items should be prioritized to prevent stockouts.",
            ],
            optimization_recs=[
                "Use calculated safety stock to protect against demand variability.",
                "Adjust reorder points to maintain target service levels.",
                "Review reorder quantities to balance carrying costs and availability.",
            ],
            risk_summary=[
                    "Current demand trends suggest moderate operational risk.",
                "Proactive replenishment can reduce stockout exposure.",
            ],
            executive_summary=(
                f"Analysis processed {total_products} products and identified "
                f"{len([a for a in risk_alerts if a.get('severity') in ('critical', 'high')])} "
                "high-priority risk alerts. Inventory optimization recommendations "
                "have been generated to improve service levels and reduce stockout risk."
            ),
            error=str(exc),
        )

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Unexpected error generating AI insights: %s",
            exc,
            exc_info=True,
        )
        return InsightsResponse(
            error=str(exc),
            executive_summary="AI insights unavailable due to an unexpected error.",
        )