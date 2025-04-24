# Flight Delay & Cancellation Predictor

This project was developed for STAT 628 at the University of Wisconsin–Madison. We use historical flight data and weather data to build predictive models for U.S. domestic flights. The Shiny application allows users to input flight details and receive predictions about:

- Whether their flight will be cancelled  
- Whether their flight will depart or arrive on time  
- If delayed, the expected delay time  
- Uncertainties associated with each prediction  

## Project Scope

Our analysis includes all U.S. domestic flights from **May to August 2024**, covering all airlines and airports.

## Features

- Predict flight cancellation, departure delay, and arrival delay  
- Weather features (snowfall, rainfall, temperature, wind speed) are used when available  
- The model automatically excludes weather features when the prediction is more than 7 days in advance  
- Built using R, Python and Shiny  

## Folder Structure

- `code/` — all scripts and code used in the project  
- `data/` — preprocessed and sample datasets used in modeling  
- `docs/` — documents such as the executive summary and technical report  

Due to file size limitations on GitHub, **full datasets are stored on Google Drive**:
👉 [Access full data here](https://drive.google.com/drive/folders/1aXDaMYt9esGaeYZpWL6yRjgCLvBKvA1F?usp=drive_link)

## Team Members

- Jiapeng Wang  
- Yifan Chen  
- Zhixing Liu  

## Acknowledgements

Flight data was provided by the U.S. Department of Transportation. Weather data was obtained via an external API.

---

Feel free to clone the repository and explore the app and models!
