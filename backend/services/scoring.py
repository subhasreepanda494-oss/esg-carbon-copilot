from typing import Dict, Any, Optional

# Industry benchmarks (prototypical values for scoring)
BENCHMARKS = {
    "Unknown": {
        "Social": {
            "employee_turnover_pct": {"benchmark": 15.0, "lower_is_better": True, "weight": 0.3},
            "training_hours_per_employee": {"benchmark": 40.0, "lower_is_better": False, "weight": 0.3},
            "workplace_incidents": {"benchmark": 5.0, "lower_is_better": True, "weight": 0.2},
            "employee_satisfaction_pct": {"benchmark": 75.0, "lower_is_better": False, "weight": 0.1},
            "diversity_female_pct": {"benchmark": 40.0, "lower_is_better": False, "weight": 0.1},
        },
        "Governance": {
            "board_independent_pct": {"benchmark": 50.0, "lower_is_better": False, "weight": 0.4},
            "ethics_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.3},
            "data_privacy_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.2},
            "whistleblower_cases": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.1},
        },
        "Environmental": {
            "total_emissions": {"benchmark": 10000.0, "lower_is_better": True, "weight": 1.0}
        }
    },
    "Manufacturing": {
        "Social": {
            "employee_turnover_pct": {"benchmark": 12.0, "lower_is_better": True, "weight": 0.3},
            "training_hours_per_employee": {"benchmark": 50.0, "lower_is_better": False, "weight": 0.3},
            "workplace_incidents": {"benchmark": 10.0, "lower_is_better": True, "weight": 0.2},
            "employee_satisfaction_pct": {"benchmark": 70.0, "lower_is_better": False, "weight": 0.1},
            "diversity_female_pct": {"benchmark": 30.0, "lower_is_better": False, "weight": 0.1},
        },
        "Governance": {
            "board_independent_pct": {"benchmark": 60.0, "lower_is_better": False, "weight": 0.4},
            "ethics_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.3},
            "data_privacy_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.2},
            "whistleblower_cases": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.1},
        },
        "Environmental": {
            "total_emissions": {"benchmark": 50000.0, "lower_is_better": True, "weight": 1.0}
        }
    },
    "IT/Software": {
        "Social": {
            "employee_turnover_pct": {"benchmark": 18.0, "lower_is_better": True, "weight": 0.3},
            "training_hours_per_employee": {"benchmark": 60.0, "lower_is_better": False, "weight": 0.3},
            "workplace_incidents": {"benchmark": 1.0, "lower_is_better": True, "weight": 0.2},
            "employee_satisfaction_pct": {"benchmark": 85.0, "lower_is_better": False, "weight": 0.1},
            "diversity_female_pct": {"benchmark": 45.0, "lower_is_better": False, "weight": 0.1},
        },
        "Governance": {
            "board_independent_pct": {"benchmark": 70.0, "lower_is_better": False, "weight": 0.4},
            "ethics_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.3},
            "data_privacy_incidents": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.2},
            "whistleblower_cases": {"benchmark": 0.0, "lower_is_better": True, "weight": 0.1},
        },
        "Environmental": {
            "total_emissions": {"benchmark": 2000.0, "lower_is_better": True, "weight": 1.0}
        }
    }
}

def calculate_metric_score(value: float, benchmark: float, lower_is_better: bool) -> float:
    if benchmark == 0:
        if lower_is_better:
            return 100.0 if value == 0 else max(0.0, 100.0 - (value * 20.0))
        else:
            return 100.0 if value > 0 else 0.0

    if lower_is_better:
        # If value is lower than benchmark, score > 100, we cap at 100
        # If value is exactly benchmark, score is 50
        # If value is double the benchmark, score is 0
        ratio = value / benchmark
        score = 100.0 - (ratio * 50.0) + 50.0 if ratio <= 1 else 50.0 - ((ratio - 1) * 50.0)
    else:
        # If value is higher than benchmark, score > 100, we cap at 100
        # If value is exactly benchmark, score is 50
        ratio = value / benchmark
        score = (ratio * 50.0)
        
    return max(0.0, min(100.0, score))

def calculate_pillar_performance(metrics: Dict[str, Any], pillar: str, industry: str = "Unknown") -> tuple[Optional[float], list]:
    benchmarks = BENCHMARKS.get(industry, BENCHMARKS["Unknown"]).get(pillar, {})
    
    if not benchmarks or not metrics:
        return None, []
        
    total_score = 0.0
    total_weight = 0.0
    details = []
    
    for metric_name, rules in benchmarks.items():
        val = metrics.get(metric_name)
        if val is not None:
            try:
                numeric_val = float(val)
                score = calculate_metric_score(numeric_val, rules["benchmark"], rules["lower_is_better"])
                weighted_score = score * rules["weight"]
                
                total_score += weighted_score
                total_weight += rules["weight"]
                
                details.append({
                    "metric": metric_name,
                    "value": numeric_val,
                    "benchmark": rules["benchmark"],
                    "lower_is_better": rules["lower_is_better"],
                    "normalized_score": score,
                    "weight": rules["weight"],
                    "weighted_score": weighted_score
                })
            except (ValueError, TypeError):
                continue
                
    if total_weight > 0:
        final_score = total_score / total_weight
        return final_score, details
    
    return None, []
