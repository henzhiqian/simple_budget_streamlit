import calendar  # Core Python Module
from datetime import datetime
import pandas as pd  # Core Python Module
from dateutil.relativedelta import relativedelta

import plotly.graph_objects as go  # pip install plotly
import streamlit as st  # pip install streamlit
from streamlit_option_menu import option_menu  # pip install streamlit-option-menu

import database as db  # local import
import creditcard # local import

# -------------- SETTINGS --------------
incomes = ["Salary", "Investment", "Other Income"]
expenses = ["Rent", "Utilities", "Groceries", "Food", "Other Expenses", "Parents"]
currency = "SGD"
page_title = "Income and Expense Tracker"
page_icon = ":money_with_wings:"  # emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
layout = "centered"
# --------------------------------------

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
st.title(page_title + " " + page_icon)

# --- DROP DOWN VALUES FOR SELECTING THE PERIOD ---


# --- DATABASE INTERFACE ---
# def get_all_periods():
#     items = db.fetch_all_periods()
#     periods = [item["key"] for item in items]
#     return periods


# --- HIDE STREAMLIT STYLE ---
# hide_st_style = """
#             <style>
#             #MainMenu {visibility: hidden;}
#             footer {visibility: hidden;}
#             header {visibility: hidden;}
#             </style>
#             """
# st.markdown(hide_st_style, unsafe_allow_html=True)

# --- NAVIGATION MENU ---
selected = option_menu(
    menu_title=None,
    options=["Data Entry", "Data Visualization"],
    icons=["pencil-fill", "bar-chart-fill"],  # https://icons.getbootstrap.com/
    orientation="horizontal",
)

# --- INPUT & SAVE PERIODS ---
if selected == "Data Entry":
    input_date = st.date_input("Input Date", datetime.today())  

    option = st.selectbox('How would you like to import data?', ('Credit card bills', 'Bank sync', 'Manual Entry'))

    if option == 'Credit card bills':
        uploaded_file = st.file_uploader("Upload credit card statement", ["pdf", "PDF"])
        if uploaded_file is not None:
            with open('./temp/tmp.pdf', 'wb') as f:
                f.write(uploaded_file.getbuffer())
            df = creditcard.read_creditcard('./temp/tmp.pdf')
            # st.write(df)
 

    elif option == 'Bank sync':
        banks_lst = st.selectbox('Which bank would you like to sync?', ('All', 'DBS', 'OCBC', 'UOB', 'Endowus'))

    # --- Manual Entry ---
    elif option == 'Manual Entry':
        st.header(f"Manual Entry in {currency}")
        with st.form("entry_form", clear_on_submit=True):

            "---"
            # if st.checkbox("Manual Entry"):
            with st.expander("Income"):
                for income in incomes:
                    st.number_input(f"{income}:", min_value=0, format="%i", step=10, key=income)
            with st.expander("Expenses"):
                for expense in expenses:
                    st.number_input(f"{expense}:", min_value=0, format="%i", step=10, key=expense)
            with st.expander("Comment"):
                comment = st.text_area("", placeholder="Enter a comment here ...")

            "---"
            submitted = st.form_submit_button("Save Data")
            if submitted:
                dt = st.session_state['input_date']
                incomes = {income: st.session_state[income] for income in incomes}
                expenses = {expense: st.session_state[expense] for expense in expenses}
                
                # prepare df
                df = pd.DataFrame(columns = ['datetime', 'income_amt', 'income_type', 'expense_amt', 'expense_type', 'comment'])
                for k,v in incomes.items():
                    df.loc[len(df)] = [dt, v, k, 0, '', comment]
                
                for k,v in expenses.items():
                    df.loc[len(df)] = [dt, v, k, 0, '', comment]

                db.insert_period(df)
                st.success("Data saved!")


# --- PLOT PERIODS ---
if selected == "Data Visualization":
    st.header("Data Visualization")
    with st.form("saved_periods"):
        start_date = st.date_input("Start Date", datetime.today() - relativedelta(days=30))
        end_date = st.date_input("End Date", datetime.today())
        submitted = st.form_submit_button("Plot Period")

        if submitted:
            # Get data from database
            period_data = db.get_period(start_date, end_date)
            income_type = period_data["income_type"].tolist()
            income_amt = period_data["income_amt"].tolist()
            expense_type = period_data["expense_type"].tolist()
            expense_amt = period_data["expense_amt"].tolist()

            # Create metrics
            total_income = period_data['income_amt'].sum()
            total_expense = period_data['expense_amt'].sum()
            remaining_budget = total_income - total_expense
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Income", f"{total_income} {currency}")
            col2.metric("Total Expense", f"{total_expense} {currency}")
            col3.metric("Remaining Budget", f"{remaining_budget} {currency}")

            # Create sankey chart
            label = income_type + ["Total Income"] + expense_type
            source = list(range(len(income_amt))) + [len(income_amt)] * len(expense_amt)
            target = [len(income_amt)] * len(income_amt) + [label.index(expense) for expense in expense_type]
            value = income_amt + expense_amt
            
            # Data to dict, dict to sankey
            link = dict(source=source, target=target, value=value)
            node = dict(label=label, pad=20, thickness=30, color="#E694FF")
            data = go.Sankey(link=link, node=node)

            # Plot it!
            fig = go.Figure(data)
            fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)
            