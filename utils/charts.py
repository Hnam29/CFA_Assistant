"""
utils/charts.py — Reusable Plotly chart components for CFA dashboard.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict

from utils.cfa_topics import TOPIC_NAMES, TOPIC_COLORS


def radar_chart(topic_scores: Dict[str, float], height: int = 360) -> go.Figure:
    """Radar / spider chart for performance across CFA topics."""
    topics = list(topic_scores.keys())
    scores = list(topic_scores.values())

    # Close the polygon
    topics_closed = topics + [topics[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=topics_closed,
        fill="toself",
        fillcolor="rgba(99,102,241,0.15)",
        line=dict(color="#6366f1", width=2),
        marker=dict(size=6, color="#6366f1"),
        name="Your Score",
    ))
    fig.add_trace(go.Scatterpolar(
        r=[60] * len(topics_closed),
        theta=topics_closed,
        fill="toself",
        fillcolor="rgba(6,182,212,0.05)",
        line=dict(color="#06b6d4", width=1, dash="dot"),
        name="Pass Threshold (60%)",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="#1e293b",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155", color="#64748b", tickfont=dict(size=10)),
            angularaxis=dict(gridcolor="#334155", color="#94a3b8"),
        ),
        showlegend=True,
        legend=dict(font=dict(color="#94a3b8"), bgcolor="rgba(0,0,0,0)"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=60, r=60, t=40, b=40),
        height=height,
    )
    return fig


def score_timeline(sessions: List[Dict], height: int = 280) -> go.Figure:
    """Line chart of score over time."""
    if not sessions:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=height)
        return fig

    df = pd.DataFrame(sessions)
    df = df[df["completed"] == 1].copy()
    if df.empty:
        fig = go.Figure()
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", height=height)
        return fig

    df["started_at"] = pd.to_datetime(df["started_at"])
    df = df.sort_values("started_at")

    fig = px.line(
        df, x="started_at", y="score",
        color="topic",
        markers=True,
        labels={"started_at": "Date", "score": "Score (%)", "topic": "Topic"},
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(gridcolor="#334155", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="#334155", zerolinecolor="#334155", range=[0, 100]),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")),
        margin=dict(l=20, r=20, t=20, b=20),
        height=height,
    )
    return fig


def topic_bar_chart(topic_scores: Dict[str, float], height: int = 380) -> go.Figure:
    """Horizontal bar chart colored by score band."""
    topics = list(topic_scores.keys())
    scores = list(topic_scores.values())
    colors = ["#10b981" if s >= 70 else "#f59e0b" if s >= 50 else "#ef4444" for s in scores]

    fig = go.Figure(go.Bar(
        x=scores, y=topics,
        orientation="h",
        marker=dict(color=colors, opacity=0.85),
        text=[f"{s:.0f}%" for s in scores],
        textposition="outside",
        textfont=dict(color="#e2e8f0"),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8"),
        xaxis=dict(range=[0, 110], gridcolor="#334155", zerolinecolor="#334155"),
        yaxis=dict(gridcolor="#334155"),
        margin=dict(l=10, r=40, t=10, b=10),
        height=height,
    )
    return fig


def mini_gauge(score: float, label: str = "Score") -> go.Figure:
    """Small gauge indicator for a single score."""
    color = "#10b981" if score >= 70 else "#f59e0b" if score >= 50 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number=dict(suffix="%", font=dict(color=color, size=28)),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor="#64748b"),
            bar=dict(color=color, thickness=0.25),
            bgcolor="#1e293b",
            borderwidth=0,
            steps=[
                dict(range=[0, 50], color="#1e293b"),
                dict(range=[50, 70], color="#1e293b"),
                dict(range=[70, 100], color="#1e293b"),
            ],
            threshold=dict(
                line=dict(color="#6366f1", width=2),
                thickness=0.75, value=60,
            ),
        ),
        title=dict(text=label, font=dict(color="#94a3b8", size=13)),
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=15, r=15, t=30, b=10),
        height=180,
    )
    return fig

def cfa_score_report_chart(topic_perf_list: List[Dict]) -> go.Figure:
    """Official replica of the CFA candidate performance score report."""
    order = [
        "Ethical and Professional Standards",
        "Quantitative Methods",
        "Economics",
        "Financial Statement Analysis",
        "Corporate Finance",
        "Equities",
        "Fixed Income",
        "Derivatives",
        "Alternative Investments",
        "Portfolio Management"
    ]
    
    labels_map = {
        "Ethical and Professional Standards": "Ethical<br>and<br>Professional<br>Standards<br>(15-20%)",
        "Quantitative Methods": "Quantitative<br>Methods<br>(6-9%)",
        "Economics": "Economics<br>(6-9%)",
        "Financial Statement Analysis": "Financial<br>Statement<br>Analysis<br>(11-14%)",
        "Corporate Finance": "Corporate<br>Finance<br>(6-9%)",
        "Equities": "Equities<br>(11-14%)",
        "Fixed Income": "Fixed<br>Income<br>(11-14%)",
        "Derivatives": "Derivatives<br>(5-8%)",
        "Alternative Investments": "Alternative<br>Investments<br>(7-10%)",
        "Portfolio Management": "Portfolio<br>Management<br>(8-12%)"
    }
    
    admin_averages = {
        "Ethical and Professional Standards": 62,
        "Quantitative Methods": 58,
        "Economics": 60,
        "Financial Statement Analysis": 56,
        "Corporate Finance": 61,
        "Equities": 63,
        "Fixed Income": 59,
        "Derivatives": 57,
        "Alternative Investments": 62,
        "Portfolio Management": 60
    }
    
    perf_map = {p["topic"]: p["avg_score"] for p in topic_perf_list}
    
    x_data = []
    y_user = []
    y_base = []
    y_range_len = []
    y_admin = []
    
    for t in order:
        score = perf_map.get(t, None)
        if score is None:
            score = 50.0
        
        min_r = max(0, score - 10)
        max_r = min(100, score + 10)
        range_len = max_r - min_r
        
        x_data.append(labels_map[t])
        y_user.append(score)
        y_base.append(min_r)
        y_range_len.append(range_len)
        y_admin.append(admin_averages[t])
        
    fig = go.Figure()
    
    # 1. Likely range box (Vibrant sky blue)
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_range_len,
        base=y_base,
        marker_color="rgba(56, 189, 248, 0.7)",
        marker_line=dict(color="rgba(14, 165, 233, 0.9)", width=1.5),
        width=0.4,
        name="Likely Score Range",
        hoverinfo="none"
    ))
    
    # 2. Topic Administration Average
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_admin,
        mode="markers",
        marker=dict(
            symbol="line-ew",
            size=22,
            line=dict(color="#94a3b8", width=2, dash="dot")
        ),
        name="Topic Administration Avg"
    ))
    
    # 3. Your Score
    fig.add_trace(go.Scatter(
        x=x_data,
        y=y_user,
        mode="markers",
        marker=dict(
            symbol="line-ew",
            size=26,
            line=dict(color="#f1f5f9", width=4.5)
        ),
        name="Your Score"
    ))
    
    # Dynamic range calculation to remove blank space
    max_score = max(y_user + y_admin)
    min_score = min([b for b in y_base] + y_admin)
    
    max_y = max(80, int(max_score + 10))
    min_y = min(45, int(min_score - 10))
    
    min_y = max(0, min_y)
    max_y = min(100, max_y)

    # Passing threshold lines
    fig.add_hline(y=70, line_dash="solid", line_color="#475569", line_width=1)
    fig.add_hline(y=50, line_dash="solid", line_color="#475569", line_width=1)
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#94a3b8", size=10),
        yaxis=dict(
            range=[min_y, max_y], 
            gridcolor="#1e293b", 
            zerolinecolor="#1e293b",
            tickvals=[50, 70],
            ticktext=["50%", "70%"],
            title="Score (%)",
            tickfont=dict(size=11, color="#94a3b8")
        ),
        xaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickangle=0,
            tickfont=dict(size=9.5, color="#e2e8f0")
        ),
        margin=dict(l=40, r=40, t=10, b=60),
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10.5, color="#94a3b8")
        )
    )
    return fig
