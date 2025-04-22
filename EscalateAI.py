import streamlit as st
import pandas as pd
import random
import string
from io import BytesIO

# Set Page Configuration
st.set_page_config(page_title="EscalateAI", layout="wide")

# ---------------------------------
# Helper Functions
# ---------------------------------

# Generate a unique escalation ID in the format SESICE-XXXXX
def generate_escalation_id():
    return f"SESICE-{''.join(random.choices(string.ascii_uppercase + string.digits, k=5))}"

# Analyze the issue using NLP (sentiment, urgency, and escalation)
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

# Logging the case into the session state
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    escalation_id = generate_escalation_id()
    
    st.session_state.cases.append({
        "ID": escalation_id,
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

# Export escalations to Excel
def export_to_excel():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.warning("No data available to export.")
        return
    
    df_export = pd.DataFrame(st.session_state.cases)
    towrite = BytesIO()
    df_export.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    st.download_button(
        label="Download Escalations",
        data=towrite,
        file_name="escalations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ---------------------------------
# Show Kanban Board
# ---------------------------------
def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.markdown("## 🗂️ Escalation Kanban Board")
    st.markdown("### Track issues visually by status")

    cols = st.columns(3)
    stages = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    # Define the valid statuses
    valid_statuses = ["Open", "In Progress", "Resolved"]

    with cols[0]: st.markdown("### 🟡 Open")
    with cols[1]: st.markdown("### 🟠 In Progress")
    with cols[2]: st.markdown("### ✅ Resolved")

    for i, case in enumerate(st.session_state.cases):
        status = case["Status"]

        # Check if the status is valid, else skip the case
        if status not in valid_statuses:
            st.warning(f"⚠️ Invalid status found for case ID {case['ID']}. Skipping this case.")
            continue

        bg_color = (
            "#ffe0e0" if case["Escalated"] else
            "#fff7e6" if case["Urgency"] == "High" else
            "#e7f6ff"
        )
        with stages[status]:
            with st.container():
                st.markdown(
                    f"""
                    <div style='
                        background-color: {bg_color};
                        padding: 15px;
                        border-radius: 12px;
                        margin: 10px 0;
                        box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
                        font-size: 15px;
                    '>
                        <strong>🆔 {case['ID']}</strong><br>
                        <b>🧾 Issue:</b> {case['Brief Issue']}<br>
                        <b>🧠 Sentiment:</b> <code>{case['Sentiment']}</code><br>
                        <b>⚡ Urgency:</b> <code>{case['Urgency']}</code><br>
                        <b>📅 Reported:</b> {case['Reported Date']}<br>
                        <b>👤 Owner:</b> {case['Owner']}<br>
                        <b>🛠️ Action:</b> {case['Action Taken']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                new_status = st.selectbox(
                    "Update Status",
                    ["Open", "In Progress", "Resolved"],
                    index=["Open", "In Progress", "Resolved"].index(status),
                    key=f"{i}_status"
                )
                st.session_state.cases[i]["Status"] = new_status

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("🚨 EscalateAI - Generic Escalation Tracking")

with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])
    customer_issue = st.text_area("Enter Customer Issue", height=150)

if file:
    df = pd.read_excel(file)

    # Normalize column names: Remove extra spaces, convert to lowercase for comparison
    df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

    required_cols = {"brief issue"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error("The uploaded Excel file must contain at least an 'Issue' column.")
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

elif customer_issue:
    if st.button("🔍 Analyze & Log Escalation"):
        sentiment, urgency, escalated = analyze_issue(customer_issue)
        # Here, you would log the escalation for the entered issue
        log_case({"brief issue": customer_issue}, sentiment, urgency, escalated)
        if escalated:
            st.warning("🚨 Escalation Triggered!")
        else:
            st.success("Logged without escalation.")

# Show Kanban board
show_kanban()

# Export escalations to Excel
export_to_excel()
