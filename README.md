# Football Prediction System (Poisson Model + Data Pipeline)

This is an End-To-End project from data collection to match predictions. Using a variety of tools as **Python** (for data collection & validation), **MySQL** to get insights from the data & **Streamlit** for interactive visualization.

## Features

- Automated detailed Data Collection from Football-Data.org
- Data Cleaning & Validation pipeline
- Connect the data to an MySQL database
- MySQL relational database desing (transform the CSV to relation schema)
- SQL queries, views for team performance analysis
- Poisson Model for match predictions
- Automated process for next's matchday matches collection and match predictions.
- Full Time & Half Time predictions.
- Over/Under goal probabilities.
- Interactive Streamlit dashboard.

---
## Project Structure

Football-Prediction-System/
       
    ├── data/
        ├── matches.csv
        ├── predictions_all.csv
    ├── sql/
        ├── schema.sql
        ├── views.sql
    |    
    ├── data_collect.py        
    ├── data_validation.py     
    ├── load_csv_to_sql.py     
    ├── ht_ft_predict.py       
    ├── full_bet_app.py 
    |       
    ├── requirements.txt       
    ├── README.md              
    └── .gitignore

---
## Database Desing

The system uses a normalized MySQL schema:

- 'teams_c' -> teams information
- 'leagues_c' -> leagues data
- 'seasons_c' -> season tracking
- 'matches_info' -> detailed matches data
- 'matches' -> final match records

SQL views are used to compute aggregated statistics for modeling.

---

## Model 

The prediction engine uses a **Poisson distribution model** to estimate:

- Expected Goals for each Team
- Match Result Probabilites
    - Home Win
    - Draw
    - Away Win
- Over/Under goals (2.5 FT, 0.5 HT)

---

## How to Run

1. Data Collection

`Bash
`python data_collect.py

2. Data Cleaning & Validation

`Bash
`python data_validation.py

3. Load the data to MySQL

`Bash
`python load_csv_to_sql.py

4. Generate Predictions

`Bash
`python ht_ft_predict.py

5. Run Streamlit App

`Bash
`python -m streamlit run full_predict_app.py

---
## Live Demo
This application is **live** and continiously updated:
[**Live App**](https://football-prediction-system.streamlit.app)

---

## Technologies Used

- Python
- Pandas/Numpy
- SQL (MySQL)
- Spicy (Poisson Model)
- Streamlit

---

## Security

Sensitive Information (API keys, databse credentials) is stored in inviroment variables and excluded via .gitignore.

---

## Data Source

The dataset used in this project was collected from Football-Data Org. Please make sure to comply with their terms and conditions when using data.

---

## License

This project is licensed under the MIT License.

---








