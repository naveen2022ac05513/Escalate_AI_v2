import streamlit as st
import pandas as pd
import random
import re

# Set page configuration with modern layout
st.set_page_config(page_title="EscalateAI - Escalation Tracking", layout="wide")

# ---------------------------------
# Sentiment Analysis for Issue Detection
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    
    # Improved negative sentiment detection using regex
    negative_words = [
        r"\b(problematic|delay|issue|failure|dissatisfaction|frustration|unacceptable|mistake|complaint|unresolved|unresponsive|unstable|broken|defective|overdue|escalation|leakage|damage|burnt|critical|risk|dispute|faulty)\b"
    ]
    
    sentiment = "Negative" if any(re.search(word, text_lower) for word in negative_words) else "Positive"
    
    urgency = "High" if any(word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]) else "Low"
    
    escalation = sentiment == "Negative" and urgency == "High"
    
    return sentiment, urgency, escalation

# ---------------------------------
# Generate Unique Escalation ID
# ---------------------------------
def generate_escalation_id():
    return f"ESC-{random.randint(10000, 99999)}"

# ---------------------------------
# Log Escalation
# ---------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    escalation_id = generate_escalation_id()
    
    st.session_state.cases.append({
        "Escalation ID": escalation_id,
        "Customer": row.get("customer", "N/A"),
        "Issue": row.get("brief issue", "N/A"),
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
        "Date Reported": row.get("issue reported date", "N/A"),
        "Owner": row.get("owner", "N/A"),
        "Status": row.get("status", "Open"),
    })

# ---------------------------------
# Show Kanban Board with Improved Graphics
# ---------------------------------
def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.subheader("🗂️ Escalation Kanban Board")
    cols = st.columns(3)
    stages = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    for case in st.session_state.cases:
        with stages[case["Status"]]:
            st.markdown("----")
            st.markdown(f"**🧾 Issue: {case['Issue']}**")
            st.write(f"🔹 Sentiment: `{case['Sentiment']}` | Urgency: `{case['Urgency']}`")
            st.write(f"📅 Reported: {case['Date Reported']} | 👤 Owner: {case.get('Owner', 'N/A')}")
            st.write(f"✅ Escalated: {case['Escalated']}")

            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{case['Escalation ID']}_status"
            )
            
            case["Status"] = new_status  # Persist changes

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("🚨 EscalateAI - Escalation Tracking System")

# Layout: Left for File Upload & Analysis, Right for Kanban Board
left_column, right_column = st.columns([1, 3])

with left_column:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    # Allow user to trigger analysis AFTER upload
    if file is not None:
        df = pd.read_excel(file)

        # Normalize column names for compatibility
        df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

        required_cols = {"customer", "brief issue", "issue reported date", "status", "owner"}
        missing_cols = required_cols - set(df.columns)

        if missing_cols:
            st.error(f"Excel file is missing required columns: {', '.join(missing_cols)}")
        else:
            if st.button("🔍 Analyze Issues & Log Escalations"):
                for _, row in df.iterrows():
                    sentiment, urgency, escalated = analyze_issue(row["brief issue"])
                    log_case(row, sentiment, urgency, escalated)
                st.success("Escalations auto-logged from Excel file!")

with right_column:
    show_kanban()

# Option to download escalations
if "cases" in st.session_state and st.session_state.cases:
    df_cases = pd.DataFrame(st.session_state.cases)
    st.download_button(
        label="Download Escalations as Excel",
        data=df_cases.to_excel(index=False, engine="openpyxl"),
        file_name="escalations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
