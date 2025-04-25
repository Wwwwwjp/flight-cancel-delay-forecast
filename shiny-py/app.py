from shiny import App, ui, render, reactive
import shiny
import pandas as pd
import joblib
from datetime import datetime, timedelta
# from hms import parse as parse_hms
from weather_fetch import get_weather_features_for_user_input
import category_encoders
import xgboost
import numpy as np
import shiny.experimental as x
from pathlib import Path
import os
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_hms(timestr):
    try:
        return datetime.strptime(timestr, "%H:%M:%S").time()
    except ValueError:
        return None

# 加载机场信息
airport_info = pd.read_csv("data/airports_info_.csv")

# Load airport type information
#airport_types = pd.read_csv("type_airport.csv")
airport_types = pd.read_csv("data/type_airport.csv")


# 查找经纬度函数
def get_coords(iata_code):
    row = airport_info[airport_info['Airport'] == iata_code.upper()]
    if row.empty:
        return (None, None)
    return row.iloc[0]['Latitude'], row.iloc[0]['Longitude']

# Airport type lookup function
def get_airport_type(iata_code):
    row = airport_types[airport_types['origin'] == iata_code.upper()]
    if row.empty:
        return "large_airport"  # Default to large_airport if not found
    return row.iloc[0]['type']

# Load models with error handling
try:
    logger.info("Loading weather-based models...")
    arrival_delay_weather = joblib.load('model/pipe_arr_weather.pkl')
    departure_delay_weather = joblib.load('model/pipe_dep_weather.pkl')
    cancellation_weather = joblib.load('model/pipe_cancel_weather.pkl')
    logger.info("Weather-based models loaded successfully")
except Exception as e:
    logger.error(f"Error loading weather-based models: {str(e)}")
    raise

try:
    logger.info("Loading non-weather models...")
    arrival_delay_non_weather = joblib.load('model/pipe_arr_no_weather.pkl')
    departure_delay_non_weather = joblib.load('model/pipe_dep_no_weather.pkl')
    cancellation_non_weather = joblib.load('model/pipe_cancel_no_weather.pkl')
    logger.info("Non-weather models loaded successfully")
except Exception as e:
    logger.error(f"Error loading non-weather models: {str(e)}")
    raise

# Configure static file serving
www_dir = Path(__file__).parent / "www"
static_assets = {
    "background": "background3.jpg",
    "plane_icon": "smallplane.png"
}

