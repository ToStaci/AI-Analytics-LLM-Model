import streamlit as st
from dotenv import load_dotenv
from src.agent import TelemetrySQLAgent
from src.analytics import CommunityAnalyticsEngine

load_dotenv()

st.set_page_config(page_title="Studio AI Telemetry & Feedback", page_icon="📊", layout="wide")

@st.cache_resource
def get_sql_agent():
    return TelemetrySQLAgent()

@st.cache_resource
def get_analytics_engine():
    return CommunityAnalyticsEngine()

st.title("AI Analytics Hub")
tab1, tab2 = st.tabs(["🔍 Telemetry Text-to-SQL", "📝 Player Feedback Analytics"])
 
with tab1:
    st.header("Query Game Telemetry in Natural Language")
    st.caption("Ask questions about matches, weapon usage, maps, or player stats.")

    agent = get_sql_agent()
    
    user_query = st.text_input(
        "Enter query:", 
        placeholder="Which weapon dealt the most damage overall?",
        max_chars=300
    )

    if user_query:
        with st.spinner("Generating SQL and querying database..."):
            try:

                res = agent.text_to_sql(user_query)
                
                if res.get("error"):
                    st.warning(
                        f"⚠️ Failed to execute query against database.\n\n"
                        f"**Details:** {res['error']}\n\n"
                        f"Please rephrase your question."
                    )
                else:
                    st.subheader("Generated SQL Query")
                    st.code(res.get("sql", "-- No SQL generated"), language="sql")

                    st.subheader("Result Data")
                    st.dataframe(res.get("data", []), use_container_width=True)

            except Exception as e:
                st.error(
                    "⚠️ An unexpected error occurred while processing the query. "
                    "Please rephrase your question or check your database connection."
                )


with tab2:
    st.header("Batch Review & Bug Report Parser")
    st.caption("Analyze unstructured feedback to extract categories, sentiment, and severity.")

    default_reviews = (
        "M4A1 is way too overpowered after the last patch, it shreds everyone in 2 shots!\n"
        "FPS drops to 15 when entering the main city on Chernarus map.\n"
        "Desync during multiplayer matches is terrible, hits are not registering."
    )

    reviews_text = st.text_area("Paste Player Reviews (one per line, max 30):", value=default_reviews, height=150)

    if st.button("Analyze Batch", type="primary"):
        raw_list = [r.strip() for r in reviews_text.split("\n") if r.strip()]
        
        if len(raw_list) > 30:
            st.warning("⚠️ Limit exceeded. Automatically processed the first 30 reviews.")
        
        reviews_list = raw_list[:30]

        if not reviews_list:
            st.warning("Please enter at least one review.")
        else:
            with st.spinner("Processing feedback with Pydantic structured output..."):
                try:
                    engine = get_analytics_engine()
                    report = engine.analyze_feedback_batch(reviews_list)

                    st.subheader("Summary")
                    col1, col2 = st.columns(2)
                    col1.metric("Total Analyzed", getattr(report, "total_analyzed", 0))
                    col2.metric("Top Complaint", getattr(report, "top_complaint", "N/A"))

                    st.subheader("Categorized Issues")
                    issues_data = [issue.model_dump() for issue in report.issues]
                    st.dataframe(issues_data, use_container_width=True)

                except Exception as e:
  
                    st.error(
                        "⚠️ Failed to analyze feedback. "
                        "Please check the format of the entered data or API limits."
                    )