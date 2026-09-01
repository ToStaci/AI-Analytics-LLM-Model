import streamlit as st
from dotenv import load_dotenv
from src.agent import TelemetrySQLAgent
from src.analytics import CommunityAnalyticsEngine

load_dotenv()

st.set_page_config(page_title="Studio AI Telemetry & Feedback", page_icon="📊", layout="wide")
st.title("AI Analytics Hub")

tab1, tab2 = st.tabs(["🔍 Telemetry Text-to-SQL", "📝 Player Feedback Analytics"])

with tab1:
    st.header("Query Game Telemetry in Natural Language")
    st.caption("Ask questions about matches, weapon usage, maps, or player stats.")

    agent = TelemetrySQLAgent()
    user_query = st.text_input(
        "Enter query:", 
        placeholder="Which weapon dealt the most damage overall?"
    )

    if user_query:
        with st.spinner("Generating SQL and querying database..."):
            res = agent.text_to_sql(user_query)
            
            if res["error"]:
                st.error(f"SQL Error: {res['error']}")
            else:
                st.subheader("Generated SQL Query")
                st.code(res["sql"], language="sql")

                st.subheader("Result Data")
                st.dataframe(res["data"], use_container_width=True)

with tab2:
    st.header("Batch Review & Bug Report Parser")
    st.caption("Analyze unstructured feedback to extract categories, sentiment, and severity.")

    default_reviews = (
        "M4A1 is way too overpowered after the last patch, it shreds everyone in 2 shots!\n"
        "FPS drops to 15 when entering the main city on Chernarus map.\n"
        "Desync during multiplayer matches is terrible, hits are not registering."
    )

    reviews_text = st.text_area("Paste Player Reviews (one per line):", value=default_reviews, height=150)

    if st.button("Analyze Batch", type="primary"):
        reviews_list = [r.strip() for r in reviews_text.split("\n") if r.strip()]
        
        with st.spinner("Processing feedback with Pydantic structured output..."):
            engine = CommunityAnalyticsEngine()
            report = engine.analyze_feedback_batch(reviews_list)

            st.subheader("Summary")
            col1, col2 = st.columns(2)
            col1.metric("Total Analyzed", report.total_analyzed)
            col2.metric("Top Complaint", report.top_complaint)

            st.subheader("Categorized Issues")
            issues_data = [issue.model_dump() for issue in report.issues]
            st.dataframe(issues_data, use_container_width=True)