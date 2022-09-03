import calendar  # Core Python Module
from datetime import datetime
from logging import PlaceHolder  # Core Python Module
import streamlit as st
import streamlit_authenticator as stauth  # pip install streamlit-authenticator
# from streamlit_option_menu import option_menu  # pip install streamlit-option-menu
import pandas as pd
# import plotly.graph_objects as go
import altair as alt
from collections import Counter

import database as db

# -------------- SETTINGS --------------
incomes = ["Salary", "Investment Income", "Other Income"]
expenses = ["Utilities", "Morgage", "Dining Out", "Groceries", "Transport", "Hobby", "Other Expenses"]
currency = "AUD"
page_title = "Expense Tracker"
# page_icon = ":money_with_wings:"  # emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
layout = "centered"

st.set_page_config(page_title=page_title, layout=layout) #page_icon=page_icon
st.title(page_title) #+ " " + page_icon)

# --- HIDE STREAMLIT STYLE ---
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --------------------------------------

# --------------- USER AUTHENTIFICATION ---------------------------
users = db.fetch_all_users()
# print(users)

usernames = [user['key'] for user in users]
names = [user['name'] for user in users]
hashed_passwords = [user['password'] for user in users]

credentials = {"usernames":{}}

for un, name, pw in zip(usernames, names, hashed_passwords):
    user_dict = {"name":name,"password":pw}
    credentials["usernames"].update({un:user_dict})

authenticator = stauth.Authenticate(credentials, "tracker", "abcdef", cookie_expiry_days=30)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status == False:
    st.error("Username/password is incorrect")

if authentication_status == None:
    st.warning("Please enter your username and password")

