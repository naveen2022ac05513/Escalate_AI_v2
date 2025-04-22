import streamlit as st
import pandas as pd
import io
import random
from datetime import datetime

# Set Page Configuration
st.set_page_config(page_title="EscalateAI", layout="wide")

# ---------------------------------
# Helper Functions
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()

    # Sentiment analysis based on negative words
    negative_words = [
        "problematic", "delay", "issue", "failure", "dissatisfaction", "horrible",
        "frustration", "unacceptable", "terrible", "mistake", "disappointed", "angry",
        "complaint", "unhappy", "regret", "worst", "lost", "trouble", "missed", "irritated",
        "displeased", "rejected", "denied", "not satisfied", "unresolved", "unresponsive",
        "unreliable", "subpar", "unstable", "negative impact", "setback", "annoyed", "frustrating",
        "non-compliance", "broken", "inconvenience", "defective", "overdue", "escalation", "no progress"
    ]
    
    sentiment = "Negative" if any(word in text_lower for word in negative_words) else "Positive"
    
    urgency = "High" if any(word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]) else "Low"
    
    escalation = sentiment == "Negative" and urgency == "High"
    
    return sentiment, urgency, escalation


def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    escalation_id = f"SESICE-{random.randint(10000, 99999)}"
    
    st.session_state.cases.append({
        "Escalation ID": escalation_id,
        "Customer": row["customer"],
        "Brief Issue": row["brief issue"],
        "Issue Reported Date": row["issue reported date"],
        "Action Taken": row["action taken"],
        "Owner": row["owner"],
        "Status": row["status"],
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
    })


def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.subheader("🗂️ **Escalation Kanban Board**")

    # Create columns for different stages in the Kanban with graphical labels
    cols = st.columns(3)
    stages = {
        "Open": {"column": cols[0], "color": "yellow", "label": "🟡 Open"},
        "In Progress": {"column": cols[1], "color": "orange", "label": "🟠 In Progress"},
        "Resolved": {"column": cols[2], "color": "green", "label": "✅ Resolved"}
    }

    for case in st.session_state.cases:
        with stages[case["Status"]]["column"]:
            st.markdown(f"#### {stages[case['Status']]['label']}")
            st.markdown(f"**🧾 Issue: {case['Brief Issue']}**")
            st.write(f"🔹 Sentiment: `{case['Sentiment']}` | Urgency: `{case['Urgency']}`")
            st.write(f"📅 Reported: {case['Issue Reported Date']} | 👤 Owner: {case.get('Owner', 'N/A')}")
            st.write(f"✅ Action Taken: {case.get('Action Taken', 'N/A')}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{case['Escalation ID']}_status"
            )
            if new_status != case["Status"]:
                case["Status"] = new_status  # Update the status
                st.experimental_rerun()  # Rerun the app to reflect status changes


def download_excel():
    if "cases" in st.session_state and st.session_state.cases:
        df_export = pd.DataFrame(st.session_state.cases)
        towrite = io.BytesIO()
        df_export.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button(
            label="Download Escalation Data",
            data=towrite,
            file_name="escalations.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )


# ---------------------------------
# Main App Logic
# ---------------------------------

# Freeze header with custom CSS
st.markdown("""
    <style>
        .stApp { 
            padding-top: 100px; 
        }
        header {
            position: sticky;
            top: 0;
            background-color: #2F4F4F;
            padding: 10px;
            z-index: 10;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<h1 style="text-align: center; color: white;">🚨 **EscalateAI - Escalation Tracking System**</h1>', unsafe_allow_html=True)

# Create two columns (1 for manual entry/upload, 2 for Kanban board)
col1, col2 = st.columns([1, 3])  # Increase width for the Kanban board (3) and manual entry/upload (1)

# Manual Entry and Upload Excel Tracker on the left (col1)
with col1:
    st.subheader("📤 **Upload Escalation Tracker**")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        st.write(df)
        download_excel()

    st.subheader("📝 **Manual Entry - Log Escalation**")
    with st.form(key="manual_entry_form"):
        customer_name = st.text_input("Customer Name")
        brief_issue = st.text_area("Brief Issue")
        criticality = st.selectbox("Criticality", ["Low", "Medium", "High"])
        impact = st.selectbox("Impact", ["Low", "Medium", "High"])
        action_owner = st.text_input("Action Owner")
        date_reported = st.date_input("Date Reported")

        submit_button = st.form_submit_button(label="Submit Issue")

        if submit_button:
            if customer_name and brief_issue and action_owner:
                sentiment, urgency, escalated = analyze_issue(brief_issue)
                row = {
                    "customer": customer_name,
                    "brief issue": brief_issue,
                    "issue reported date": str(date_reported),
                    "action taken": "Pending",
                    "owner": action_owner,
                    "status": "Open"
                }
                log_case(row, sentiment, urgency, escalated)

# Kanban Board on the right (col2)
with col2:
    show_kanban()

# Download Button at the bottom
download_excel()
