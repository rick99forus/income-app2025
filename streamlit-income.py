import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
from fpdf import FPDF
# import matplotlib.pyplot as plt

# Configure the Streamlit page
st.set_page_config(
    page_title="TaxImple",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
SUPER_RATE = 0.11
PENALTY_RATE_MULTIPLIER = 1.5
BUSINESS_NAME = "Make It Simple Pty Ltd"

# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = 0
if "header_section" not in st.session_state:
    st.session_state["header_section"] = "home"
if "income_data" not in st.session_state:
    st.session_state["income_data"] = []
if "edit_index" not in st.session_state:
    st.session_state["edit_index"] = None
if "view_index" not in st.session_state:
    st.session_state["view_index"] = None

# Navigation Functions
def navigate_to(section):
    st.session_state["header_section"] = section
    st.session_state["page"] = 0

# Tax calculation
def calculate_tax(yearly_income):
    if yearly_income <= 18200:
        return 0
    elif yearly_income <= 45000:
        return (yearly_income - 18200) * 0.19
    elif yearly_income <= 120000:
        return 5092 + (yearly_income - 45000) * 0.325
    elif yearly_income <= 180000:
        return 29467 + (yearly_income - 120000) * 0.37
    else:
        return 51667 + (yearly_income - 180000) * 0.45

# Calculate hours worked
def calculate_hours(start, end):
    format_str = "%I:%M %p"
    try:
        start_time = datetime.strptime(start, format_str)
        end_time = datetime.strptime(end, format_str)
        if start_time >= end_time:
            end_time += timedelta(days=1)
        
        hours = (end_time - start_time).seconds / 3600
        
        # Deduct 0.5 hours (30 min) unpaid break for shifts over 6 hours
        if hours > 6:
            hours -= 0.5
        
        return hours
    except ValueError:
        return 0

# Penalty rate application
def apply_penalty_rates(start, end, hourly_rate):
    base_hours = calculate_hours(start, end)
    penalty_hours = 0
    if base_hours > 0:
        start_time = datetime.strptime(start, "%I:%M %p").time()
        end_time = datetime.strptime(end, "%I:%M %p").time()
        if end_time > datetime.strptime("08:00 PM", "%I:%M %p").time():
            penalty_hours += (
                datetime.combine(datetime.min, end_time) - datetime.strptime("08:00 PM", "%I:%M %p")
            ).seconds / 3600
    regular_income = (base_hours - penalty_hours) * hourly_rate
    penalty_income = penalty_hours * hourly_rate * PENALTY_RATE_MULTIPLIER
    return base_hours, regular_income, penalty_income

def format_time_input(time_str):
    if len(time_str) == 2 and ':' not in time_str:
        return time_str + ":"
    return time_str

def combine_time_inputs(time_str, am_pm):
    time_str = format_time_input(time_str)
    return f"{time_str} {am_pm}"

# Learn Section Functions
def learn_entitlements():
    st.title("Learn Your Entitlements")
    st.markdown("""
    Here you can learn about your entitlements as an employee in Australia, such as:
    - Leave entitlements (annual, personal, and parental leave).
    - Fair Work Commission (FWC) pay guidelines.
    - Rights under workplace agreements.
    """)
    st.button("Back to Home", on_click=lambda: navigate_to("home"))

def learn_taxes():
    st.title("Learn Your Taxes")
    st.markdown("""
    Learn about how taxes work in Australia, including:
    - Income tax brackets for the 2023-2024 financial year.
    - Deductions and offsets.
    - Understanding PAYG (Pay-As-You-Go) taxation.
    """)
    st.button("Back to Home", on_click=lambda: navigate_to("home"))

def learn_budget():
    st.title("Learn Your Budget")
    st.markdown("""
    Learn how to manage your budget effectively:
    - Track your income and expenses.
    - Set savings goals.
    - Plan for retirement with superannuation.
    """)
    st.button("Back to Home", on_click=lambda: navigate_to("home"))

# Header with Hover Effect
header_style = """
<style>
.header {
    position: fixed;
    top: 0;
    width: 100%;
    background-color: #ffffff;
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 20px;
}

.header .title {
    font-size: 24px;
    font-weight: bold;
    color: #2196F3;
}

.header .menu {
    display: flex;
    align-items: center;
}

.header .menu .dropdown {
    display: none;
    position: absolute;
    background-color: #ffffff;
    box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.2);
    z-index: 1;
    right: 20px;
    top: 50px;
}

.header .menu .dropdown a {
    color: black;
    padding: 12px 16px;
    text-decoration: none;
    display: block;
}

.header .menu .dropdown a:hover {
    background-color: #f1f1f1;
}

.header .menu:hover .dropdown {
    display: block;
}

@media (max-width: 768px) {
    .header .menu {
        display: none;
    }

    .header .burger {
        display: block;
    }
}

.burger {
    display: none;
    cursor: pointer;
}

.burger div {
    width: 25px;
    height: 3px;
    background-color: #2196F3;
    margin: 5px;
}

.sidebar-item {
    position: relative;
    padding: 10px;
    margin-bottom: 10px;
    background-color:rgb(30, 30, 30);
    color: #ffffff;
    border-radius: 10px;
    box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.85);
}

.sidebar-item:hover .sidebar-buttons {
    display: block;
}

.sidebar-buttons {
    display: none;
    position: absolute;
    bottom: -20px;
    text-align: center;
}
</style>
<div class="header">
    <div class="title">TaxImple</div>
    <div class="menu">
        <div class="dropdown">
            <a href="#" onclick="Streamlit.setComponentValue('entitlements')">Learn Your Entitlements</a>
            <a href="#" onclick="Streamlit.setComponentValue('taxes')">Learn Your Taxes</a>
            <a href="#" onclick="Streamlit.setComponentValue('budget')">Learn Your Budget</a>
        </div>
    </div>
    <div class="burger" onclick="toggleMenu()">
        <div></div>
        <div></div>
        <div></div>
    </div>
</div>
<script>
function toggleMenu() {
    const menu = document.querySelector('.header .menu');
    menu.style.display = menu.style.display === 'flex' ? 'none' : 'flex';
}

const links = document.querySelectorAll(".dropdown a");
links.forEach(link => {
    link.addEventListener("click", event => {
        event.preventDefault();
        const section = event.target.innerHTML.toLowerCase().replace(" ", "_");
        window.location.href = "?header_section=" + section;
    });
});
</script>
"""
st.markdown(header_style, unsafe_allow_html=True)

# Main Application Logic
if st.session_state["header_section"] == "entitlements":
    learn_entitlements()
elif st.session_state["header_section"] == "taxes":
    learn_taxes()
elif st.session_state["header_section"] == "budget":
    learn_budget()
elif st.session_state["header_section"] == "view":
    index = st.session_state["view_index"]
    data = st.session_state["income_data"][index]
    st.title(f"Income Breakdown for Week {data['week']}")
    st.metric("Gross Income", f"${data['gross_income']:.2f}")
    st.metric("Taxes Owed", f"${data['taxes_owed']:.2f}")
    st.metric("Net Income", f"${data['net_income']:.2f}")
    st.metric("Superannuation Contribution", f"${data['superannuation']:.2f}")
    st.metric("Income Minus Tax and Super", f"${data['income_minus_tax_and_super']:.2f}")

    # Income Breakdown Chart
    fig = go.Figure(
        go.Pie(
            labels=["Net Income", "Taxes Owed", "Superannuation"],
            values=[data['net_income'], data['taxes_owed'], data['superannuation']],
            hole=0.4
        )
    )
    fig.update_layout(title="Income Breakdown")
    st.plotly_chart(fig, use_container_width=True)

    # Back Button
    if st.button("Back"):
        st.session_state["header_section"] = "home"
        st.experimental_rerun()
else:
    # Main Application Content (Default Home Screen)
    st.title("Income and Tax Calculator")
    
    # Desktop Layout
    col1, col2 = st.columns(2)
    
    # Income Form (Left Column)
    start_time_placeholder = "HH:MM"
    end_time_placeholder = "HH:MM"
    with col1:
        st.header("Income Form")
        position = st.selectbox("Position Type", ["Full-time", "Part-time", "Casual"], index=st.session_state.get("edit_position_index", 0))
        shift_type = st.selectbox("Shift Type", ["Day", "Afternoon", "Night"], index=st.session_state.get("edit_shift_type_index", 0))
        
        start_time_input = st.text_input("Start Time:", value=st.session_state.get("edit_start_time", ""), placeholder=start_time_placeholder)
        start_time_am_pm = st.selectbox("AM/PM", ["AM", "PM"], index=0 if "AM" in st.session_state.get("edit_start_time", "") else 1, key="start_am_pm")
        combined_start_time = combine_time_inputs(start_time_input, start_time_am_pm)

        end_time_input = st.text_input("End Time:", value=st.session_state.get("edit_end_time", ""), placeholder=end_time_placeholder)
        end_time_am_pm = st.selectbox("AM/PM", ["AM", "PM"], index=0 if "AM" in st.session_state.get("edit_end_time", "") else 1, key="end_am_pm")
        combined_end_time = combine_time_inputs(end_time_input, end_time_am_pm)
        
        hourly_rate = st.number_input("Hourly Rate ($)", min_value=0.0, step=0.5, value=st.session_state.get("edit_hourly_rate", 0.0))
        days_worked = st.multiselect("Days Worked", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=st.session_state.get("edit_days_worked", []))
        period = st.selectbox("Select Income Period:", ["Weekly", "Fortnightly", "Monthly", "Yearly"], index=st.session_state.get("edit_period_index", 0))

    # Income Results (Right Column)
    with col2:
        st.header("Results")
        if not start_time_input or not end_time_input or hourly_rate <= 0 or not days_worked:
            st.warning("Please fill out all inputs to view results.")
        else:
            total_hours, total_income, total_penalty_income = 0, 0, 0
            for _ in days_worked:
                hours, income, penalty_income = apply_penalty_rates(combined_start_time, combined_end_time, hourly_rate)
                total_hours += hours
                total_income += income
                total_penalty_income += penalty_income

            if period == "Weekly":
                income_multiplier = 1
            elif period == "Fortnightly":
                income_multiplier = 2
            elif period == "Monthly":
                income_multiplier = 4
            else:
                income_multiplier = 52

            total_hours *= income_multiplier
            total_income *= income_multiplier
            total_penalty_income *= income_multiplier

            gross_income = total_income + total_penalty_income
            yearly_income = gross_income * (52 / income_multiplier)
            yearly_tax = calculate_tax(yearly_income)
            period_tax = yearly_tax / (52 / income_multiplier)
            period_superannuation = gross_income * SUPER_RATE
            net_income = gross_income - period_tax
            income_minus_tax_and_super = gross_income - period_tax - period_superannuation

            st.metric("Total Hours", f"{total_hours:.2f}")
            st.metric("Gross Income", f"${gross_income:.2f}")
            st.metric("Taxes Owed", f"${period_tax:.2f}")
            st.metric("Net Income", f"${net_income:.2f}")
            st.metric("Superannuation Contribution", f"${period_superannuation:.2f}")
            st.metric("Income Minus Tax and Super", f"${income_minus_tax_and_super:.2f}")

            # Store or Update Results Button
            if st.session_state["edit_index"] is None:
                if st.button("Store Results"):
                    week_number = datetime.now().isocalendar()[1]
                    st.session_state["income_data"].append({
                        "week": week_number,
                        "position": position,
                        "shift_type": shift_type,
                        "start_time": start_time_input + " " + start_time_am_pm,
                        "end_time": end_time_input + " " + end_time_am_pm,
                        "hourly_rate": hourly_rate,
                        "days_worked": days_worked,
                        "period": period,
                        "gross_income": gross_income,
                        "taxes_owed": period_tax,
                        "net_income": net_income,
                        "superannuation": period_superannuation,
                        "income_minus_tax_and_super": income_minus_tax_and_super
                    })
            else:
                if st.button("Update Results"):
                    index = st.session_state["edit_index"]
                    st.session_state["income_data"][index] = {
                        "week": st.session_state["income_data"][index]["week"],
                        "position": position,
                        "shift_type": shift_type,
                        "start_time": start_time_input + " " + start_time_am_pm,
                        "end_time": end_time_input + " " + end_time_am_pm,
                        "hourly_rate": hourly_rate,
                        "days_worked": days_worked,
                        "period": period,
                        "gross_income": gross_income,
                        "taxes_owed": period_tax,
                        "net_income": net_income,
                        "superannuation": period_superannuation,
                        "income_minus_tax_and_super": income_minus_tax_and_super
                    }
                    st.session_state["edit_index"] = None

            # Display relevant entitlements based on position type
            st.header("Relevant Entitlements")
            if position == "Full-time":
                st.markdown("""
                - Annual leave: 4 weeks per year.
                - Personal/carer's leave: 10 days per year.
                - Public holidays: Paid if you normally work on the day.
                """)
            elif position == "Part-time":
                st.markdown("""
                - Annual leave: Pro-rata based on hours worked.
                - Personal/carer's leave: Pro-rata based on hours worked.
                - Public holidays: Paid if you normally work on the day.
                """)
            else:
                st.markdown("""
                - Casual loading: Typically 25% higher pay rate.
                - No paid leave entitlements.
                - Public holidays: Unpaid unless you work on the day.
                """)

    # Sidebar to display stored income data
    st.sidebar.header("Stored Income Data")
    for index, data in enumerate(st.session_state["income_data"]):
        with st.sidebar:
            st.markdown(f"""
            <div class="sidebar-item">
                <strong>Week {data['week']}</strong><br>
                Gross Income: ${data['gross_income']:.2f}
                <div class="sidebar-buttons">
                    <button onclick="window.location.href='?edit_index={index}'">Edit</button>
                    <button onclick="window.location.href='?view_index={index}'">View</button>
                    <button onclick="window.location.href='?delete_index={index}'">Delete</button>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Handle sidebar button clicks
    if "edit_index" in st.query_params:
        index = int(st.query_params["edit_index"][0])
        st.session_state["edit_index"] = index
        st.session_state["edit_position_index"] = ["Full-time", "Part-time", "Casual"].index(st.session_state["income_data"][index]["position"])
        st.session_state["edit_shift_type_index"] = ["Day", "Afternoon", "Night"].index(st.session_state["income_data"][index]["shift_type"])
        st.session_state["edit_start_time"] = st.session_state["income_data"][index]["start_time"]
        st.session_state["edit_end_time"] = st.session_state["income_data"][index]["end_time"]
        st.session_state["edit_hourly_rate"] = st.session_state["income_data"][index]["hourly_rate"]
        st.session_state["edit_days_worked"] = st.session_state["income_data"][index]["days_worked"]
        st.session_state["edit_period_index"] = ["Weekly", "Fortnightly", "Monthly", "Yearly"].index(st.session_state["income_data"][index]["period"])
        st.experimental_rerun()
    elif "view_index" in st.query_params:
        index = int(st.query_params["view_index"][0])
        st.session_state["view_index"] = index
        st.session_state["header_section"] = "view"
        st.experimental_rerun()
    elif "delete_index" in st.query_params:
        index = int(st.query_params["delete_index"][0])
        del st.session_state["income_data"][index]
        st.experimental_rerun()

# Disclaimer and Links
st.markdown("""
**Disclaimer:** This tool provides general information only and does not constitute financial advice. For more detailed information, please refer to the following resources:
- [Fair Work Commission](https://www.fwc.gov.au/)
- [Australian Taxation Office (ATO)](https://www.ato.gov.au/)
""")
