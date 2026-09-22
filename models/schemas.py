"""
models/schemas.py

Pydantic data models used throughout VE-AI.
These define the structured contracts between the UI, the
deterministic engines, and the AI layer.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator


# ======================================================================
# DATA TRACEABILITY STATUS
# ======================================================================
class DataStatus(str, Enum):
    VERIFIED = "VERIFIED"
    USER_INPUT = "USER_INPUT"
    SYNTHETIC_DEMO = "SYNTHETIC_DEMO"
    AI_PROPOSED = "AI_PROPOSED"
    CALCULATED = "CALCULATED"
    MISSING = "MISSING"


class ReviewStatus(str, Enum):
    AI_PROPOSED = "AI_PROPOSED"
    ACCEPTED_FOR_ANALYSIS = "ACCEPTED_FOR_ANALYSIS"
    MORE_INFO_REQUESTED = "MORE_INFO_REQUESTED"
    REJECTED = "REJECTED"


class EngineerDecision(str, Enum):
    PENDING = "PENDING"
    APPROVE = "APPROVE"
    REQUEST_MORE_INFO = "REQUEST_MORE_INFO"
    REJECT = "REJECT"


# ======================================================================
# PROJECT / COMPONENT / BASELINE
# ======================================================================
class ProjectInfo(BaseModel):
    project_name: str
    project_type: str
    location: str
    project_phase: str
    analysis_scope: str
    currency: str = "EGP"
    base_year: int
    design_life_years: int
    analysis_period_years: int
    discount_rate: float
    data_status: DataStatus = DataStatus.SYNTHETIC_DEMO


class ComponentData(BaseModel):
    component_name: str
    system: str
    quantity: int
    beam_length_m: float
    beam_width_m: float
    beam_height_m: float
    baseline_material: str
    beam_weight_tonnes: float
    primary_function: str
    secondary_functions: List[str] = Field(default_factory=list)
    required_design_life_years: int
    max_allowable_deflection_mm: float
    required_load_capacity_pct: float
    safety_critical: bool
    data_status: DataStatus = DataStatus.SYNTHETIC_DEMO


class FinancialAssumptions(BaseModel):
    """Shared financial inputs used by the baseline and every alternative."""
    initial_cost: float
    annual_operating_cost: float
    annual_maintenance_cost: float
    replacement_year: Optional[int] = None
    replacement_cost: float = 0.0
    residual_value: float = 0.0
    discount_rate: float
    analysis_period_years: int

    @field_validator("discount_rate")
    @classmethod
    def _check_rate(cls, v: float) -> float:
        if not (0 <= v < 1):
            raise ValueError("discount_rate must be a fraction between 0 and 1 (e.g. 0.08 for 8%)")
        return v


class Baseline(BaseModel):
    name: str
    material: str
    financials: FinancialAssumptions
    data_status: DataStatus = DataStatus.SYNTHETIC_DEMO


# ======================================================================
# RISK
# ======================================================================
class RiskItem(BaseModel):
    risk: str
    probability: int = Field(ge=1, le=5)
    impact: int = Field(ge=1, le=5)
    mitigation: str = ""
    residual_probability: int = Field(ge=1, le=5, default=1)
    residual_impact: int = Field(ge=1, le=5, default=1)
    owner: str = ""

    @property
    def score(self) -> int:
        return self.probability * self.impact

    @property
    def residual_score(self) -> int:
        return self.residual_probability * self.residual_impact


# ======================================================================
# SUSTAINABILITY
# ======================================================================
class SustainabilityIndicators(BaseModel):
    embodied_carbon_index: float
    construction_waste_index: float
    operational_energy_index: float
    data_status: DataStatus = DataStatus.SYNTHETIC_DEMO

    @property
    def composite_index(self) -> float:
        """Lower is better. 100 = baseline reference level."""
        return (self.embodied_carbon_index + self.construction_waste_index
                + self.operational_energy_index) / 3.0


# ======================================================================
# ALTERNATIVE (AI OUTPUT SCHEMA + engineering data)
# ======================================================================
class CostEstimate(BaseModel):
    value: Optional[float] = None
    currency: str = "EGP"
    confidence: str = "low"


class Alternative(BaseModel):
    alt_id: str
    name: str
    principle: str
    function_equivalence: str
    material: str = ""
    technical_changes: List[str] = Field(default_factory=list)
    benefits: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    required_data: List[str] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    cost_estimate: CostEstimate = Field(default_factory=CostEstimate)
    ai_confidence: str = "low"
    review_status: ReviewStatus = ReviewStatus.AI_PROPOSED

    # Deterministic engineering data (editable by the engineer)
    financials: Optional[FinancialAssumptions] = None
    sustainability: Optional[SustainabilityIndicators] = None
    technical_performance_score: Optional[float] = None

    # Review metadata
    reviewer: Optional[str] = None
    review_timestamp: Optional[str] = None
    review_reason: Optional[str] = None

    data_status: DataStatus = DataStatus.AI_PROPOSED


class AIAlternativesResponse(BaseModel):
    """Top-level schema the LLM must return."""
    alternatives: List[Alternative]


# ======================================================================
# AUDIT LOG
# ======================================================================
class AuditEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    action: str
    entity: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    source: str = "SYSTEM"
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    decision: Optional[str] = None
    user: str = "engineer"


# ======================================================================
# AI CONTEXT (input sent to the LLM)
# ======================================================================
class AIContext(BaseModel):
    project_context: Dict[str, Any]
    component_data: Dict[str, Any]
    function_definition: Dict[str, Any]
    performance_requirements: Dict[str, Any]
    baseline: Dict[str, Any]
    constraints: List[str]
    safety_requirements: Dict[str, Any]
    evaluation_criteria: List[str]
    missing_data: List[str]
    forbidden_assumptions: List[str]
