import os

from deta import Deta
import streamlit as st
# from dotenv import load_dotenv

# load_dotenv(".env")
# DETA_KEY = os.getenv("DETA_KEY")
# deta = Deta(DETA_KEY)

deta = Deta(st.secrets["deta_key"])

db = deta.Base("monthly_report")

def insert_period(years, period, dates, incomes, expenses):
    """Returns the report on a successful creation, otherwise raises an error"""
    return db.put({"key": dates, "years": years, "period": period, "incomes": incomes, "expenses": expenses})

def fetch_all_periods():
    """Returns a dict of all periods"""
    res = db.fetch()
    return res.items

def get_year(year):
    """Returns a dict of all periods"""
    res = db.fetch({'period?contains': year})
    return res.items


def get_period(period):
    """If not found, the function will return None"""
    return db.fetch({"period": period})


# ------------- USER DATABASE ------------------------
dbu = deta.Base("users_db")

def insert_user(username, name, password):
    return dbu.put({"key":username, 'name': name, 'password': password})

def fetch_all_users():
    """Returns a dict of all users"""
    res = dbu.fetch()
    return res.items

def get_user(username):
    return dbu.get(username)

def update_user(username, updates):
    return dbu.update(updates, username)

def delete_user(username):
    return dbu.delete(username)