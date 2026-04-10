from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Industrial Market Intelligence Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "market_opportunities.csv"

# -----------------------
# LOAD DATA
# -----------------------

df = pd.read_csv(CSV_PATH)

# Clean numeric columns
if "opportunity_score" in df.columns:
    df["opportunity_score"] = pd.to_numeric(df["opportunity_score"], errors="coerce")

if "cluster" in df.columns:
    df["cluster"] = pd.to_numeric(df["cluster"], errors="coerce")

# Fill null text fields if needed
for col in ["priority_label", "market_type", "executive_summary", "recommended_action_llm"]:
    if col in df.columns:
        df[col] = df[col].fillna("")

# -----------------------
# HEADER
# -----------------------
st.title("Industrial Market Intelligence Dashboard")
st.caption("Identify, prioritize, and act on high-value market opportunities.")

# -----------------------
# TOP MARKET OPPORTUNITIES
# -----------------------
st.subheader("Top Market Opportunities")

top_df = df.sort_values("opportunity_score", ascending=False).head(3)

for _, row in top_df.iterrows():
    st.markdown(f"""
    **{row['state_name']} — {row['industry']}**  
    Opportunity Score: **{row['opportunity_score']:.3f}**  
    Priority: {row['priority_label']}  
    Action: {row['recommended_action_llm']}
    """)
    st.markdown("---")

# -----------------------
# FILTERS
# -----------------------
st.subheader("Explore Markets")

industry_filter = st.selectbox(
    "Filter by Industry",
    ["All"] + sorted(df["industry"].dropna().unique().tolist())
)

state_filter = st.selectbox(
    "Filter by State",
    ["All"] + sorted(df["state_name"].dropna().unique().tolist())
)

filtered_df = df.copy()

if industry_filter != "All":
    filtered_df = filtered_df[filtered_df["industry"] == industry_filter]

if state_filter != "All":
    filtered_df = filtered_df[filtered_df["state_name"] == state_filter]

filtered_df = filtered_df.sort_values("opportunity_score", ascending=False)

st.dataframe(filtered_df, use_container_width=True)

# -----------------------
# MARKET POSITIONING
# -----------------------
st.subheader("Market Positioning")

if filtered_df.empty:
    st.warning("No rows match the current filters.")
else:
    
    bar_fig = px.bar(
        filtered_df.head(10),
        x="opportunity_score",
        y="state_name",
        color="priority_label",
        hover_data=["industry", "market_type"],
        orientation="h",
        title="Top Markets by Opportunity Score"
    )
    bar_fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(bar_fig, use_container_width=True)

# -----------------------
# EXECUTIVE DETAIL VIEW
# -----------------------
st.subheader("Executive Detail View")

selected_market = st.selectbox(
    "Select a market to inspect",
    filtered_df.apply(lambda r: f"{r['state_name']} — {r['industry']}", axis=1).tolist()
    if not filtered_df.empty else []
)

if selected_market and not filtered_df.empty:
    detail_row = filtered_df[
        filtered_df.apply(lambda r: f"{r['state_name']} — {r['industry']}", axis=1) == selected_market
    ].iloc[0]

    st.markdown(f"### {detail_row['state_name']} — {detail_row['industry']}")
    st.write(f"**Opportunity Score:** {detail_row['opportunity_score']:.3f}")
    st.write(f"**Priority Label:** {detail_row['priority_label']}")
    st.write(f"**Market Type:** {detail_row['market_type']}")

    if str(detail_row["executive_summary"]).strip():
        st.write("**Executive Summary:**")
        st.write(detail_row["executive_summary"])

    if str(detail_row["recommended_action_llm"]).strip():
        st.write("**Recommended Action:**")
        st.write(detail_row["recommended_action_llm"])

# -----------------------
# QUESTION BOX
# -----------------------
st.subheader("Ask a Question About the Data")

question = st.text_area(
    "Type a business question",
    placeholder="Example: What are the best expansion markets and why?"
)

def answer_question(question_text, data):
    if data.empty:
        return "There are no records available under the current filters."

    q = question_text.lower()

    if "top" in q or "best" in q or "strongest" in q:
        top_rows = data.head(3)
        lines = []
        for _, row in top_rows.iterrows():
            lines.append(
                f"- {row['state_name']} — {row['industry']} "
                f"(score {row['opportunity_score']:.3f}, "
                f"{row['priority_label'].lower()}, "
                f"{row['market_type'].lower()})"
            )
        return "The strongest markets in the current filtered view are:\n\n" + "\n".join(lines)

    if "compare" in q:
        if len(data) < 2:
            return "There are not enough filtered records to compare."
        r1 = data.iloc[0]
        r2 = data.iloc[1]
        return (
            f"{r1['state_name']} — {r1['industry']} ranks above "
            f"{r2['state_name']} — {r2['industry']} with opportunity scores of "
            f"{r1['opportunity_score']:.3f} and {r2['opportunity_score']:.3f}, respectively."
        )

    if "priority" in q or "action" in q or "recommend" in q:
        top_rows = data.head(3)
        lines = []
        for _, row in top_rows.iterrows():
            lines.append(
                f"**{row['state_name']} — {row['industry']}**: {row['recommended_action_llm']}"
            )
        return "\n\n".join(lines)

    top_row = data.iloc[0]
    return (
        f"Based on the current filtered data, the leading market is "
        f"{top_row['state_name']} — {top_row['industry']} with an opportunity score of "
        f"{top_row['opportunity_score']:.3f}. It is labeled "
        f"'{top_row['priority_label']}' and classified as '{top_row['market_type']}'."
    )

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        st.markdown("### Answer")
        st.write(answer_question(question, filtered_df))

# -----------------------
# METHODOLOGY
# -----------------------
with st.expander("How this works"):
    st.markdown("""
    - Opportunity Score combines market size, growth, and concentration into a ranked signal.
    - Clustering groups similar market profiles into broad strategic categories.
    - Executive summaries and recommended actions were generated from structured market records.
    """)
