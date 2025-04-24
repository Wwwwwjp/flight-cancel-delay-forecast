library(tidyverse)
raw_data <- read_csv("May2024.csv")

raw_data = raw_data[1:500,]
# Re-code Day of the Week
data <-
  raw_data %>% 
  mutate(DAY_OF_WEEK = 
         case_match(DAY_OF_WEEK,
                    1 ~ "Mon",
                    2 ~ "Tue",
                    3 ~ "Wed",
                    4 ~ "Thu",
                    5 ~ "Fri",
                    6 ~ "Sat",
                    7 ~ "Sun",
                    9 ~ NA)) %>%
  filter(!is.na(DAY_OF_WEEK)) %>%
  mutate(CANCELLATION_CODE = 
           case_match(CANCELLATION_CODE,
                      NA ~ NA,
                      "A" ~ "Carrier",
                      "B" ~ "Weather",
                      "C" ~ "NAS",
                      "D" ~ "Security")) %>%
  rename(
    DAY = "DAY_OF_MONTH", WEEK = "DAY_OF_WEEK", DATE = "FL_DATE",
    ORIGIN_IATA = "ORIGIN", ORIGIN_CITY = "ORIGIN_CITY_NAME",
    DEST_IATA = "DEST", DEST_CITY = "DEST_CITY_NAME",
    MKT_AIRLINE = "MKT_UNIQUE_CARRIER",MKT_FL_NUM = "MKT_CARRIER_FL_NUM",
    SCH_DEP_TIME = "CRS_DEP_TIME",ACT_DEP_TIME ="DEP_TIME",
    SCH_ARR_TIME = "CRS_ARR_TIME",ACT_ARR_TIME ="ARR_TIME",
    SCH_DURATION = "CRS_ELAPSED_TIME",ACT_DURATION ="ACTUAL_ELAPSED_TIME")
################################################################################
# Add in additional **Origin** airport information: important to know airport type (small, medium, large)
# and its elevation
#.  We will read in information from ourairports.com (which is provided as a CSV here)
#  That dataset includes the IATA airport code, which will use a key to join the two datasets
################################################################################
ourairports <- 
  read_csv(file = "our_airports_info.csv") %>%
  filter(!is.na(iata_code))

airport_tz <- 
  read_csv(file = "airport_timezone.csv") %>% 
  select(iata_code, iana_tz)

ourairports_origin <- 
  ourairports %>% rename(ORIGIN_TYPE = "type",
                         ORIGIN_ELEV = "elevation_ft",
                         ORIGIN_IATA = "iata_code")
tz_origin <-
  airport_tz %>% rename(ORIGIN_IATA = "iata_code",
                        ORIGIN_TZ = "iana_tz")

data <-
  data %>%
  left_join(ourairports_origin, by = "ORIGIN_IATA") %>%
  left_join(tz_origin, by = "ORIGIN_IATA")

################################################################################
# Add in additional **Destination** airport information:
################################################################################

ourairports_dest <- 
  ourairports %>% 
  rename(DEST_TYPE = "type",
         DEST_ELEV = "elevation_ft",
         DEST_IATA = "iata_code")
tz_dest <-
  airport_tz %>% rename(DEST_IATA = "iata_code",
                        DEST_TZ = "iana_tz")

data <-
  data %>%
  left_join(ourairports_dest, by = "DEST_IATA") %>%
  left_join(tz_dest, by = "DEST_IATA")

################################################################################
# Function to convert times to UTC
# day: day (e.g., 1). Must be numeric.
# hour: hours (e.g., 1,13,21). Must be numeric
# min : minutes (e.g., 23,3). Must be numeric.
# iana_tz: iana timezone. Must be character
################################################################################
convertToUTC <- function(month, day, year, time, iana_tz)
{
  hour <- substring(time,1,2)
  min <- substring(time,3,4)
  tmp <- paste(month,"/",day,"/",year," ",hour,":",min,sep="")
  time_formatted =  parse_date_time(tmp,orders=c("mdY HM", "mdY"),tz=iana_tz)
  return(force_tz(with_tz(time_formatted,"UTC"),"UTC"))
}

sch_dep_utc <- rep(NA_POSIXct_, times = nrow(data))
sch_arr_utc <- rep(NA_POSIXct_, times = nrow(data))
act_dep_utc <- rep(NA_POSIXct_, times = nrow(data))
act_arr_utc <- rep(NA_POSIXct_, times = nrow(data))

for(i in 1:nrow(data)){
  # scheduled departure time in UTC
  if(i %% floor(nrow(data)/100) == 0) print(paste("Converted times for row", i, "of", nrow(data)))
  sch_dep_utc[i] <-
    convertToUTC(data$MONTH[i], data$DAY[i], data$YEAR[i], 
                 data$SCH_DEP_TIME[i], data$ORIGIN_TZ[i])

  # add scheduled duration to schedule departure to get scheduled arrival
  sch_duration_minutes <- as.numeric(data$SCH_DURATION[i])
  sch_arr_utc[i] <- 
    parse_date_time(sch_dep_utc[i],orders=c("Ymd HMS","Ymd"),tz="UTC") + 
    minutes(sch_duration_minutes)

  if(!is.na(data$DEP_DELAY[i])){
    dep_delay_minutes <- as.numeric(data$DEP_DELAY[i])
    act_dep_utc[i] <- 
      parse_date_time(sch_dep_utc[i],orders=c("Ymd HMS","Ymd"),tz="UTC") + 
      minutes(dep_delay_minutes)
  }
  
  if(!is.na(data$ARR_DELAY[i])){
    arr_delay_minutes <- as.numeric(data$ARR_DELAY[i])
    act_arr_utc[i] <-
      parse_date_time(sch_arr_utc[i],orders=c("Ymd HMS","Ymd"),tz="UTC") + 
      minutes(arr_delay_minutes)
  } 
}  
data <-
  data %>%
  mutate(SCH_DEP_TIME_UTC = sch_dep_utc,
         ACT_DEP_TIME_UTC = act_dep_utc,
         SCH_ARR_TIME_UTC = sch_arr_utc,
         ACT_ARR_TIME_UTC = act_arr_utc)

write.csv(data, file = "sample_data.csv", row.names = FALSE)
