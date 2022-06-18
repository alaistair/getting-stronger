import altair as alt
import pandas as pd
import numpy as np
import streamlit as st
import sqlite3
from datetime import datetime

def main():
    st.set_page_config(layout="wide")

    # Load silver SQLite database
    PATH = './data/silver/'
    con = sqlite3.connect(f"{PATH}silver.sqlite")
    workout_names = get_workout_names(con)

    workout_dates = get_full_table(con)[['Date']]
    chart = workout_chart(workout_dates)
    st.altair_chart(chart)


    with st.expander("See history"):
        st.write(get_flat_table(con))

    with st.expander("See all workouts"):
        col1, col2, col3, col4 = st.columns((1,1,1,1))
        col1.write("#### Workout")
        col2.write("#### Latest")
        col3.write("#### Weight")
        col4.write("#### Reps")

        for workout_name in workout_names:
            last_workout_date, df_last_workout = get_last_workout(workout_name, con)
            col1.write(workout_name)
            col2.write(last_workout_date)
            col3.write(df_last_workout[0][1])
            col4.write(df_last_workout[0][2])


def workout_chart(workout_dates):
    # Convert datetime to date
    workout_dates['Date'] = workout_dates.applymap(lambda x: datetime.strptime(x, "%Y-%m-%d %H:%M:%S").date())
    # Count sets
    workout_dates = workout_dates.groupby(workout_dates['Date']).size().reset_index(name='Count')
    # Add weekday column
    workout_dates['Day of week'] = workout_dates['Date'].map(lambda x: x.weekday()+1)

    chart = alt.Chart(workout_dates).mark_rect().encode(
        y=alt.Y('yearmonthdate(Date):O'),
        x=alt.X('Day of week:O'),
        color=alt.Color('Count:Q', scale=alt.Scale(scheme="inferno"), sort="descending"),
    )

    return chart


def day_of_week(date):
    return date.datetime.weekday()


def get_full_table(con):
    df_dates = pd.read_sql_query("SELECT * FROM Dates", con).drop(columns=['index'])
    df_workout_set = pd.read_sql_query("SELECT * FROM Workout_Set", con).drop(columns=['index'])
    df_workout_volume = pd.read_sql_query("SELECT * FROM Workout_Volume", con).drop(columns=['index'])

    df_full_table = pd.merge(df_workout_set, 
                             df_workout_volume, 
                             how='left',
                             on='SetID')
    df_full_table = pd.merge(df_full_table,
                             df_dates,
                             how='left',
                             on='WorkoutID')
    return df_full_table

def get_flat_table(con):

    df_full_table = get_full_table(con)
    df_full_table = df_full_table.drop(columns=['SetID', 'WorkoutID'])
    return df_full_table.pivot_table(index=['Date', 'Weight'], 
                                     values='Reps', 
                                     columns='Workout_Name', 
                                     aggfunc='size')

def get_last_workout(workout_name, con):
    cur = con.cursor()
    query = "SELECT Workout_Volume.WorkoutID, MAX(Date) \
             FROM Workout_Volume \
             LEFT JOIN Workout_Set \
             ON Workout_Volume.SetID = Workout_Set.SetID\
             LEFT JOIN Dates \
             ON Workout_Volume.WorkoutID = Dates.WorkoutID \
             WHERE Workout_Name=:workout_name"
    cur.execute(query, {'workout_name': workout_name})
    temp = cur.fetchall()
    last_workoutID = temp[0][0]
    last_workout_date = temp[0][1]

    query = "SELECT Workout_Name, Weight, Reps \
             FROM Workout_Volume \
             LEFT JOIN Workout_Set \
             ON Workout_Volume.SetID = Workout_Set.SetID \
             WHERE WorkoutID=:workoutID \
             AND Workout_Name=:workout_name"
    cur.execute(query, {'workoutID': last_workoutID, 'workout_name': workout_name})

    return last_workout_date, cur.fetchall()

def get_workout_names(con):
    cursor = con.cursor()
    cursor.execute("SELECT DISTINCT(Workout_Name) FROM Workout_Set")
    workout_names = cursor.fetchall()
    # Flatten nested list
    return [element for sublist in workout_names for element in sublist]

if __name__ == '__main__':
    main()