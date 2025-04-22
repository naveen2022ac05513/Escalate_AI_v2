import streamlit as st
import pandas as pd
import random
import io

# Set Page Configuration
st.set_page_config(page_title="EscalateAI", layout="wide")

# Define the list of negative sentiment words and phrases
negative_words = [
    "problematic", "delay", "issue", "failure", "dissatisfaction", "horrible", "frustration", 
    "unacceptable", "terrible", "mistake", "disappointed", "angry", "complaint", "unhappy", 
    "regret", "worst", "lost", "trouble", "missed", "irritated", "displeased", "rejected", 
    "denied", "not satisfied", "unresolved", "unresponsive", "unreliable", "subpar", "unstable", 
    "negative impact", "setback", "annoyed", "frustrating", "non-compliance", "broken", 
    "inconvenience", "defective", "overdue", "escalation", "no progress"
]

negative_phrases = [
    "this is unacceptable", "not up to the mark", "we are disappointed with", "this has caused a delay",
    "it’s not working as expected", "this is a huge inconvenience", "we are dissatisfied with", 
    "the system failed to", "the response was inadequate", "we are experiencing issues"
]

# ---------------------------------
# NLP-Based Issue Analysis
# ---------------------------------
def analyze_issue(text):
    # Convert text to lowercase for consistent comparison
    text_lower = text.lower()

    # Check for negative sentiment by looking for the words and phrases in the text
    sentiment = "Negative" if any(word in text_lower for word in negative_words) or any(phrase in text_lower for phrase in negative_phrases) else "Positive"

    # Determine urgency based on specific keywords
    urgency = "High" if any(word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]) else "Low"

    # Define escalation condition based on negative sentiment and high urgency
    escalation = sentiment == "Negative" and urgency == "High"
    return sentiment, urgency, escalation

# ---------------------------------
# Logging Escalations
# ---------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []

    escalation_id = f"SESICE-{str(random.randint(10000, 99999))}"

    st.session_state.cases.append({
        "Escalation ID": escalation_id,
        "Customer": row["customer"],
        "Brief Issue": row["brief issue"],
        "Reported Date": row.get("issue reported date", "N/A"),
        "Action Taken": row.get("action taken", "N/A"),
        "Owner": row.get("owner", "N/A"),
        "Status": row.get("status", "Open"),
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
    })

def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.subheader("📌 Escalation Kanban Board")
    cols = st.columns(3)
    stages = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    for i, case in enumerate(st.session_state.cases):
        with stages[case["Status"]]:
            st.markdown("----")
            st.markdown(f"**🧾 Issue: {case['Brief Issue']}**")
            st.write(f"🔹 Sentiment: `{case['Sentiment']}` | Urgency: `{case['Urgency']}`")
            st.write(f"📅 Reported: {case['Reported Date']} | 👤 Owner: {case.get('Owner', 'N/A')}")
            st.write(f"✅ Action Taken: {case.get('Action Taken', 'N/A')}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{i}_status"
            )
            st.session_state.cases[i]["Status"] = new_status

# ---------------------------------
# Download Excel Functionality
# ---------------------------------
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
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("🚨 EscalateAI - Generic Escalation Tracking")

with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file)

    # Normalize column names: Remove extra spaces, convert to lowercase for comparison
    df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

    required_cols = {"brief issue", "customer", "issue reported date", "action taken", "owner"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error(f"The uploaded Excel file is missing the following columns: {', '.join(missing_cols)}")
    else:
        df["selector"] = df["brief issue"].astype(str)
        selected = st.selectbox("Select Case", df["selector"])
        row = df[df["selector"] == selected].iloc[0]

        st.subheader("📄 Issue Details")
        for col in df.columns:
            st.write(f"**{col.capitalize()}:** {row.get(col, 'N/A')}")

        if st.button("🔍 Analyze & Log Escalation"):
            sentiment, urgency, escalated = analyze_issue(row["brief issue"])
            log_case(row, sentiment, urgency, escalated)
            if escalated:
                st.warning("🚨 Escalation Triggered!")
            else:
                st.success("Logged without escalation.")

# Manual Entry Form
col1, col2 = st.columns([1, 2])  # Create two columns (1 for manual entry, 2 for Kanban board)

with col1:
    st.subheader("📝 Manual Entry - Log Escalation")
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
                if escalated:
                    st.warning("🚨 Escalation Triggered!")
                else:
                    st.success("Logged without escalation.")
            else:
                st.error("Please fill in all required fields!")

with col2:
    # Show Kanban board
    show_kanban()

# Download Excel button
download_excel()

