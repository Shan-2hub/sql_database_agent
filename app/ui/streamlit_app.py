
import streamlit as st
import pandas as pd
import plotly.express as px

from app.agent.runner import run_agent


# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(
    page_title="SQL Analytics Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# Custom Styling
# --------------------------------------------------

st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    div[data-testid="stMetric"] {
        background: #1c2333;
        border: 1px solid #303b50;
        padding: 18px;
        border-radius: 12px;
    }

    .app-subtitle {
        color: #9ca3af;
        font-size: 16px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# Session State
# --------------------------------------------------

if "agent_result" not in st.session_state:
    st.session_state.agent_result = None

if "query_history" not in st.session_state:
    st.session_state.query_history = []


# --------------------------------------------------
# Sidebar
# --------------------------------------------------

with st.sidebar:
    st.title("📊 SQL Analytics Agent")

    st.caption("AI-powered database analytics")

    st.divider()

    st.subheader("About")

    st.write(
        "Ask questions about your database using "
        "natural language. The AI agent generates, "
        "validates, and executes read-only SQL queries."
    )

    st.divider()

    st.subheader("Example Queries")

    examples = [
        "Show all orders sorted by date.",
        "What is the total revenue?",
        "Show the top 5 customers by order amount.",
        "How many orders are completed?",
        "Show total sales by product.",
    ]

    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state.selected_query = example

    st.divider()

    st.caption("Powered by LangGraph, NeMo and SQLGlot")


# --------------------------------------------------
# Main Header
# --------------------------------------------------

st.title("SQL & Database Analytics Agent")

st.markdown(
    '<p class="app-subtitle">'
    'Interact with your database using natural language.'
    '</p>',
    unsafe_allow_html=True,
)

st.divider()


# --------------------------------------------------
# Query Input
# --------------------------------------------------

st.subheader("Ask your database")

default_query = st.session_state.get("selected_query", "")

with st.form("query_form"):
    user_query = st.text_area(
        "Enter your question",
        value=default_query,
        placeholder="Example: Show total revenue by product",
        height=100,
    )

    submitted = st.form_submit_button(
        "🚀 Execute Query",
        use_container_width=True,
    )


# --------------------------------------------------
# Execute Agent
# --------------------------------------------------

if submitted:

    if not user_query.strip():
        st.warning("Please enter a question.")

    else:
        with st.spinner("Analyzing your request..."):

            try:
                result = run_agent(user_query)

                st.session_state.agent_result = result

                st.session_state.query_history.append({
                    "query": user_query,
                    "status": result.get("status"),
                    "rows": result.get("row_count", 0),
                })

            except Exception as error:
                st.error(f"Application error: {error}")


# --------------------------------------------------
# Display Results
# --------------------------------------------------

result = st.session_state.agent_result

if result:

    status = result.get("status")

    st.divider()

    if status == "blocked":

        st.error("🛡️ Security Alert: Request Blocked")

        st.write(
            "NeMo Guardrails identified this request "
            "as potentially unsafe. SQL generation was prevented."
        )

        st.info(result.get("error", "Unsafe input detected."))

    elif status == "error":

        st.error("Query execution failed.")

        st.write(result.get("error"))

    elif status == "success":

        st.success("Query executed successfully.")

        # KPI Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Rows Returned",
                result.get("row_count", 0),
            )

        with col2:
            st.metric(
                "Retry Attempts",
                result.get("retry_count", 0),
            )

        with col3:
            st.metric(
                "Execution Status",
                "Success",
            )

        # SQL Query
        with st.expander("Generated SQL", expanded=True):

            st.code(
                result.get("generated_sql") or "",
                language="sql",
            )

        # Results Table
        st.subheader("Query Results")

        rows = result.get("results", [])
        columns = result.get("columns", [])

        if rows:

            dataframe = pd.DataFrame(
                rows,
                columns=columns,
            )

            st.dataframe(
                dataframe,
                use_container_width=True,
                hide_index=True,
            )

            # Plotly Visualization
            st.subheader("Data Visualization")

            numeric_columns = dataframe.select_dtypes(
                include="number"
            ).columns.tolist()

            if numeric_columns:

                all_columns = dataframe.columns.tolist()

                chart_col1, chart_col2 = st.columns(2)

                with chart_col1:
                    x_column = st.selectbox(
                        "X-axis",
                        all_columns,
                        index=0,
                    )

                with chart_col2:
                    y_column = st.selectbox(
                        "Y-axis",
                        numeric_columns,
                        index=0,
                    )

                if x_column != y_column:

                    chart_data = dataframe.copy()

                    fig = px.bar(
                        chart_data,
                        x=x_column,
                        y=y_column,
                        title=f"{y_column} by {x_column}",
                    )

                    fig.update_layout(
                        template="plotly_dark",
                        height=450,
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True,
                    )

            else:
                st.info(
                    "No numeric columns are available "
                    "for visualization."
                )

        else:
            st.info("The query returned no records.")

    # Execution Logs
    with st.expander("Agent Execution Logs"):

        for log in result.get("logs", []):
            st.write(f"• {log}")


# --------------------------------------------------
# Query History
# --------------------------------------------------

if st.session_state.query_history:

    st.divider()

    st.subheader("Recent Query History")

    history_df = pd.DataFrame(
        st.session_state.query_history
    )

    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True,
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------

st.divider()

st.caption(
    "SQL & Database Analytics Agent | "
    "LangGraph • NeMo Guardrails • SQLGlot • Streamlit • Plotly"
)
