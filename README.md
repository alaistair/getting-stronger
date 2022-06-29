Tracking strength training with a Streamlit frontend and SQLite backend.


# Data model



| Dates | datatype | example |
| --- | --- | --- |
| Date | datetime | 2020-08-16T00:00:00 |
| WorkoutID | int | 1 |

| Workout_Set | datatype | example |
| --- | --- | --- |
| SetID | int | 1 |
| Workout_Name | str | Deadlift |
| Weight | int | 10 |
| Reps | int | 3 |

| Workout_Volume | datatype | example |
| --- | --- | --- |
| WorkoutID | int | 1 |
| SetID | int | 1 |