app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.style("""
        /* Full-page */
        html, body {
            height: 100%;
            background-image: url('background3.jpg');
            background-size: cover;
            background-attachment: fixed;
            background-position: center center;
            background-repeat: no-repeat;
            color: white;
        }

        /* Frosted-glass box */
        .box-style {
            width: 750px;
            padding: 25px;
            border-radius: 20px;
            backdrop-filter: blur(12px);
            background-color: rgba(0, 0, 0, 0.4);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
            color: white;
        }

        /* Title spacing */
        .title-section {
            text-align: center;
            margin-bottom: 40px;
        }
        .title-section h1 {
            font-size: 70px;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 6px rgba(0,0,0,0.6);
            margin: 0;
        }
        .title-section h4 {
            font-size: 24px;
            font-weight: normal;
            color: white;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
            margin: 10px 0 0 0;
        }

        /* Input rows */
        .input-row {
            margin-bottom: 15px;
        }
        .input-row > div {
            display: flex;
            gap: 15px;
        }
        .input-group {
            flex: 1;
        }
        .input-group label {
            display: block;
            margin-bottom: 5px;
            color: #fff;
            font-size: 14px;
        }
        input[type="text"], input[type="date"] {
            width: 100%;
            padding: 8px 12px;
            border: none;
            border-radius: 4px;
            background-color: rgba(255, 255, 255, 0.9);
            color: #333;
        }
        input[type="text"]::placeholder {
            color: #666;
        }

        /* Predict button */
        .predict-btn-wrapper {
            text-align: center;
            margin-top: 20px;
        }
        .predict-btn {
            background-color: #dc3545;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .predict-btn:hover {
            background-color: #c82333;
        }

        /* Output text */
        .output-text {
            background-color: rgba(0, 0, 0, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            white-space: pre-wrap;
            color: white !important;
        }
        
        /* Ensure text output is always white */
        .output-text * {
            color: white !important;
        }
        #prediction_output {
            color: white !important;
        }
        
        /* Additional style for Shiny text output */
        pre.shiny-text-output {
            color: white !important;
            background-color: transparent !important;
            border: none !important;
            font-family: inherit !important;
        }

        /* Small plane icon */
        .plane-icon {
            position: fixed;
            top: 20px;
            left: 20px;
            width: 60px;
            height: 60px;
            opacity: 0.8;
            transition: opacity 0.3s;
        }
        .plane-icon:hover {
            opacity: 1;
        }

        /* Travel Advice button */
        .suggest-btn {
            position: fixed;
            top: 20px;
            left: 20px;
            display: flex;
            align-items: center;
            gap: 3px;
            background-color: transparent;
            border: none;
            color: white;
            font-weight: bold;
            cursor: pointer;
            text-decoration: none;
            transition: opacity 0.3s;
        }
        .suggest-btn:hover {
            opacity: 0.8;
        }
        .suggest-btn img {
            width: 60px;
            height: 60px;
            margin-right: 3px;
        }

        /* Advice page styles */
        .advice-content {
            color: white;
            line-height: 1.6;
            margin: 20px 0;
        }
        .advice-content h3 {
            color: #ffd700;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .advice-content ul {
            margin: 10px 0;
            padding-left: 20px;
        }
        .advice-content li {
            margin: 8px 0;
        }
        """)
    ),
    
    # Page state
    ui.output_text("page"),
    
    # Home page
    ui.panel_conditional(
        "output.page == 'home'",
        # Travel Advice Button with plane icon
        ui.panel_absolute(
            {"top": 20, "left": 20, "fixed": True, "draggable": False},
            ui.input_action_button(
                "suggest_btn",
                ui.tags.div(
                    ui.tags.img(src="smallplane.png", style="width: 60px; height: 60px; margin-right: 3px;"),
                    "Travel Advice"
                ),
                style="background-color: transparent; border: none; color: white; font-weight: bold;"
            )
        ),
        # Main Content
        ui.div(
            {"style": "height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center;"},
            ui.div(
                {"class": "title-section"},
                ui.h1("SkyCast"),
                ui.h4("Predict your flight. Manage your life.")
            ),
            ui.div(
                {"class": "box-style"},
                ui.div(
                    {"class": "input-row"},
                    ui.div(
                        {},
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Departure Airport*"),
                            ui.input_text("origin", None, placeholder="JFK", value="JFK")
                        ),
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Destination Airport*"),
                            ui.input_text("dest", None, placeholder="LAX", value="LAX")
                        )
                    )
                ),
                ui.div(
                    {"class": "input-row"},
                    ui.div(
                        {},
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Flight Date*"),
                            ui.input_date("flight_date", None, value=datetime.today())
                        ),
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Carrier*"),
                            ui.input_text("carrier", None, placeholder="AA", value="AA")
                        )
                    )
                ),
                ui.div(
                    {"class": "input-row"},
                    ui.div(
                        {},
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Departure Time*"),
                            ui.input_text("dep_time", None, placeholder="08:00", value="08:00")
                        ),
                        ui.div(
                            {"class": "input-group"},
                            ui.tags.label("Arrival Time*"),
                            ui.input_text("arr_time", None, placeholder="11:30", value="11:30")
                        )
                    )
                ),
                ui.div(
                    {"class": "predict-btn-wrapper"},
                    ui.input_action_button("predict_btn", "🔍 Predict", class_="predict-btn")
                ),
                ui.div(
                    {"class": "output-text"},
                    ui.output_text_verbatim("prediction_output")
                )
            )
        )
    ),
    
    # Advice page
    ui.panel_conditional(
        "output.page == 'advice'",
        ui.div(
            {"class": "box-style", "style": "margin: 100px auto; max-width: 800px;"},
            ui.h2("✈️ Travel Advice", style="font-weight: bold; color: white; text-align: center; margin-bottom: 20px;"),
            ui.div(
                {"class": "advice-content"},
                ui.tags.ul(
                    ui.tags.li("Preferred Airlines: Delta Air Lines (DL), United Airlines (UA), and American Airlines (AA) generally offer more reliable service and are recommended for a smoother travel experience."),
                    ui.tags.li("Best Travel Days: To reduce the risk of flight delays and cancelations, consider avoiding travel on Mondays, which tend to experience higher traffic and operational disruptions."),
                    ui.tags.li("Monthly Advisory – January: In January, flights operated by United Airlines (UA) have shown a higher likelihood of cancelations and delays. Choosing Delta or American Airlines during this month may offer a more dependable option."),
                    ui.tags.li("Airline Reliability: Delta and American Airlines consistently demonstrate lower cancelation rates and are preferred choices, particularly for time-sensitive travel. Conversely, Southwest and Alaska Airlines have shown less reliability in this regard and may be best avoided if schedule certainty is important."),
                    ui.tags.li("Holiday Travel Guidance: Try to avoid scheduling flights within two days before or five days after major holidays. These peak travel windows often see elevated levels of congestion, leading to increased chances of delays and cancelations."),
                    ui.tags.li("Tight Schedule Tip: For travelers with tight connections or critical timing, Delta and American Airlines are especially recommended due to their more consistent on-time performance.")
                )
            ),
            ui.div(
                {"style": "text-align: center; margin-top: 30px;"},
                ui.input_action_button("back_btn", "Return", class_="btn btn-secondary")
            )
        )
    )
)

