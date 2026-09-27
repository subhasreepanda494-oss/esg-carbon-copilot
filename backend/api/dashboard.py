from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
from backend.database import get_audit_logs
from backend.services.scoring import calculate_pillar_performance

router = APIRouter()

class Risk(BaseModel):
    category: str
    risk_type: str # "Data Quality" or "ESG Performance"
    severity: str
    metric: str
    reason: str
    suggested_action: str

class Recommendation(BaseModel):
    area: str
    reason: str
    suggested_action: str
    expected_improvement: str

class MetricDetail(BaseModel):
    metric: str
    value: float
    benchmark: float
    lower_is_better: bool
    normalized_score: float
    weight: float
    weighted_score: float

class ESGData(BaseModel):
    # Profile
    company_name: str
    industry: str
    location: str
    reporting_year: str
    employees: int
    revenue: str
    reporting_period: str
    
    # Scorecard
    overall_data_quality: Optional[int]
    overall_performance: Optional[int]
    
    environmental_data_quality: Optional[int]
    environmental_performance: Optional[int]
    
    social_data_quality: Optional[int]
    social_performance: Optional[int]
    
    governance_data_quality: Optional[int]
    governance_performance: Optional[int]
    
    # Social
    employee_turnover_pct: Optional[float]
    training_hours_per_employee: Optional[float]
    workplace_incidents: Optional[int]
    employee_satisfaction_pct: Optional[int]
    diversity_female_pct: Optional[int]
    community_investment: Optional[str]
    
    # Governance
    board_independent_pct: Optional[int]
    ethics_incidents: Optional[int]
    data_privacy_incidents: Optional[int]
    whistleblower_cases: Optional[int]
    governance_policy_status: Optional[str]
    
    # Risks and Recommendations
    risks: List[Risk]
    recommendations: List[Recommendation]
    
    # Performance details for "Why is my score this value?"
    performance_details: Dict[str, List[MetricDetail]]
    
    # For environmental charts (Scope 1, 2, 3)
    scope1_emissions: Optional[float] = 0
    scope2_emissions: Optional[float] = 0
    scope3_emissions: Optional[float] = 0
    total_emissions: Optional[float] = 0

