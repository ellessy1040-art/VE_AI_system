"""
data/demo_case.py

SYNTHETIC DEMONSTRATION DATA -- NOT OFFICIAL PROJECT DATA
============================================================
All numerical values in this module are synthetic, illustrative
engineering-style assumptions created ONLY to demonstrate the
VE-AI decision-support workflow end-to-end. They do NOT represent
real Egyptian Monorail project data, verified costs, certified
structural capacities, or official engineering approvals.

Every value here is tagged with a DataStatus (see models/schemas.py)
of SYNTHETIC_DEMO so the UI can label it appropriately wherever it
is displayed.
"""

from models.schemas import DataStatus

# ------------------------------------------------------------------
# 1. PROJECT OVERVIEW
# ------------------------------------------------------------------
DEFAULT_PROJECT = {
    "project_name": "Egyptian Monorail \u2014 Demonstration Case",
    "project_type": "Urban Monorail",
    "location": "Egypt",
    "project_phase": "Detailed Design",
    "analysis_scope": "Guideway Beam System",
    "currency": "EGP",
    "base_year": 2026,
    "design_life_years": 50,
    "analysis_period_years": 50,
    "discount_rate": 0.08,
    "data_status": DataStatus.SYNTHETIC_DEMO,
}

# ------------------------------------------------------------------
# 2. COMPONENT & FUNCTION DEFINITION
# ------------------------------------------------------------------
DEFAULT_COMPONENT = {
    "component_name": "Guideway Beam",
    "system": "Guideway System",
    "quantity": 1200,
    "beam_length_m": 24.0,
    "beam_width_m": 1.80,
    "beam_height_m": 1.60,
    "baseline_material": "Prestressed Concrete",
    "beam_weight_tonnes": 68.0,
    "primary_function": "Carry and guide train loads",
    "secondary_functions": [
        "Transfer loads to supporting structure",
        "Maintain required guideway alignment",
        "Provide required service life",
    ],
    "required_design_life_years": 50,
    "max_allowable_deflection_mm": 20.0,
    "required_load_capacity_pct": 100.0,
    "safety_critical": True,
    "data_status": DataStatus.SYNTHETIC_DEMO,
}

# ------------------------------------------------------------------
# 3. BASELINE FINANCIAL ASSUMPTIONS
#    Baseline -- Prestressed Concrete Guideway Beam
# ------------------------------------------------------------------
DEFAULT_BASELINE = {
    "name": "Baseline \u2014 Prestressed Concrete Guideway Beam",
    "material": "Prestressed Concrete",
    "initial_cost": 1_200_000_000.0,
    "annual_operating_cost": 5_000_000.0,
    "annual_maintenance_cost": 12_000_000.0,
    "replacement_year": 30,
    "replacement_cost": 300_000_000.0,
    "residual_value": 50_000_000.0,
    "discount_rate": 0.08,
    "analysis_period_years": 50,
    "data_status": DataStatus.SYNTHETIC_DEMO,
}

