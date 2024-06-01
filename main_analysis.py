"""
@author Tomasz Lasota 20 May 2024 v01

This script, main_analysis.py, along with its companion script, analysis_functions.py, is designed to analyze txt files generated 
from heater testing. The analysis process will output a CSV file that includes the minimum, maximum, and mean values, as well as 
the heating and cooling rates derived from the data.
The txt files should be generated using an instrument script that consists of a ramp up to a single heat temperature, holds for 
at least 55 sec followed by a ramp down to room temperature. 
This script is not designed to work with data files containing more than one lysis plateau.

Important Usage Instructions:
1. The main_analysis.py script should not be edited in any way.
2. This script must be run in conjunction with the analysis_functions.py script.
3. Ensure that all txt files are provided in the same working directory as these scripts.
4. The files must have an 11-digit instrument ID number included in their filenames.
5. The files must be in.txt format.
6. The files must have the set temerature in the file name in formax xxxC or xxC 

By adhering to these guidelines, you can ensure the scripts will function correctly and provide accurate analysis results.
"""



import pandas as pd
import matplotlib.pyplot as plt
from analysis_functions import *



# initilize variables
T_start = 35                                                                                                                  # sync target temperature
T_sync_start = 30                                                                                                             # sync start temperature
T_sync_end = 40                                                                                                               # sync end temperature
threshold = 0.5
min_plateau_length = 50
plot_TSC = False
results = pd.DataFrame(columns=["Instrument_ID", "Temp_condition", "Min degC", "Max degC", "Mean degC", "Heating rate (degC/s)", "Heating time (s)", "Cooling rate (deg/s)", "Cooling time (s)"])

files = get_txt_files()

for i, file in enumerate(files):

    if file:
        
        ### Load TSC data ###
        data=pd.read_csv(file, skiprows=1, skipfooter=1, 
                                    names=['ch1', 'ch2', 'main', 'ch4', 'time'], 
                                    header=None, engine='python')
        
        ### extract instrument ID and temp condition from TSC file ###
        
        ID_files = get_instrument_ID(file)
        temp = get_temp_condition(file)
        
        ### Sync data to 40 deg C ###
        try:
            t_start = get_t_start(data, channel="main", T_sync_start=T_sync_start, T_sync_end=T_sync_end, T_start=T_start)   # time at which 40 would be reached                                                                                       
            data["time"] = (data["time"] - t_start)/1000 
        except:
            print(f"Heater test failed for {file}")
            exit()

        ### find plateau indexes ###
        plateau_indexes = find_plateau_indexes(data, plateau_length=100, plateau_threshold=0.5, target_temperature=85)
        if (data["time"][plateau_indexes[-1]] - data["time"][plateau_indexes[0]]) > min_plateau_length:
            print(f"Heater test successful for {file}")
        else:
            print("Test failed due to insufficient temperature stability. Plateau achieved for the max: " + str(data["time"][plateau_indexes[-1]] - data["time"][plateau_indexes[0]]))
        
        # find min and max temperatures values for plateaus
        min_temp, max_temp, avg_temp = get_min_max_avg_temps(data, plateau_indexes)


        ### find cooling and heating phases ###
        # find cooling times and temperatures
        start_cool_time, target_cool_time, times_cooling, temps_cooling, _= find_cooling(data, plateau_indexes[-1], 40, 38, "main") 
        # check if start_cool_time is not None
        if start_cool_time is not None:
             cooling_rate, cooling_time = calculate_rate(95, 40, start_cool_time, target_cool_time)
        else:
            # calculate the rate of cooling between the last plateau value and 40 degC
            cooling_rate, cooling_time = calculate_rate(temps_cooling[plateau_indexes[-1]], 40, times_cooling[plateau_indexes[-1]], target_cool_time)
        
        # find heating times and temperatures
        start_heat_time, target_heat_time, times_heating, temps_heating = find_heating(data, plateau_indexes[0], 36, 40, "main")
        if target_heat_time is not None:
             heat_rate, heat_time = calculate_rate(40, 95, start_heat_time, target_heat_time)
        else:
            heat_rate, heat_time = calculate_rate(40, temps_heating[plateau_indexes[0]], start_heat_time, times_heating[plateau_indexes[0]])
        
        # add results to dataframe
        results.loc[i] = [ID_files, temp, min_temp, max_temp, avg_temp, heat_rate, heat_time, cooling_rate, cooling_time]

    if plot_TSC: 
            plt.figure(figsize=(12,8))
            plt.title(file)
            plt.plot(data["time"], data["main"], color="black")                                             # need to add other curves and change colour scheme
            plateau_x = data["time"][plateau_indexes]
            plateau_y = data["main"][plateau_indexes]
            plt.scatter(plateau_x, plateau_y, color = 'red', s = 20)
            plt.grid()
            plt.ylim(20,120)
            plt.xlabel("Time (s)")
            plt.ylabel("Temperature (degC)")
            plt.legend()
            plt.show()
            
results.to_csv("Heater_test_results.csv")