if authentication_status:
    # --- DROP DOWN VALUES FOR SELECTING THE PERIOD ---
    years = [datetime.today().year, datetime.today().year - 1]
    months = list(calendar.month_name[1:])
    # print(months)

    # --- DATABASE INTERFACE ---
    def get_all_periods():
        items = db.fetch_all_periods()
        periods = [item["period"] for item in items]
        return periods

    def get_all_years():
        items = db.fetch_all_periods()
        years = [item["years"] for item in items]
        return years

    authenticator.logout("Logout", "sidebar")
    st.sidebar.header(f"Welcome {name}")
    st.sidebar.subheader(f"Data Entry in {currency}")
    # ------------ DATA ENTRY SIDEBAR ------------------------
    with st.sidebar:
        col1, col2, col3 = st.columns(3)
        col1.selectbox("Select Year:", years, key="year", index=0)
        col2.selectbox("Select Month:", months, key="month", index=datetime.today().month-1)
        year = int(st.session_state["year"])
        month = months.index(st.session_state["month"])
        # print(calendar.monthrange(year, month)[1])
        num_days = calendar.monthrange(year, month+1)[1] # Add one to get the correct month
        days = [day for day in range(1, num_days+1)] # Add one to get the correct no of days of the month
        # print(year, month, days)
        # print(calendar.monthrange(year,month+1))

        col3.selectbox("Select Day:", days, key="day", index=datetime.today().day-1)
        day = int(st.session_state["day"])

        years = str(st.session_state["year"])
        period = str(st.session_state["year"]) + "_" + str(st.session_state["month"])
        dates = str(st.session_state["year"]) + "_" + str(st.session_state["month"]) + "_" + str(st.session_state["day"])
        res = db.fetch_all_periods()

        ex_expenses = dict.fromkeys(expenses, 0)
        ex_incomes = dict.fromkeys(incomes, 0)
        for i in range(len(res)):
            if res[i]['key'] == dates:
                ex_expenses = res[i]['expenses']
                ex_incomes = res[i]['incomes']

        "---"
        with st.sidebar.form("entry_form"):
            with st.expander("Income"):
                for key, val in ex_incomes.items():
                    st.number_input(f"{key}:", min_value=0, format="%i", step=10, key=key, value=val)

            with st.expander("Expenses"):
                for key, val in ex_expenses.items():
                    st.number_input(f"{key}:", min_value=0, format="%i", step=10, key=key, value=val)
            # with st.expander("Comment"):
            #     comment = st.text_area("", placeholder="Enter a comment here ...")
        
            "---"
            submitted = st.form_submit_button("Save Data")
            if submitted:
 
                incomes = {income: st.session_state[income] for income in incomes}
                expenses = {expense: st.session_state[expense] for expense in expenses}
                
                db.insert_period(years, period, dates, incomes, expenses)
                st.success('Data saved!')

    ## ------------ DATA VISUALISATION ------------------------------
    with st.form("saved_periods"):
        period = st.selectbox("Month Summary", set(get_all_periods()))
        submitted = st.form_submit_button("Plot")
        if submitted:
            # Get data from database
            period_data = db.get_period(period)

            expenses_need = Counter() # Need = Utilities and Morgage
            expenses_want = Counter()
            # print(expenses[:2])
            for elem in period_data.items:
                for key, value in elem["expenses"].items():
                    if key in expenses[:2]:
                        expenses_need[key] += value
                    else:
                        expenses_want[key] += value

            incomes = Counter()
            for elem in period_data.items:
                for key, value in elem["incomes"].items():
                    incomes[key] += value

            # Create metrics
            total_income = sum(incomes.values())
            total_expense_need = sum(expenses_need.values())
            total_expense_want = sum(expenses_want.values())
            remaining_budget = total_income - total_expense_need - total_expense_want
            pct_expense_need = int((total_expense_need / total_income) * 100)
            pct_expense_want = int((total_expense_want / total_income) * 100)
            pct_remaining_budget = int((remaining_budget / total_income) * 100)
            st.metric("Month Income", f"$ {total_income}")
            col1, col2= st.columns(2)
            col1.metric("Month Expense - Need", f"$ {total_expense_need} ({pct_expense_need} %)")
            col2.metric("Month Expense - Want", f"$ {total_expense_want} ({pct_expense_want} %)")
            st.metric("Month Saving", f"$ {remaining_budget} ({pct_remaining_budget} %)")
            # st.text(f"Comment: {comment}")

            expenses_merged = {**expenses_need, **expenses_want}
            # print(expenses_merged)
            data = pd.DataFrame({'keys': expenses_merged.keys(), 'values': expenses_merged.values()})
            c = alt.Chart(data).mark_bar().encode(
                x=alt.X('keys', axis=alt.Axis(title=None)), y=alt.Y('values', axis=alt.Axis(title='$ (AUD)')))

            st.altair_chart(c, use_container_width=True)

    with st.form("saved_year"):
        year = st.selectbox("Yearly tracker", set(get_all_years()))
        res = db.get_year(year)
        # res = db.fetch_all_periods()
        # print(res)
        submitted_y = st.form_submit_button("Plot")
        if submitted_y:

            list_period = []
            for elem in res:
                if elem["period"] not in list_period:
                    list_period.append(elem["period"])
            list_period = set(list_period)

            income_month = {}
            income_invest_month = {}
            expense_month = {}
            for p in list_period:
                expenses = Counter()
                incomes = Counter()
                for elem in res:
                    if p == elem["period"]:
                        for key, value in elem["expenses"].items():
                            expenses[key] += value

                        for key, value in elem["incomes"].items():
                            incomes[key] += value

                # Create metrics
                total_income_invest = sum(value for key, value in incomes.items() if key == 'Investment Income')
                # print(total_income_invest)
                total_income = sum(incomes.values()) - total_income_invest
                total_expense = sum(expenses.values())

                income_month[p] = total_income
                income_invest_month[p] = total_income_invest
                expense_month[p] = total_expense

            df1 = pd.DataFrame(income_month.items(), columns=["period", "income"])
            df2 = pd.DataFrame(income_invest_month.items(), columns=["period", "investment income"])
            df3 = pd.DataFrame(expense_month.items(), columns=["period", "expense"])

            # df = pd.merge(df1, df2, df3, on="period")
            df = df1.merge(df2, on="period").merge(df3, on="period")
            data = df.reset_index().melt('period', ignore_index = False)

            data = data[data['variable']!='index']
            replacement_map = {mon: int(i+1) for i, mon in enumerate(months)}

            data['month'] = data['period'].str[5:].map(replacement_map)
            data = data.sort_values('month')

            c = alt.Chart(data).mark_line().encode(
                x=alt.X('month', axis=alt.Axis(tickMinStep=1, title='Month')),
                y=alt.Y('value', axis=alt.Axis(title='$ (AUD)')),
                color=alt.Color('variable', legend=alt.Legend(
                    orient='none',legendX=30, legendY=-16,
                    direction='horizontal',titleAnchor='middle')))
            
            st.altair_chart(c, use_container_width=True)