# ------------------------------------------------------------------
# 4. PREDEFINED DEMO ALTERNATIVES (used by Mock AI / Demo Mode)
#    Financial + technical + sustainability assumptions
# ------------------------------------------------------------------
DEFAULT_ALTERNATIVES = [
    {
        "alt_id": "ALT_A",
        "name": "Steel Box Girder",
        "principle": (
            "Replace the prestressed concrete guideway beam with a "
            "fabricated structural steel box girder designed to provide "
            "the same primary load-carrying and guideway function."
        ),
        "function_equivalence": (
            "Provides equivalent primary load-carrying and guideway "
            "alignment function through a fabricated steel box section "
            "instead of a prestressed concrete section."
        ),
        "material": "Structural Steel",
        "technical_changes": [
            "Fabricated welded steel box cross-section",
            "Bolted or welded field splices at beam joints",
            "Applied corrosion-protection coating system",
        ],
        "benefits": [
            "Lower self-weight than concrete section",
            "Faster fabrication in controlled shop conditions",
            "Potentially faster erection sequence",
        ],
        "constraints": [
            "Requires certified structural steel fabricator",
            "Requires long-term corrosion protection maintenance",
            "Requires fire protection review where applicable",
        ],
        "required_data": [
            "Verified structural capacity calculation",
            "Deflection and fatigue verification",
            "Corrosion protection specification",
            "Verified market pricing from fabricators",
        ],
        "risks": [
            {"risk": "Corrosion", "probability": 3, "impact": 4,
             "mitigation": "Apply certified multi-coat corrosion protection system and periodic inspection regime",
             "residual_probability": 2, "residual_impact": 3, "owner": "Structural Engineer"},
            {"risk": "Steel Supply Chain", "probability": 2, "impact": 4,
             "mitigation": "Secure early supplier agreements and qualify multiple fabricators",
             "residual_probability": 1, "residual_impact": 3, "owner": "Procurement Lead"},
            {"risk": "Erection Complexity", "probability": 2, "impact": 3,
             "mitigation": "Develop detailed erection sequence and method statement, use experienced steel erectors",
             "residual_probability": 1, "residual_impact": 2, "owner": "Construction Manager"},
        ],
        "sustainability": {
            "embodied_carbon_index": 85,
            "construction_waste_index": 70,
            "operational_energy_index": 98,
        },
        "technical_performance_score": 97,
        "ai_confidence": "medium",
        "cost": {
            "initial_cost": 1_050_000_000.0,
            "annual_operating_cost": 5_000_000.0,
            "annual_maintenance_cost": 18_000_000.0,
            "replacement_year": 30,
            "replacement_cost": 250_000_000.0,
            "residual_value": 80_000_000.0,
        },
    },
    {
        "alt_id": "ALT_B",
        "name": "Steel-Concrete Composite Girder",
        "principle": (
            "Replace the prestressed concrete guideway beam with a "
            "composite section combining a structural steel girder and "
            "a reinforced concrete deck acting compositely to carry and "
            "guide train loads."
        ),
        "function_equivalence": (
            "Provides equivalent primary load-carrying and guideway "
            "alignment function through composite steel-concrete action."
        ),
        "material": "Steel-Concrete Composite",
        "technical_changes": [
            "Structural steel girder with shear-connected concrete deck",
            "Composite action via shear studs at the steel-concrete interface",
            "Applied corrosion protection to exposed steel surfaces",
        ],
        "benefits": [
            "Combines steel stiffness with concrete durability",
            "Reduced steel corrosion exposure versus a full steel section",
            "Good balance of weight and stiffness",
        ],
        "constraints": [
            "Requires quality control at the steel-concrete interface",
            "Requires composite design verification",
            "Requires qualified composite-construction contractor",
        ],
        "required_data": [
            "Verified structural capacity and composite action calculation",
            "Deflection and fatigue verification",
            "Interface (shear connector) design verification",
            "Verified market pricing",
        ],
        "risks": [
            {"risk": "Steel-Concrete Interface Durability", "probability": 2, "impact": 3,
             "mitigation": "Specify certified shear connectors and quality inspection at interface",
             "residual_probability": 1, "residual_impact": 2, "owner": "Structural Engineer"},
            {"risk": "Localized Corrosion at Exposed Steel", "probability": 2, "impact": 3,
             "mitigation": "Apply protective coating and schedule periodic inspection",
             "residual_probability": 1, "residual_impact": 2, "owner": "Maintenance Engineer"},
            {"risk": "Fabrication & Construction Complexity", "probability": 2, "impact": 2,
             "mitigation": "Engage experienced composite-construction contractor, detailed method statement",
             "residual_probability": 1, "residual_impact": 2, "owner": "Construction Manager"},
        ],
        "sustainability": {
            "embodied_carbon_index": 82,
            "construction_waste_index": 72,
            "operational_energy_index": 97,
        },
        "technical_performance_score": 98,
        "ai_confidence": "medium",
        "cost": {
            "initial_cost": 1_100_000_000.0,
            "annual_operating_cost": 5_000_000.0,
            "annual_maintenance_cost": 15_000_000.0,
            "replacement_year": 30,
            "replacement_cost": 270_000_000.0,
            "residual_value": 65_000_000.0,
        },
    },
    {
        "alt_id": "ALT_C",
        "name": "Optimized Prestressed Concrete Beam",
        "principle": (
            "Retain the prestressed concrete solution but optimize the "
            "cross-section, prestressing layout, and mix design to "
            "reduce material use and long-term maintenance while "
            "preserving the same primary function."
        ),
        "function_equivalence": (
            "Provides the same primary load-carrying and guideway "
            "alignment function as the baseline, using an optimized "
            "prestressed concrete section."
        ),
        "material": "Prestressed Concrete (Optimized)",
        "technical_changes": [
            "Refined cross-section geometry to reduce material volume",
            "Optimized prestressing tendon layout",
            "Improved concrete mix design for durability",
        ],
        "benefits": [
            "Retains a familiar, well-proven construction method",
            "Lower change in construction methodology and risk versus baseline",
            "Reduced material quantity versus baseline",
        ],
        "constraints": [
            "Requires updated structural design verification",
            "Requires updated formwork and casting-yard setup",
            "Marginal cost benefit relative to the baseline",
        ],
        "required_data": [
            "Verified optimized structural capacity calculation",
            "Deflection and long-term creep/shrinkage verification",
            "Verified updated cost estimate from contractor",
        ],
        "risks": [
            {"risk": "Formwork & Casting Complexity", "probability": 2, "impact": 2,
             "mitigation": "Use proven precast yard processes and quality control procedures",
             "residual_probability": 1, "residual_impact": 2, "owner": "Construction Manager"},
            {"risk": "Prestressing Losses / Long-term Creep", "probability": 2, "impact": 3,
             "mitigation": "Apply conservative long-term loss allowances and monitoring during service",
             "residual_probability": 1, "residual_impact": 2, "owner": "Structural Engineer"},
            {"risk": "Construction Tolerance Deviations", "probability": 1, "impact": 2,
             "mitigation": "Apply standard precast QA/QC and survey control",
             "residual_probability": 1, "residual_impact": 1, "owner": "Site Engineer"},
        ],
        "sustainability": {
            "embodied_carbon_index": 90,
            "construction_waste_index": 85,
            "operational_energy_index": 99,
        },
        "technical_performance_score": 99,
        "ai_confidence": "high",
        "cost": {
            "initial_cost": 1_130_000_000.0,
            "annual_operating_cost": 5_000_000.0,
            "annual_maintenance_cost": 11_000_000.0,
            "replacement_year": 30,
            "replacement_cost": 290_000_000.0,
            "residual_value": 50_000_000.0,
        },
    },
]

