import streamlit as st
import pandas as pd

# ---------------------------------
# Set Page Configuration
# ---------------------------------
st.set_page_config(page_title="EscalateAI", layout="wide")

# ---------------------------------
# NLP-Based Issue Analysis
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    sentiment = "Negative" if any(
        word in text_lower for word in ["delay", "issue", "problem", "fail", "dissatisfaction"]
    ) else "Positive"
    urgency = "High" if any(
        word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]
    ) else "Low"
    escalation = sentiment == "Negative" and urgency == "High"
    return sentiment, urgency, escalation

# ---------------------------------
# Logging Escalations
# ---------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []

    st.session_state.cases.append({
        "Brief Issue": row["brief issue"],
        "Customer": row.get("customer", "N/A"),
        "Reported Date": row.get("issue reported date", "N/A"),
        "Action Taken": row.get("action taken", "N/A"),
        "Owner": row.get("owner", "N/A"),
        "Status": row.get("status", "Open"),
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
    })

# ---------------------------------
# Kanban Board Display
# ---------------------------------
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
# UI Header
# ---------------------------------
st.title("🚨 EscalateAI - Customer Escalation Tracker")

# ---------------------------------
# Sidebar - File Upload and Manual Entry
# ---------------------------------
with st.sidebar:
    st.header("📥 Upload Escalation Tracker (Excel)")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    st.markdown("---")
    st.header("📝 Quick Manual Entry")
    manual_issue = st.text_area("Enter Customer Issue")

    if st.button("Analyze Manual Issue"):
        if manual_issue.strip():
            sentiment, urgency, escalated = analyze_issue(manual_issue)
            row = {
                "brief issue": manual_issue,
                "customer": "Manual Entry",
                "issue reported date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "action taken": "N/A",
                "owner": "Unassigned",
                "status": "Open"
            }
            log_case(row, sentiment, urgency, escalated)
            if escalated:
                st.warning("🚨 Escalation Triggered!")
            else:
                st.success("Logged without escalation.")
        else:
            st.error("Please enter an issue before analyzing.")

    st.markdown("---")
    with st.expander("➕ Detailed Manual Entry"):
        customer = st.text_input("Customer Name")
        detailed_issue = st.text_area("Issue Description")
        owner = st.text_input("Owner")
        if st.button("Add Detailed Issue"):
            if detailed_issue.strip():
                sentiment, urgency, escalated = analyze_issue(detailed_issue)
                row = {
                    "brief issue": detailed_issue,
                    "customer": customer or "Manual",
                    "issue reported date": pd.Timestamp.now().strftime("%Y-%m-%d"),
                    "action taken": "N/A",
                    "owner": owner or "Unassigned",
                    "status": "Open"
                }
                log_case(row, sentiment, urgency, escalated)
                if escalated:
                    st.warning("🚨 Escalation Triggered!")
                else:
                    st.success("Issue logged.")
            else:
                st.error("Issue description cannot be empty.")

# ---------------------------------
# File-based Case Logging
# ---------------------------------
if file:
    df = pd.read_excel(file)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

    required_cols = {"brief issue"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error("The uploaded Excel file must contain at least a 'brief issue' column.")
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

# ---------------------------------
# Display Kanban Board
# ---------------------------------
show_kanban()
