"""
utils/cfa_topics.py — CFA Level I official curriculum topic map (2026/2027).

Sources: CFA Institute 2026 & 2027 Level I Topic Outlines (Learning Outcome Statements).
Topic names and subtopics match the official CFA Institute published materials exactly.
"""

from typing import Dict, List

# CFA Level I — official topic area weights (2025/2026/2027 curriculum)
# The CFA Institute publishes weight RANGES; we use the midpoint of each range.
# Official ranges: Ethics 15-20%, FSA/Fixed Income/Equity Investments 11-14%,
# Portfolio Management 8-12%, Alternatives 7-10%,
# Quant/Economics/Corporate Issuers 6-9%, Derivatives 5-8%
CFA_TOPICS: Dict[str, Dict] = {

    # ── 1. Ethical and Professional Standards ─────────────────────────────────
    "Ethical and Professional Standards": {
        "weight": 17,
        "color": "#6366f1",
        "subtopics": [
            "Ethics and Trust in the Investment Profession",
            "Code of Ethics and Standards of Professional Conduct",
            "Guidance for Standard I: Professionalism",
            "Guidance for Standard II: Integrity of Capital Markets",
            "Guidance for Standard III: Duties to Clients",
            "Guidance for Standard IV: Duties to Employers",
            "Guidance for Standard V: Investment Analysis, Recommendations, and Actions",
            "Guidance for Standard VI: Conflicts of Interest",
            "Guidance for Standard VII: Responsibilities as a CFA Institute Member or CFA Candidate",
            "Application of the Code and Standards: Level I",
        ],
    },

    # ── 2. Quantitative Methods ───────────────────────────────────────────────
    "Quantitative Methods": {
        "weight": 8,
        "color": "#8b5cf6",
        "subtopics": [
            "Returns of Financial Assets and Instruments",
            "The Time Value of Money in Finance",
            "Statistical Characteristics of Asset Returns",
            "Statistical Distributions for Financial Asset Prices and Returns",
            "Estimation and Hypothesis Testing",
            "The Return and Risk of a Financial Portfolio",
            "Simulation of Financial Asset Prices and Returns",
            "Applications of Simple Linear Regression in Finance",
            "Introduction to Financial Data Science",
        ],
    },

    # ── 3. Economics ──────────────────────────────────────────────────────────
    "Economics": {
        "weight": 8,
        "color": "#0ea5e9",
        "subtopics": [
            "The Firm and Market Structures",
            "Understanding Business Cycles",
            "Fiscal Policy",
            "Monetary Policy",
            "Introduction to Geopolitics",
            "International Trade",
            "Capital Flows and the FX Market",
            "Exchange Rate Calculations",
        ],
    },

    # ── 4. Financial Statement Analysis ──────────────────────────────────────
    "Financial Statement Analysis": {
        "weight": 12,
        "color": "#06b6d4",
        "subtopics": [
            "Introduction to Financial Statement Analysis",
            "Analyzing Income Statements",
            "Analyzing Balance Sheets",
            "Analyzing Statements of Cash Flows I",
            "Analyzing Statements of Cash Flows II",
            "Analysis of Inventories",
            "Analysis of Long-Term Assets",
            "Topics in Long-Term Liabilities and Equity",
            "Analysis of Income Taxes",
            "Financial Reporting Quality",
            "Financial Analysis Techniques",
            "Introduction to Financial Statement Modeling",
        ],
    },

    # ── 5. Corporate Issuers ──────────────────────────────────────────────────
    "Corporate Issuers": {
        "weight": 8,
        "color": "#10b981",
        "subtopics": [
            "Corporate Governance: Conflicts, Mechanisms, Risks, and Benefits",
            "Working Capital and Liquidity",
            "Capital Investments and Capital Allocation",
            "Capital Structure",
            "Business Models",
        ],
    },

    # ── 6. Equity Investments ───────────────────────────────────────────────────
    "Equity Investments": {
        "weight": 12,
        "color": "#f59e0b",
        "subtopics": [
            "Equity Instrument Features",
            "Equity Jurisdictions, Classes, and the Voting Process",
            "Equity Issuance and Trading",
            "Sources of Equity Returns",
            "Discounted Cash Flow (DCF) and Growth Models",
            "Relative Value Equity Valuation Approaches",
            "Financial Statement Forecasting in Equity Valuation",
            "Industry and Competitive Analysis",
            "Company Analysis: Past, Present, and Future",
            "Equity Analyst Research Reports",
            "The Capital Asset Pricing Model, Market Model, and Other Factor-Based Equity Models",
        ],
    },

    # ── 7. Fixed Income ───────────────────────────────────────────────────────
    "Fixed Income": {
        "weight": 12,
        "color": "#ef4444",
        "subtopics": [
            "Fixed-Income Instrument Features",
            "Fixed-Income Cash Flows and Types",
            "Fixed-Income Issuance and Trading",
            "Fixed-Income Markets for Corporate Issuers",
            "Fixed-Income Markets for Government Issuers",
            "Fixed-Income Bond Valuation: Prices and Yields",
            "Yield and Yield Spread Measures for Fixed-Rate Bonds",
            "Yield and Yield Spread Measures for Floating-Rate Instruments",
            "The Term Structure of Interest Rates: Spot, Par, and Forward Curves",
            "Interest Rate Risk and Return",
            "Yield-Based Bond Duration Measures and Properties",
            "Yield-Based Bond Convexity and Portfolio Properties",
            "Curve-Based and Empirical Fixed-Income Risk Measures",
            "Credit Risk",
            "Credit Analysis for Government Issuers",
            "Credit Analysis for Corporate Issuers",
            "Fixed-Income Securitization",
            "Asset-Backed Security (ABS) Instrument and Market Features",
            "Mortgage-Backed Security (MBS) Instrument and Market Features",
        ],
    },

    # ── 8. Derivatives ────────────────────────────────────────────────────────
    "Derivatives": {
        "weight": 5,
        "color": "#ec4899",
        "subtopics": [
            "Derivative Instrument and Derivative Market Features",
            "Forward Commitment and Contingent Claim Features and Instruments",
            "Derivative Benefits, Risks, and Issuer and Investor Uses",
            "Arbitrage, Replication, and the Cost of Carry in Pricing Derivatives",
            "Pricing and Valuation of Forward Contracts and for an Underlying with Varying Maturities",
            "Pricing and Valuation of Futures Contracts",
            "Pricing and Valuation of Interest Rate and Other Swaps",
            "Pricing and Valuation of Options",
            "Option Replication Using Put–Call Parity",
            "Valuing a Derivative Using a One-Period Binomial Model",
        ],
    },

    # ── 9. Alternative Investments ────────────────────────────────────────────
    "Alternative Investments": {
        "weight": 8,
        "color": "#f97316",
        "subtopics": [
            "Alternative Investment Features, Methods, and Structures",
            "Alternative Investment Performance and Returns",
            "Investments in Private Capital: Equity and Debt",
            "Real Estate and Infrastructure",
            "Natural Resources",
            "Hedge Funds",
            "Introduction to Digital Assets",
        ],
    },

    # ── 10. Portfolio Management ──────────────────────────────────────────────────────────
    "Portfolio Management": {
        "weight": 10,
        "color": "#14b8a6",
        "subtopics": [
            "Portfolio Risk and Return: Part I",
            "Portfolio Risk and Return: Part II",
            "Portfolio Management: An Overview",
            "Basics of Portfolio Planning and Construction",
            "The Behavioral Biases of Individuals",
            "Introduction to Risk Management",
        ],
    },
}

