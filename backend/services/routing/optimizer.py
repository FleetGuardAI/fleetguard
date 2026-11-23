"""
FleetGuard — Route Scoring & Optimization Model
Classifies and scores multiple route alternatives using normalized multi-criteria analysis.
"""

from typing import List, Dict, Any
from services.routing.schemas import RouteOption, CostEstimate


class RouteOptimizer:
    """
    Evaluates, ranks, and categorizes routing alternatives into:
    - RECOMMENDED: Optimal balance of travel expense, time, and distance
    - FASTEST: Minimum driving duration
    - LOWEST_COST: Minimum direct fuel and toll expenditure
    - ALTERNATIVE: Additional valid paths
    """

    @staticmethod
    def optimize_routes(raw_routes: List[Dict[str, Any]]) -> List[RouteOption]:
        if not raw_routes:
            return []

        if len(raw_routes) == 1:
            r = raw_routes[0]
            cost: CostEstimate = r["cost_estimate"]
            return [
                RouteOption(
                    id="route-0",
                    category="RECOMMENDED",
                    category_label="Recommended (Direct Route)",
                    distance_km=r["distance_km"],
                    duration_hours=r["duration_hours"],
                    duration_seconds=r["duration_seconds"],
                    polyline=r["polyline"],
                    cost_estimate=cost,
                    summary=r.get("summary", "Primary Route"),
                    toll_estimate=r.get("toll_estimate"),
                    tolls_available=r.get("tolls_available", True),
                    provider=r.get("provider", "routing_engine"),
                    traffic_aware=r.get("traffic_aware", False),
                    vehicle_restrictions_supported=r.get("vehicle_restrictions_supported", False),
                    suitability_warning=r.get("suitability_warning"),
                    score=1.0,
                    selection_reason="Single direct route established by navigation provider."
                )
            ]

        # Multiple routes: perform normalized multi-criteria evaluation
        min_dur = min(r["duration_seconds"] for r in raw_routes)
        max_dur = max(r["duration_seconds"] for r in raw_routes)

        min_cost = min(r["cost_estimate"].direct_travel_cost for r in raw_routes)
        max_cost = max(r["cost_estimate"].direct_travel_cost for r in raw_routes)

        min_dist = min(r["distance_km"] for r in raw_routes)
        max_dist = max(r["distance_km"] for r in raw_routes)

        dur_span = max_dur - min_dur if max_dur > min_dur else 1.0
        cost_span = max_cost - min_cost if max_cost > min_cost else 1.0
        dist_span = max_dist - min_dist if max_dist > min_dist else 1.0

        fastest_idx = min(range(len(raw_routes)), key=lambda i: raw_routes[i]["duration_seconds"])
        cheapest_idx = min(range(len(raw_routes)), key=lambda i: raw_routes[i]["cost_estimate"].direct_travel_cost)

        scored_routes = []
        for i, r in enumerate(raw_routes):
            dur = r["duration_seconds"]
            cost_val = r["cost_estimate"].direct_travel_cost
            dist = r["distance_km"]

            # Normalized values in [0.0, 1.0] where 0 is best
            norm_dur = (dur - min_dur) / dur_span
            norm_cost = (cost_val - min_cost) / cost_span
            norm_dist = (dist - min_dist) / dist_span

            # Weights: 45% cost, 40% time, 15% distance
            score = 0.45 * norm_cost + 0.40 * norm_dur + 0.15 * norm_dist
            scored_routes.append((score, i, r))

        # Best overall score
        scored_routes.sort(key=lambda x: x[0])
        best_idx = scored_routes[0][1]

        result_options = []
        assigned_categories = set()

        for score, idx, r in scored_routes:
            cost: CostEstimate = r["cost_estimate"]

            # Determine category
            if idx == best_idx and "RECOMMENDED" not in assigned_categories:
                cat = "RECOMMENDED"
                cat_label = "Recommended"
                assigned_categories.add("RECOMMENDED")

                # Compose transparent explanation
                if idx == fastest_idx and idx == cheapest_idx:
                    reason = "Optimal choice: simultaneously the fastest and lowest direct-cost route."
                elif idx == cheapest_idx:
                    savings = (raw_routes[fastest_idx]["cost_estimate"].direct_travel_cost or 0) - (cost.direct_travel_cost or 0)
                    time_diff = (r["duration_seconds"] - raw_routes[fastest_idx]["duration_seconds"]) // 60
                    reason = f"Economically optimal: saves ₹{savings:.2f} with {time_diff}m variance versus fastest route."
                else:
                    reason = "Balanced route providing optimal trade-off between transit time, fuel consumption, and toll fees."

            elif idx == fastest_idx and "FASTEST" not in assigned_categories:
                cat = "FASTEST"
                cat_label = "Fastest Route"
                assigned_categories.add("FASTEST")
                time_saved = (raw_routes[cheapest_idx]["duration_seconds"] - r["duration_seconds"]) // 60
                reason = f"Minimizes driving duration by {time_saved}m compared to cheapest alternative."

            elif idx == cheapest_idx and "LOWEST_COST" not in assigned_categories:
                cat = "LOWEST_COST"
                cat_label = "Lowest Direct Cost"
                assigned_categories.add("LOWEST_COST")
                savings = (raw_routes[fastest_idx]["cost_estimate"].direct_travel_cost or 0) - (cost.direct_travel_cost or 0)
                reason = f"Minimizes direct travel expenses by ₹{savings:.2f}."

            else:
                cat = "ALTERNATIVE"
                cat_label = f"Alternative {len(result_options) + 1}"
                reason = "Viable alternative route."

            result_options.append(
                RouteOption(
                    id=f"route-{idx}",
                    category=cat,
                    category_label=cat_label,
                    distance_km=r["distance_km"],
                    duration_hours=r["duration_hours"],
                    duration_seconds=r["duration_seconds"],
                    polyline=r["polyline"],
                    cost_estimate=cost,
                    summary=r.get("summary", f"Option {idx + 1}"),
                    toll_estimate=r.get("toll_estimate"),
                    tolls_available=r.get("tolls_available", True),
                    provider=r.get("provider", "routing_engine"),
                    traffic_aware=r.get("traffic_aware", False),
                    vehicle_restrictions_supported=r.get("vehicle_restrictions_supported", False),
                    suitability_warning=r.get("suitability_warning"),
                    score=round(score, 4),
                    selection_reason=reason
                )
            )

        # Ensure RECOMMENDED route is first in the list
        result_options.sort(key=lambda opt: 0 if opt.category == "RECOMMENDED" else (1 if opt.category == "FASTEST" else 2))
        return result_options