# 服务器逻辑
def server(input, output, session):
    # Add current page reactive value
    current_page = reactive.Value("home")
    prediction_result = reactive.Value("")
    
    @output
    @render.text
    def page():
        return current_page.get()

    @reactive.Effect
    @reactive.event(input.suggest_btn)
    def _():
        current_page.set("advice")

    @reactive.Effect
    @reactive.event(input.back_btn)
    def _():
        current_page.set("home")

    @output
    @render.text
    def prediction_output():
        return prediction_result.get()

    @reactive.Effect
    @reactive.event(input.predict_btn)
    def _():
        # 获取用户输入
        origin = input.origin() or "JFK"
        dest = input.dest() or "LAX"
        flight_date = input.flight_date()
        carrier = input.carrier() or "AA"
        dep_time = input.dep_time() or "08:00"
        arr_time = input.arr_time() or "11:30"

        # Process times
        dep_time_obj = parse_hms(f"{dep_time}:00" if len(dep_time) == 5 else dep_time)
        arr_time_obj = parse_hms(f"{arr_time}:00" if len(arr_time) == 5 else arr_time)
        
        if not dep_time_obj or not arr_time_obj:
            prediction_result.set("❌ Invalid time format. Please use HH:MM format (e.g., 08:00)")
            return

        dep_time_min = dep_time_obj.hour * 60 + dep_time_obj.minute
        arr_time_min = arr_time_obj.hour * 60 + arr_time_obj.minute
        sch_duration = arr_time_min - dep_time_min
        if sch_duration < 0:
            sch_duration += 1440

        # Calculate date difference
        current_date = datetime.now().date()
        days_difference = (flight_date - current_date).days

        # 获取经纬度
        lat_o, lon_o = get_coords(origin)
        lat_d, lon_d = get_coords(dest)

        if None in (lat_o, lon_o, lat_d, lon_d):
            prediction_result.set("❌ Invalid airport code. Please check your airport codes.")
            return

        # Get airport types from the CSV file
        origin_type = get_airport_type(origin)
        dest_type = get_airport_type(dest)

        # Base input data without weather features
        input_data = {
            'DATE': 0,
            'CANCELLATION_CODE': 0,
            'DEP_DELAY': 0,
            'DEP_DELAY_NEW': 0,
            'ARR_DELAY': 0,
            'CARRIER_DELAY': 0,
            'WEATHER_DELAY': 0,
            'NAS_DELAY': 0,
            'SECURITY_DELAY': 0,
            'LATE_AIRCRAFT_DELAY': 0,
            "WEEK": flight_date.strftime("%a"),
            "MKT_AIRLINE": carrier.upper(),
            "ORIGIN_IATA": origin.upper(),
            "DEST_IATA": dest.upper(),
            "SCH_DEP_TIME": dep_time_min,
            "SCH_ARR_TIME": arr_time_min,
            "SCH_DURATION": sch_duration,
            "DISTANCE": 0,
            "ORIGIN_TYPE": origin_type,  # Use looked-up origin airport type
            "ORIGIN_ELEV": 0,
            "DEST_TYPE": dest_type,  # Use looked-up destination airport type
            "DEST_ELEV": 0,
            "IS_WEEKEND": int(flight_date.weekday() >= 5),
            "IS_HOLIDAY": 0,
            "DEP_HOUR": dep_time_obj.hour,
            "ARR_HOUR": arr_time_obj.hour,
        }

        try:
            input_df = pd.DataFrame([input_data])
            
            if days_difference <= 7:  # Within a week
                # Try to get weather info
                weather_info = get_weather_features_for_user_input(
                    lat_o, lon_o, lat_d, lon_d, flight_date.strftime("%Y-%m-%d")
                )
                
                if weather_info is not None:
                    # Use weather model if we have weather data
                    input_data.update(weather_info)
                    input_df = pd.DataFrame([input_data])
                    
                    # Get all predictions using weather models
                    cancel_prob = cancellation_weather.predict_proba(input_df)[0,1]
                    arr_delay = arrival_delay_weather.predict(input_df)[0]
                    dep_delay = departure_delay_weather.predict(input_df)[0]
                    
                    result = f"""✈️ Prediction Results (Weather-based Model):

🔴 Cancellation Probability: {cancel_prob:.1%}
🟠 Expected Departure Delay: {dep_delay:.1f} minutes
🟡 Expected Arrival Delay: {arr_delay:.1f} minutes"""
                    prediction_result.set(result)
                    return
                
            # If no weather data or beyond 7 days, use non-weather model
            cancel_prob = cancellation_non_weather.predict_proba(input_df)[0,1]
            arr_delay = arrival_delay_non_weather.predict(input_df)[0]
            dep_delay = departure_delay_non_weather.predict(input_df)[0]
            
            model_type = "Historical Data Model"
            result = f"""✈️ Prediction Results ({model_type}):

🔴 Cancellation Probability: {cancel_prob:.1%}
🟠 Expected Departure Delay: {dep_delay:.1f} minutes
🟡 Expected Arrival Delay: {arr_delay:.1f} minutes"""
            prediction_result.set(result)
            
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            prediction_result.set(f"❌ Prediction failed: {str(e)}")

# Initialize the app
app = App(app_ui, server, static_assets=www_dir)

if __name__ == "__main__":
    import shiny
    shiny.run_app(app)