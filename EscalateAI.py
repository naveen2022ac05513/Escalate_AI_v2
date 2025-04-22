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
# Generate Unique Escalation ID in CESI-XXXXXX Format
# ---------------------------------
def generate_escalation_id():
    if "last_id" not in st.session_state:
        st.session_state.last_id = 0
    st.session_state.last_id += 1
    return f"CESI-{st.session_state.last_id:06d}"

# ---------------------------------
# Logging Escalations
# ---------------------------------
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

# ---------------------------------
# Display Kanban Board
# ---------------------------------
def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.markdown("## 🗂️ Escalation Kanban Board")
    st.markdown("### Track issues visually by status")

    cols = st.columns(3)
    stages = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    with cols[0]: st.markdown("### 🟡 Open")
    with cols[1]: st.markdown("### 🟠 In Progress")
    with cols[2]: st.markdown("### ✅ Resolved")

    for i, case in enumerate(st.session_state.cases):
        status = case["Status"]
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
    df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

    required_cols = {"brief issue"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error("The uploaded Excel file must contain at least a 'brief issue' column.")
    else:
        df["selector"] = df["brief issue"].astype(str)
        selected = st.selectbox("Select Case from Excel", df["selector"])
        row = df[df["selector"] == selected].iloc[0]

        st.subheader("📄 Issue Details")
        for col in df.columns:
            st.write(f"**{col.capitalize()}:** {row.get(col, 'N/A')}")

        if st.button("🔍 Analyze & Log Selected Case"):
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

# ---------------------------------
# Export Escalations to Excel
# ---------------------------------
if "cases" in st.session_state and st.session_state.cases:
    df_export = pd.DataFrame(st.session_state.cases)

    st.markdown("---")
    st.subheader("📤 Export Escalations")
    st.download_button(
        label="⬇️ Download Escalations as Excel",
        data=df_export.to_excel(index=False),  # Removed engine='openpyxl'
        file_name="escalations.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
