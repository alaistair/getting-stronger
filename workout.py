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

    # Get workout names
    cursor.execute("SELECT DISTINCT(Workout_Name) FROM Workout_Set")
    workout_names = cursor.fetchall()
    # Flatten nested list
    workout_names = [element for sublist in workout_names for element in sublist]
    col1, col2, col3, = st.columns((1,1,1))

    workout_radio = col1.radio('', workout_names)
    workout_name = workout_radio
    last_workout_str, df_last_workout = get_last_workout(workout_name, con)
    last_workout_date = datetime.datetime.strptime(last_workout_str, "%Y-%m-%d %H:%M:%S")
    last_workout_date = last_workout_date.date()

    col2.write("## " + workout_name)
    col2.write("Latest workout")
    col2.write(last_workout_date)
    col2.write("Weight")
    col2.write(df_last_workout[0][1])
    col2.write("Reps")
    col2.write(df_last_workout[0][2])
    col2.write("Sets")

    col3.write("### .")
    weight = col3.number_input("Weight", min_value=0, value=int(df_last_workout[0][1]), key=workout_name[0] + 'weight')
    col3.number_input('Reps', min_value=0, value=int(df_last_workout[0][2]), key=workout_name[0])
    col3.button("Add set")


    with st.expander("See all workouts"):
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
            last_workout_date, df_last_workout = get_last_workout(workout_name, con)
            col1_workout.write(workout_name)
            col2_latest.write(last_workout_date)
            col3_weight.write(df_last_workout[0][1])
            col4_reps.write(df_last_workout[0][2])

    with st.expander("See history"):
        st.write(get_flat_table(con))




    con.close()

    st.write("## Barbell weight allocation")
    weight_to_lift = st.number_input("Weight to lift", min_value=0.0, value=float(weight))
    weight_bar = st.number_input("Weight of bar", min_value=0, value=16)
    weight_set_full = {20.0: 2, 10.0: 2, 5.0: 2, 2.5: 2, 1.0: 2, 0.75: 2, 0.5: 2, 0.25:2}
    weight_set_to_use_full, weight_unallocated = calculate_barbell_weights(weight_to_lift, weight_set_full, weight_bar)

    for weight, number in weight_set_to_use_full.items():
        if number > 0:
            st.write(f"{str(weight)} weight {str(number)}")

    if weight_unallocated != 0:
        st.write(f"Unallocated {str(weight_unallocated)}")





    #df_weights = weight_allocate_test(weight_set_full, weight_bar)
    #st.dataframe(df_weights.style.apply(highlight_unallocated, axis=1))

def calculate_barbell_weights(weight_to_lift, weight_set_full, weight_bar):
   
    weight_to_allocate = weight_to_lift - weight_bar
    if weight_to_allocate < 0:
        return {}, weight_to_allocate

    # Halve weight set because of two sides for barbell
    weight_set_half = {key: value//2 for key, value in weight_set_full.items()}
    weight_set_to_use_half, weight_unallocated = allocate_weights(weight_to_allocate/2, weight_set_half)

    # Double weight set for total weight
    return {key: value * 2 for key, value in weight_set_to_use_half.items()}, weight_unallocated * 2

def allocate_weights(weight_to_allocate, weight_set_full):

    weight_set = {}
    for weight, number in sorted(weight_set_full.items(), reverse=True):
        weight_set[weight] = 0

        if (weight_to_allocate >= weight) and number > 0:
            weight_set[weight] = min((weight_to_allocate // weight), number)
            weight_to_allocate -= min((weight_to_allocate // weight), number) * weight

    weight_unallocated = weight_to_allocate
    return weight_set, weight_unallocated

def total_weight(weight_set, weight_bar):
    total_weight = weight_bar
    for weight, number in weight_set.items():
        total_weight += weight * number
    return total_weight

def weight_allocate_test(weight_set_full, weight_bar):

    df_weights = pd.DataFrame()
    for i in range(15, 100):
        weight_set, weight_unallocated = calculate_barbell_weights(i, weight_set_full, weight_bar)
        weight_set['Barbell'] = weight_bar
        weight_set['Total weight'] = i
        weight_set['Unallocated'] = weight_unallocated

        df_weights = df_weights.append(weight_set, ignore_index=True)
    return df_weights

def highlight_unallocated(s):
    return ['background-color: red']*len(s) if s.Unallocated else ['background-color: white']*len(s)

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
