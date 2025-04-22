import streamlit as st
import pandas as pd
import random
from datetime import datetime

# Set Page Configuration
st.set_page_config(page_title="EscalateAI - Escalation Tracking System", layout="wide")

# ---------------------------------
# Negative Sentiment Detection
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()

    # Updated list of negative sentiment words
    negative_words = [
        "problematic", "delay", "issue", "failure", "dissatisfaction", "horrible",
        "frustration", "unacceptable", "terrible", "mistake", "disappointed", "angry",
        "complaint", "unhappy", "regret", "worst", "lost", "trouble", "missed", "irritated",
        "displeased", "rejected", "denied", "not satisfied", "unresolved", "unresponsive",
        "unreliable", "subpar", "unstable", "negative impact", "setback", "annoyed", "frustrating",
        "non-compliance", "broken", "inconvenience", "defective", "overdue", "escalation", "no progress",
        "dissatisfaction", "failure", "leakage", "damage", "burnt", "tripped", "degradation", "breakdown",
        "corrosion", "flashover", "faulty", "defective", "shortage", "mismatch", "delay", "critical",
        "escalated", "dispute", "unresolved", "risk"
    ]
    
    sentiment = "Negative" if any(word in text_lower for word in negative_words) else "Positive"
    
    urgency = "High" if any(word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]) else "Low"
    
    escalation = sentiment == "Negative" and urgency == "High"
    
    return sentiment, urgency, escalation

# ---------------------------------
# Generate Unique Escalation ID
# ---------------------------------
def generate_escalation_id():
    return f"SESICE-{random.randint(10000, 99999)}"

# ---------------------------------
# Logging Escalations
# ---------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []

    escalation_id = generate_escalation_id()

    st.session_state.cases.append({
        "Escalation ID": escalation_id,
        "Customer": row.get("customer", "N/A"),
        "Issue": row["brief issue"],
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
        "Date Reported": row.get("reported date", "N/A"),
        "Action Owner": row.get("action owner", "N/A"),
        "Status": "Open",  # Default to Open
    })

# ---------------------------------
# Show Kanban
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
            st.write(f"📅 Reported: {case['Date Reported']} | 👤 Owner: {case.get('Action Owner', 'N/A')}")
            st.write(f"✅ Escalated: {case['Escalated']}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{case['Escalation ID']}_status"
            )
            case["Status"] = new_status

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("🚨 EscalateAI - Escalation Tracking System")

# Layout: Left for form, Right for Kanban
left_column, right_column = st.columns([1, 3])

with left_column:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    # Manual Entry Form
    st.header("✏️ Manual Entry")
    with st.form(key="manual_entry_form"):
        customer_name = st.text_input("Customer Name")
        issue = st.text_area("Issue")
        criticality = st.selectbox("Criticality", ["Low", "Medium", "High"])
        impact = st.selectbox("Impact", ["Low", "Medium", "High"])
        action_owner = st.text_input("Action Owner")
        date_reported = st.date_input("Date Reported")

        submit_button = st.form_submit_button("Log Escalation")

        if submit_button:
            if customer_name and issue:
                sentiment, urgency, escalated = analyze_issue(issue)
                log_case({
                    "customer": customer_name,
                    "brief issue": issue,
                    "criticality": criticality,
                    "impact": impact,
                    "action owner": action_owner,
                    "reported date": date_reported,
                }, sentiment, urgency, escalated)
                st.success("Escalation logged successfully!")
            else:
                st.error("Please fill all fields.")

with right_column:
    show_kanban()

# Option to download escalations
if "cases" in st.session_state and st.session_state.cases:
    st.download_button(
        label="Download Escalations as Excel",
        data=pd.DataFrame(st.session_state.cases).to_excel(index=False, engine="openpyxl"),
        file_name="escalations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
