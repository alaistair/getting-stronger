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

    #st.write(get_full_table(con))

    # Get workout names
    cursor.execute("SELECT DISTINCT(Workout_Name) FROM Workout_Set")
    workout_names = cursor.fetchall()
    df_workout_names = pd.DataFrame(workout_names)
    st.write(workout_names[0][0])


    col1, col2, col3, col4, col5, col6 = st.columns((1,1,1,1,1,1))
    col1.write("Workout")
    col2.write("Last workout")
    col3.write("Date")
    col5.write("Weight")
    col1_workout, col2_last, col3_date, col4_x, col5_x, col6_x = st.columns((1,1,1,1,1,1))



    for workout_name in workout_names:
        col1_workout.write(workout_name[0])
        df_last_workout = get_last_workout(workout_name[0], con)
        st.write(df_last_workout)

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
    last_workoutID = cur.fetchall()[0][0]

    query = "SELECT Workout_Name, Weight, Reps \
             FROM Workout_Volume \
             LEFT JOIN Workout_Set \
             ON Workout_Volume.SetID = Workout_Set.SetID \
             WHERE WorkoutID=:workoutID \
             AND Workout_Name=:workout_name"
    cur.execute(query, {'workoutID': last_workoutID, 'workout_name': workout_name})

    return cur.fetchall()

if __name__ == '__main__':
    main()