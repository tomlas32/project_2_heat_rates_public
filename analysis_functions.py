import os
import numpy as np
import re


def get_t_start(df, channel, T_sync_start, T_sync_end, T_start):
    t_start = []
    i_sync_start = next(x for x, val in enumerate(df[channel])
                                if val > T_sync_start)
    i_sync_end = next(x for x, val in enumerate(df[channel])
                                if val > T_sync_end)
    times = df["time"][i_sync_start:i_sync_end]                                                             # times with values ranging from 35 to 45
    temps = df[channel][i_sync_start:i_sync_end]                                                            # corresponding temperature values for channel 1
    
    t_start.append(np.interp(T_start,temps,times))                                                          # this finds the time at which 40 deg C is reached (interpolation needed as the exact 40 degC might
    return t_start    

# function for extracting indexes and data for each temperature hold 
def find_plateau_indexes(df, plateau_length, plateau_threshold, target_temperature):
    plateau_indexes = []
    print("############Commencing search for plateau indices################")
    # Calculate rolling mean with a window size equal to plateau_length
    rolling_mean = df["main"].rolling(window=plateau_length, min_periods=1).mean()
    # Find indices where the difference between rolling mean and current value is within plateau_threshold
    plateau_indices = df[(abs(rolling_mean - df["main"]) <= plateau_threshold) & (df["main"] > target_temperature)].index
    plateau_indexes = plateau_indices.tolist()
    
    return plateau_indexes

def find_cooling(df, start_index, target_temperature, end_temp, channel):
    i_end = (df[channel].iloc[start_index:] < end_temp).idxmax()
    times_cooling = df["time"][start_index:i_end+1]                                                         # times with values ranging from 35 to 45
    temps_cooling = df[channel][start_index:i_end+1]  
    times_cooling_rev = times_cooling[::-1]                                                                 # required for interp which assumes increasing values
    temps_cooling_rev = temps_cooling[::-1]
    time_target = np.interp(target_temperature,temps_cooling_rev,times_cooling_rev) 
    if df[channel].iloc[start_index] > 95:                                                                  # for temp values above 95C at the last plateau index
        start_time = np.interp(95,temps_cooling_rev,times_cooling_rev)                                      # time at which 95 was reached. Start of cooling for the acceptance criteria (95-40)
    else:
        start_time = None
    return start_time, time_target, times_cooling, temps_cooling, i_end

def calculate_rate(T_start, T_end, time_start, time_end):
    rate = abs((T_end - T_start)/(time_end - time_start))
    time = (time_end - time_start)
    return rate, time

def find_heating(df, end_index, start_temp, target_start_temp, channel):
    start_index = (df[channel].iloc[:end_index] >= start_temp).idxmax()
    times_heating = df["time"][start_index:end_index+1]                                                     # times with values ranging from start_temp to the first temp of the plateau
    temps_heating = df[channel][start_index:end_index+1]                                                    # temps with values ranging from start_temp to the first temp of the plateau
    start_time = np.interp(target_start_temp,temps_heating,times_heating)                                   # time at which target_start_temp was reached
    if df[channel].iloc[end_index] > 95:                                                                              # for readings over 95C. Criteria is 40 to 95C
        target_time = np.interp(95,temps_heating,times_heating)                                             # time at which 95C was reached
    else:
        target_time = None                                                                                  # if temp is less than 95 target time is not needed

    return start_time, target_time, times_heating, temps_heating

# function for loading text files from the current directory
def get_txt_files():
    dir = os.path.dirname(os.path.realpath(__file__))
    list_file_names = [file for file in os.listdir(dir) if file.endswith(".txt")]

    return list_file_names

# function for extracting instrument ID from the file name
def get_instrument_ID(file_name):
    pattern = r"\d{11}"
    match = re.search(pattern, file_name)
    instrument_ID = ""
    if match:
        instrument_ID = match.group()
    else:
        print("Instrument ID not found in the file name: " + file_name)
    
    return instrument_ID

# get run condition from file name
def get_temp_condition(file_name):
    pattern = r"\d{2,3}C"
    temp_condition = ""
    match = re.search(pattern, file_name)
    if match:
        temp_condition = match.group()
    else:
        print("No condition in the txt file")
    
    return temp_condition

# fucntion for extracting min/max temperature values from plateau phase
def get_min_max_avg_temps(df, plateau_indexes):
    min_temp = df["main"].iloc[plateau_indexes].min()
    max_temp = df["main"].iloc[plateau_indexes].max()
    avg_temp = df["main"].iloc[plateau_indexes].mean()

    return min_temp, max_temp, avg_temp
