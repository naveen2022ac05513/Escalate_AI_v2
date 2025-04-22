import streamlit as st
import pandas as pd
import re

# Set page configuration
st.set_page_config(page_title="EscalateAI - Escalation Tracking", layout="wide")

# ---------------------------------
# Sentiment Analysis for Issue Detection
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    
    negative_words = [
        r"\b(problematic|delay|issue|failure|dissatisfaction|frustration|unacceptable|mistake|complaint|unresolved|unresponsive|unstable|broken|defective|overdue|escalation|leakage|damage|burnt|critical|risk|dispute|faulty)\b"
    ]
    
    sentiment = "Negative" if any(re.search(word, text_lower) for word in negative_words) else "Positive"
    urgency = "High" if any(word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]) else "Low"
    escalation = sentiment == "Negative" and urgency == "High"
    
    return sentiment, urgency, escalation

# ---------------------------------
# Generate Sequential Escalation ID
# ---------------------------------
if "escalation_counter" not in st.session_state:
    st.session_state.escalation_counter = 10000  # Starting number

def generate_escalation_id():
    escalation_id = f"ESC-{st.session_state.escalation_counter}"
    st.session_state.escalation_counter += 1
    return escalation_id

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
        "Criticality": row.get("criticalness", "N/A"),
        "Issue": row.get("brief issue", "N/A"),
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
        "Date Reported": row.get("issue reported date", "N/A"),
        "Owner": row.get("owner", "N/A"),
        "Status": row.get("status", "Open"),
    })

# ---------------------------------
# Show Kanban Board with Filters
# ---------------------------------
def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    # Filters
    st.sidebar.markdown("### 🧰 Filters")
    selected_criticality = st.sidebar.multiselect(
        "Filter by Criticality",
        options=["Low", "Medium", "High"],
        default=["Low", "Medium", "High"]
    )
    escalated_filter = st.sidebar.radio(
        "Escalated Only?",
        options=["All", "Yes", "No"],
        index=0
    )

    def apply_filters(case):
        crit_ok = case["Criticality"] in selected_criticality
        esc_ok = (
            escalated_filter == "All"
            or (escalated_filter == "Yes" and case["Escalated"])
            or (escalated_filter == "No" and not case["Escalated"])
        )
        return crit_ok and esc_ok

    filtered_cases = [case for case in st.session_state.cases if apply_filters(case)]

    # Count cases by status
    status_counts = {
        "Open": sum(1 for case in filtered_cases if case["Status"] == "Open"),
        "In Progress": sum(1 for case in filtered_cases if case["Status"] == "In Progress"),
        "Resolved": sum(1 for case in filtered_cases if case["Status"] == "Resolved"),
    }

    st.subheader(f"Escalation Kanban Board (Open: {status_counts['Open']} | In Progress: {status_counts['In Progress']} | Resolved: {status_counts['Resolved']})")
    col_open, col_progress, col_resolved = st.columns(3)
    stages = {"Open": col_open, "In Progress": col_progress, "Resolved": col_resolved}

    for case in filtered_cases:
        status = case.get("Status", "Open")
        with stages[status]:
            st.markdown("----")
            st.markdown(f"**🔷 Escalation ID: {case['Escalation ID']}**")
            st.markdown(f"**🧾 Issue:** {case['Issue']}")
            st.write(f"👤 **Customer**: {case['Customer']}")
            st.write(f"🔥 **Criticality**: `{case['Criticality']}`")
            st.write(f"📅 **Reported**: `{case['Date Reported']}`")
            st.write(f"👤 **Owner**: `{case.get('Owner', 'N/A')}`")
            st.write(f"✅ **Escalated**: `{case['Escalated']}`")

            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(status),
                key=f"{case['Escalation ID']}_status"
            )
            case["Status"] = new_status

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("EscalateAI - Escalation Tracking System")

# Sidebar: Upload or Manual Entry
with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    if file is not None:
        df = pd.read_excel(file)
        df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

        required_cols = {"customer", "brief issue", "issue reported date", "status", "owner", "criticalness"}
        missing_cols = required_cols - set(df.columns)

        if missing_cols:
            st.error(f"Excel file is missing required columns: {', '.join(missing_cols)}")
        else:
            if st.button("🔍 Analyze Issues & Log Escalations"):
                for _, row in df.iterrows():
                    sentiment, urgency, escalated = analyze_issue(str(row["brief issue"]))
                    log_case(row, sentiment, urgency, escalated)
                st.success("Escalations auto-logged from Excel file!")

    st.header("✏️ Manual Entry")
    with st.form(key="manual_entry_form"):
        customer_name = st.text_input("Customer Name")
        issue = st.text_area("Issue")
        criticality = st.selectbox("Criticality", ["Low", "Medium", "High"])
        action_owner = st.text_input("Action Owner")
        date_reported = st.date_input("Date Reported")
        submit_button = st.form_submit_button("Log Escalation")

        if submit_button:
            if customer_name and issue:
                sentiment, urgency, escalated = analyze_issue(issue)
                log_case({
                    "customer": customer_name,
                    "brief issue": issue,
                    "criticalness": criticality,
                    "owner": action_owner,
                    "issue reported date": date_reported,
                    "status": "Open"
                }, sentiment, urgency,
