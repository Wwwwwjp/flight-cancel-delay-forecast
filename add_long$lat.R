library(dplyr)

sample_data <- read_csv("sample_data.csv")
airport_info <- read_csv("airports_info_.csv")
# 第一次合并：添加出发机场的经纬度
sample_data <- sample_data %>%
  left_join(airport_info, 
            by = c("ORIGIN_IATA" = "Airport")) %>%
  rename(Latitude_origin = Latitude,
         Longitude_origin = Longitude)

# 第二次合并：添加到达机场的经纬度
sample_data <- sample_data %>%
  left_join(airport_info, 
            by = c("DEST_IATA" = "Airport")) %>%
  rename(Latitude_dest = Latitude,
         Longitude_dest = Longitude)