# ------------------------------------------------------------------
# 5. BASELINE SUSTAINABILITY INDICATORS (reference = 100)
# ------------------------------------------------------------------
BASELINE_SUSTAINABILITY = {
    "embodied_carbon_index": 100,
    "construction_waste_index": 100,
    "operational_energy_index": 100,
}

# ------------------------------------------------------------------
# 6. BASELINE RISK REGISTER (existing Prestressed Concrete)
# ------------------------------------------------------------------
BASELINE_RISKS = [
    {"risk": "Standard Construction Variability", "probability": 2, "impact": 2,
     "mitigation": "Follow proven standard construction procedures and QA/QC",
     "residual_probability": 1, "residual_impact": 2, "owner": "Construction Manager"},
    {"risk": "Long-term Creep / Shrinkage", "probability": 2, "impact": 2,
     "mitigation": "Apply standard design allowances and periodic monitoring",
     "residual_probability": 1, "residual_impact": 2, "owner": "Structural Engineer"},
    {"risk": "Routine Maintenance Requirements", "probability": 1, "impact": 2,
     "mitigation": "Follow standard maintenance and inspection schedule",
     "residual_probability": 1, "residual_impact": 1, "owner": "Maintenance Engineer"},
]

# ------------------------------------------------------------------
# 7. MCE DEFAULT CRITERIA WEIGHTS
# ------------------------------------------------------------------
DEFAULT_WEIGHTS = {
    "lcc": 40,
    "performance": 25,
    "risk": 20,
    "sustainability": 15,
}

# ------------------------------------------------------------------
# 8. SENSITIVITY ANALYSIS SCENARIOS
# ------------------------------------------------------------------
SENSITIVITY_SCENARIOS = {
    "Scenario 1 \u2014 Default Weights": {
        "lcc": 40, "performance": 25, "risk": 20, "sustainability": 15,
    },
    "Scenario 2 \u2014 Performance-Focused": {
        "lcc": 25, "performance": 40, "risk": 20, "sustainability": 15,
    },
    "Scenario 3 \u2014 Cost-Focused": {
        "lcc": 55, "performance": 20, "risk": 15, "sustainability": 10,
    },
}

# ------------------------------------------------------------------
# 9. FORBIDDEN ASSUMPTIONS / CONSTRAINTS PASSED TO THE AI
# ------------------------------------------------------------------
VE_CONSTRAINTS = [
    "Maintain required structural performance",
    "Maintain guideway alignment",
    "Suitable for infrastructure construction",
    "No compromise to safety",
    "Engineer approval required",
]

FORBIDDEN_ASSUMPTIONS = [
    "Do not invent structural capacity",
    "Do not claim code compliance without evidence",
    "Do not invent supplier prices",
    "Do not claim safety certification",
]

EVALUATION_CRITERIA = ["Life Cycle Cost", "Technical Performance", "Risk", "Sustainability"]

MISSING_DATA = [
    "Verified structural capacity calculations for all alternatives",
    "Certified market pricing from fabricators/suppliers",
    "Fatigue and corrosion protection verification",
    "Formal code-compliance review",
]

SAFETY_NOTICE = (
    "IMPORTANT: This prototype provides AI-assisted decision support for "
    "Value Engineering. It does not replace structural analysis, "
    "engineering codes, specialist review, safety assessment, or "
    "professional engineering judgment."
)

AI_ROLE_NOTICE = (
    "AI provides decision support and alternative suggestions. "
    "Final engineering approval remains with the responsible engineer."
)

DEMO_DATA_NOTICE = "Synthetic Demonstration Data \u2014 Not Official Project Data"
