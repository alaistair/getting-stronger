import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
import os
import re
import sqlite3
import datetime
import json


def main():
    st.set_page_config(layout="wide")
    
    # Load silver SQLite database
    PATH = './data/silver/'
    con = sqlite3.connect(f"{PATH}silver.sqlite")

    workout_names = get_workout_names(con)
    col1, _, col2 = st.columns((1, 0.2, 1))

    with st.sidebar:
        st.write('# Select a workout')
        workout_name = st.radio('', workout_names)
        st.button("Add new")

    last_workout_str, df_last_workout = get_last_workout(workout_name, con)
    last_workout_date = datetime.datetime.strptime(last_workout_str, "%Y-%m-%d %H:%M:%S")
    last_workout_date = last_workout_date.date()

    col1.write("# " + workout_name.replace("_", " "))
    col1.write("Latest workout")
 
    col1.write(last_workout_date)
    weight_to_lift = col1.number_input("Weight", min_value=0, value=int(df_last_workout[0][1]), key=workout_name[0] + 'weight')
    reps = col1.number_input('Reps', min_value=0, value=int(df_last_workout[0][2]), key=workout_name[0])
    col1.button("Add set")
    col1.button("Reset to previous workout")


    barbell_weight_allocation = col2.empty()
    barbell_weight_edit = col2.empty()
    weight_set_full = {20.0: 2, 10.0: 2, 5.0: 2, 2.5: 2, 1.0: 2, 0.75: 2, 0.5: 2, 0.25:2}

    with barbell_weight_edit.expander("Edit weight set"):
        weight_bar = st.number_input("Weight of bar", min_value=0, value=16)
        st.write("###### Plates")
        for weight, number in weight_set_full.items():
            number = st.number_input(str(weight)+" kg", min_value=0, value=number)

    weight_set_to_use_full, weight_unallocated = calculate_barbell_weights(weight_to_lift, weight_set_full, weight_bar)
    df_barbell_weight_allocation = show_barbell_weight_allocation(weight_set_to_use_full)


    if weight_unallocated != 0:
        col2.write(f"Unallocated {str(weight_unallocated)}")



    chart = alt.Chart(df_barbell_weight_allocation).mark_bar().encode(
        x=alt.X('Plate:N', sort=df_barbell_weight_allocation['Plate'].to_list(), axis=alt.Axis(labelAngle=0), title='Barbell weight allocation'),
        y=alt.Y('Weight:Q', axis=None),
        tooltip=['Weight']
    ).configure_axis(
        grid=False
    ).configure_view(
        strokeWidth=0
    )


    barbell_weight_allocation.altair_chart(chart, use_container_width=True)


    con.close()


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

        df_weights = pd.concat([df_weights, weight_set], ignore_index=True)
    return df_weights

def highlight_unallocated(s):
    return ['background-color: red']*len(s) if s.Unallocated else ['background-color: white']*len(s)

def get_last_workout(workout_name, con):
    cur = con.cursor()

    # Get last date of particular workout
    query = "SELECT Dates.WorkoutID, MAX(Date) \
             FROM Workout_Set \
             LEFT JOIN Dates \
             ON Workout_Set.SetID = Dates.SetID \
             WHERE Workout_Name=:workout_name"

    cur.execute(query, {'workout_name': workout_name})
    temp = cur.fetchall()
    last_workoutID = temp[0][0]
    last_workout_date = temp[0][1]

    # Get details of latest workout
    query = "SELECT Workout_Name, Weight, Reps \
             FROM Workout_Set \
             LEFT JOIN Dates \
             ON Workout_Set.SetID = Dates.SetID \
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

def show_barbell_weight_allocation(weight_set_to_use_full):

    df_barbell_weight_allocation = pd.DataFrame({"Plate":[],
                                                "Weight":[]})

    # One half of barbell
    for weight, number in weight_set_to_use_full.items():
        if number > 0:
            df_temp = pd.DataFrame({"Plate":[weight],
                                    "Weight":[weight]})
            df_barbell_weight_allocation = pd.concat([df_barbell_weight_allocation, df_temp], ignore_index=True)
            
    # Other half
    df_temp = df_barbell_weight_allocation.sort_values(by=["Plate"])
    df_temp["Plate"] = -df_temp["Plate"]
    df_temp["Plate"] = df_temp["Plate"].astype(str)
    df_barbell_weight_allocation["Plate"] = df_barbell_weight_allocation["Plate"].astype(str)

    # Bar
    barbell = pd.DataFrame({"Plate":["bar"],
                            "Weight":[16]})

    df_temp = pd.concat([df_temp, barbell], ignore_index=True)
    df_barbell_weight_allocation = pd.concat([df_temp, df_barbell_weight_allocation], ignore_index=True)

    return df_barbell_weight_allocation



if __name__ == '__main__':
    main()