# ── Convenience exports ────────────────────────────────────────────────────────
TOPIC_NAMES: List[str] = list(CFA_TOPICS.keys())
TOPIC_COLORS: Dict[str, str] = {t: v["color"] for t, v in CFA_TOPICS.items()}
TOPIC_WEIGHTS: Dict[str, int] = {t: v["weight"] for t, v in CFA_TOPICS.items()}

# Legacy name map — for migrating existing DB records to the new official names
TOPIC_NAME_MIGRATIONS: Dict[str, str] = {
    "Ethics & Professional Standards": "Ethical and Professional Standards",
    "Ethics and Professional Standards": "Ethical and Professional Standards",
    "Ethical and Professional": "Ethical and Professional Standards",
    "Financial Statement": "Financial Statement Analysis",
    "Equities": "Equity Investments",
    "Corporate Finance": "Corporate Issuers",
    "Portfolio Construction": "Portfolio Management",
}


def get_subtopics(topic: str) -> List[str]:
    """Return subtopics for the given topic name."""
    return CFA_TOPICS.get(topic, {}).get("subtopics", [])


def get_all_subtopics() -> List[str]:
    """Return a flat list of all subtopics across all topics."""
    result = []
    for v in CFA_TOPICS.values():
        result.extend(v["subtopics"])
    return result


def normalize_topic_name(name: str) -> str:
    """Map legacy/unofficial topic names to the current official name."""
    return TOPIC_NAME_MIGRATIONS.get(name, name)


DIFFICULTY_LEVELS = ["Easy", "Medium", "Hard"]
SESSION_TYPES = ["Practice", "Mock Exam", "Review"]

# CFA exam windows — 4 per year (approx. 3rd week of each month)
CFA_EXAM_WINDOWS = {
    "February": {"month": 2, "day": 18, "label": "Feb (Winter)"},
    "May":      {"month": 5, "day": 20, "label": "May (Spring)"},
    "August":   {"month": 8, "day": 19, "label": "Aug (Summer)"},
    "November": {"month": 11, "day": 18, "label": "Nov (Fall)"},
}