@router.get("/dashboard-data", response_model=ESGData)
async def get_dashboard_data():
    logs = get_audit_logs()
    
    scope1 = 0.0
    scope2 = 0.0
    scope3 = 0.0
    total = 0.0
    env_unverified_count = 0
    env_logs_count = 0
    
    social_metrics = {}
    gov_metrics = {}
    soc_unverified_count = 0
    gov_unverified_count = 0
    soc_logs_count = 0
    gov_logs_count = 0
    
    for log in logs:
        cat = log.get('category', 'Environmental')
        status = log.get('status')
        activity = log.get('activity', '')
        quantity = log.get('quantity', 0)
        
        if cat == 'Environmental':
            env_logs_count += 1
            emissions = log.get('emissions_kg_co2e') or 0.0
            total += emissions
            scope = log.get('scope', '').upper()
            if 'SCOPE 1' in scope:
                scope1 += emissions
            elif 'SCOPE 2' in scope:
                scope2 += emissions
            elif 'SCOPE 3' in scope:
                scope3 += emissions
                
            if status != 'VERIFIED':
                env_unverified_count += 1
                
        elif cat == 'Social':
            soc_logs_count += 1
            social_metrics[activity] = quantity
            if status != 'VERIFIED':
                soc_unverified_count += 1
                
        elif cat == 'Governance':
            gov_logs_count += 1
            gov_metrics[activity] = quantity
            if status != 'VERIFIED':
                gov_unverified_count += 1
            
    # Data Quality Calculation (Valid / Total)
    env_dq = None
    if env_logs_count > 0:
        env_verified_ratio = (env_logs_count - env_unverified_count) / env_logs_count
        env_dq = int(env_verified_ratio * 100)
        
    soc_dq = None
    if soc_logs_count > 0:
        soc_verified_ratio = (soc_logs_count - soc_unverified_count) / soc_logs_count
        soc_dq = int(soc_verified_ratio * 100)
        
    gov_dq = None
    if gov_logs_count > 0:
        gov_verified_ratio = (gov_logs_count - gov_unverified_count) / gov_logs_count
        gov_dq = int(gov_verified_ratio * 100)
        
    dq_scores = [s for s in [env_dq, soc_dq, gov_dq] if s is not None]
    overall_dq = int(sum(dq_scores) / len(dq_scores)) if dq_scores else None
    
    # ESG Performance Calculation (Benchmark vs Actual)
    industry = "Unknown"  # Would come from user profile
    env_perf, env_details = calculate_pillar_performance({"total_emissions": total} if env_logs_count > 0 else {}, "Environmental", industry)
    soc_perf, soc_details = calculate_pillar_performance(social_metrics if soc_logs_count > 0 else {}, "Social", industry)
    gov_perf, gov_details = calculate_pillar_performance(gov_metrics if gov_logs_count > 0 else {}, "Governance", industry)
    
    perf_scores = [s for s in [env_perf, soc_perf, gov_perf] if s is not None]
    overall_perf = int(sum(perf_scores) / len(perf_scores)) if perf_scores else None
    
    risks = []
    recommendations = []
    
    # Data Quality Risks
    if env_unverified_count > 0:
        risks.append(Risk(
            category="Environmental", 
            risk_type="Data Quality",
            severity="High", 
            metric="Unverified Emissions", 
            reason=f"{env_unverified_count} records require review", 
            suggested_action="Review and approve pending emission factors"
        ))
    if soc_unverified_count > 0:
        risks.append(Risk(
            category="Social", 
            risk_type="Data Quality",
            severity="Medium", 
            metric="Invalid Social Data", 
            reason=f"{soc_unverified_count} records invalid", 
            suggested_action="Re-upload corrected social metrics"
        ))
    if gov_unverified_count > 0:
        risks.append(Risk(
            category="Governance", 
            risk_type="Data Quality",
            severity="Medium", 
            metric="Invalid Governance Data", 
            reason=f"{gov_unverified_count} records invalid", 
            suggested_action="Re-upload corrected governance metrics"
        ))
        
    # Performance Risks & Recommendations
    all_details = {"Environmental": env_details, "Social": soc_details, "Governance": gov_details}
    for pillar, details in all_details.items():
        for d in details:
            # If normalized score is < 50, it means we are worse than benchmark
            if d["normalized_score"] < 50:
                risks.append(Risk(
                    category=pillar,
                    risk_type="ESG Performance",
                    severity="High" if d["normalized_score"] < 25 else "Medium",
                    metric=d["metric"],
                    reason=f"Metric {d['value']} is worse than industry benchmark {d['benchmark']}",
                    suggested_action=f"Improve {d['metric']} to meet benchmark"
                ))
                recommendations.append(Recommendation(
                    area=pillar,
                    reason=f"{d['metric']} is underperforming",
                    suggested_action=f"Implement policies to improve {d['metric']}",
                    expected_improvement=f"Align with industry benchmark of {d['benchmark']}"
                ))

    return ESGData(
        company_name="Uploaded Data Company",
        industry=industry,
        location="Global",
        reporting_year="2026",
        employees=0,
        revenue="N/A",
        reporting_period="Jan 1 - Dec 31",
        overall_data_quality=overall_dq,
        overall_performance=overall_perf,
        environmental_data_quality=env_dq,
        environmental_performance=int(env_perf) if env_perf is not None else None,
        social_data_quality=soc_dq,
        social_performance=int(soc_perf) if soc_perf is not None else None,
        governance_data_quality=gov_dq,
        governance_performance=int(gov_perf) if gov_perf is not None else None,
        employee_turnover_pct=social_metrics.get("employee_turnover_pct"),
        training_hours_per_employee=social_metrics.get("training_hours_per_employee"),
        workplace_incidents=social_metrics.get("workplace_incidents"),
        employee_satisfaction_pct=social_metrics.get("employee_satisfaction_pct"),
        diversity_female_pct=social_metrics.get("diversity_female_pct"),
        community_investment=social_metrics.get("community_investment"),
        board_independent_pct=gov_metrics.get("board_independent_pct"),
        ethics_incidents=gov_metrics.get("ethics_incidents"),
        data_privacy_incidents=gov_metrics.get("data_privacy_incidents"),
        whistleblower_cases=gov_metrics.get("whistleblower_cases"),
        governance_policy_status=gov_metrics.get("governance_policy_status"),
        risks=risks,
        recommendations=recommendations,
        performance_details=all_details,
        scope1_emissions=scope1,
        scope2_emissions=scope2,
        scope3_emissions=scope3,
        total_emissions=total
    )

@router.get("/report/summary", response_model=ESGData)
async def get_report_summary():
    return await get_dashboard_data()
