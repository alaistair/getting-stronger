import altair as alt
import pandas as pd
import numpy as np
import streamlit as st
import os
import re
import sqlite3
import datetime
import json

def main():
    st.set_page_config(layout="wide")

    # Load silver SQLite database
    PATH = '/Users/alaistairchan/Dropbox/Workout/data/silver/'
    con = sqlite3.connect(f"{PATH}silver.sqlite")
    cursor = con.cursor()

    st.write(get_flat_table(con))

    # Get workout names
    cursor.execute("SELECT DISTINCT(Workout_Name) FROM Workout_Set")
    workout_names = cursor.fetchall()
    df_workout_names = pd.DataFrame(workout_names)

    col1, col2, col3, = st.columns((1,1,1))
    col1.write("#### Workout")
    col2.write("#### Last")
    col3.write("#### Add")

    col1, col2, col3, col4, col5, col6 = st.columns((1,1,1,1,1,1))
    col2.write("#### Latest")
    col3.write("#### Weight")
    col4.write("#### Reps")
    col5.write("#### Weight")
    col6.write("#### Reps")
    col1_workout, col2_latest, col3_weight, col4_reps, col5_weight_add, col6_x = st.columns((1,1,1,1,1,1))



    for workout_name in workout_names:
        last_workout_date, df_last_workout = get_last_workout(workout_name[0], con)
        col1_workout.write(workout_name[0])
        col2_latest.write(last_workout_date)
        col3_weight.write(df_last_workout[0][1])
        col4_reps.write(df_last_workout[0][2])
        try:
            col5_weight_add.number_input('', min_value=0, value=int(df_last_workout[0][1]), key=workout_name[0])
        except Exception:
            pass
    con.close()



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

if __name__ == '__main__':
    main()
    padding = 3
    st.markdown(f""" <style>
        .reportview-container .main .block-container{{
            padding-top: {padding}rem;
            padding-right: {padding}rem;
            padding-left: {padding}rem;
            padding-bottom: {padding}rem;
        }} </style> """, unsafe_allow_html=True)