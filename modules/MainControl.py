import pandas as pd
import os
from tkinter import ttk
from modules.SensorCorrection import SensorCorrection
from modules.PlotMeasurementFigures import PlotMeasurementFigures
from modules.PlotCalibrationFigures import PlotCalibrationFigures
from modules.DataProcessor import DataProcessor
from modules.SampleDataLarge import SampleDataLarge

from modules.FigureFormatting import FigureFormatting
from modules.ComsolModel import ComsolProcessor
from modules.DirectoryGenerator import DirectoryGenerator

from modules.MiscCalculations import TempDistSolver, ThermalConductivity


# Sample selection
sample_data = SampleDataLarge()
sample = sample_data.SN2
sample_name = sample['sample_name']
path = sample['path']       # This is general path to large_test
timestamps = sample['timestamps']
fignames = sample_data.fignames

# Sample thermal conductivity (dry thermal conductivity and moist thermal conductivity)
porosity = sample['sample_props']['porosity']
ks = sample['sample_props']['ks']
rhos = sample['sample_props']['rhos']
w_grav = sample['sample_props']['w_grav']

thermal = ThermalConductivity(porosity, ks, rhos, w_grav)
kdry, kmoist = thermal.calculate_thermal_conductivity()

# Initialize two zone solver
zone_solver = TempDistSolver()


# Measurement and figure directories
measurement_data_dir = '01_measurement_data\\'
measuremnet_figures_dir = '02_measurement_figures\\'

# Sample measurement data path:
sample_measurement_data_path = path + measurement_data_dir + 'Sample_' + sample_name + '\\'

# Sample measurement figures path:
sample_measurement_figures_path = path + measuremnet_figures_dir + 'Sample_' + sample_name + '\\'

# Sample measurement data subdirectoies:
measurement_data = '02_measurement_data\\'
comsol_data = '03_comsol_model\\'
calib_data = '04_calib_data\\'
figures_save = '06_figures\\'
folders = {'01_combined_plots': '01_combined_plots\\',
           '02_time_series_temperature': '02_time_series_temperature\\',
           '03_time_series_moisture': '03_time_series_moisture\\',
           '04_gradient_temperature': '04_gradient_temperature\\',
           '05_gradient_moisture': '05_gradient_moisture\\',
           '06_last_24_hours': '06_last_24_hours\\'}

save_path = sample_measurement_figures_path
comsol_path = sample_measurement_data_path + comsol_data
data_path = sample_measurement_data_path + measurement_data

# Calibration fit figures (optional):
#calibration_figures = PlotCalibrationFigures(data_path, sample)
#calibration_figures.plot_calibration_figure()


# Plot formatter
formatter = FigureFormatting()

# Column names:
temperature_columns_main = ['U1', 'U2', 'U3', 'U4', 'U5', 'U6',
                            'R1', 'R2', 'R3', 'R4', 'R5', 'R6',
                            'D1', 'D2', 'D3', 'D4', 'D5', 'D6']
temperature_columns_moist = ['U1', 'U2', 'U3', 'U4',
                            'R1', 'R2', 'R3', 'R4',
                            'D1', 'D2', 'D3', 'D4']
temperature_columns_ext = ['X1', 'X2', 'X3', 'K1', 'K2', 'K3']
temperature_columns = temperature_columns_main + temperature_columns_ext
moisture_columns = ['MS1', 'MS2', 'MS3', 'MS4', 'MS5', 'MS6', 'MS7', 'MS8', 'MS9', 'MS10', 'MS11', 'MS12']
power_column = ['power']
columns = temperature_columns + moisture_columns + power_column

# Setting file path:
df = pd.DataFrame(columns=columns)
for file in os.listdir(sample_measurement_data_path + measurement_data):
    if file.endswith('csv'):
        df_loc = pd.read_csv(sample_measurement_data_path + measurement_data + file, index_col=0, names=columns)
        df = pd.concat([df, df_loc])
    else:
        pass

# Measurement corrections:
def corrector_func():
    corrector = SensorCorrection(sample_measurement_data_path + calib_data)
    for name in temperature_columns:
        df[name] = df[name].apply(lambda mes_val: corrector.tempertaure_sensor_correction(name, mes_val))
    for temp_name, moist_name in zip(temperature_columns_moist, moisture_columns):
        df[moist_name] = df.apply(lambda line: corrector.moisture_sensor_correction(temp_name,
                                                                                    moist_name,
                                                                                    line[temp_name],
                                                                                    line[moist_name]), axis=1)
#corrector_func()

# Plot figures
"""
Options to select from:
- plot_all_measurements()   -> plots a 4 row, 3 column figure
- plot_temperature_series()   -> plots temperature series separately
- plot_moisture_series()   -> plots separately moisture figures series
- plot_temperature_gradient()   -> plots temperature gradient separately
- plot_moisture_gradient()   -> plots separately moisture figure gradient
"""

df.index = pd.to_datetime(df.index)

# Execute data deletion (this deletes flawed data)
data_processor = DataProcessor(sample)
data_processor.delete_flawed_data(df)

# Generating dfs from comsol solutions
#comsol_processor = ComsolProcessor(sample, comsol_path)
#comsol_dfs = comsol_processor.generate_comsol_df()
comsol_dfs = []

# Directory generator:
directory_generator = DirectoryGenerator(sample)

class PlottingOptions:
    def __init__(self):
        self.plot_figures = PlotMeasurementFigures(df, timestamps, fignames, save_path, comsol_path, sample)
        self.formatter = FigureFormatting()

    def all_combined_plot(self, xscale):
        self.plot_figures.plot_all_measurements(folder=folders['01_combined_plots'],
                                                formatter=formatter.std_paper_4x3_full_width,
                                                xscale=xscale)

    def temperature_series_separate(self):
        self.plot_figures.plot_temperature_series(folder=folders['02_time_series_temperature'],
                                                  formatter=formatter.std_paper_1x1_full_width)
        self.plot_figures.plot_temperature_series(folder=folders['02_time_series_temperature'],
                                                  formatter=formatter.std_paper_1x1_full_width,
                                                  xaxis_type='datetime')

    def temperature_gradient_separate(self, xscale):
        self.plot_figures.plot_temperature_gradient(folder=folders['04_gradient_temperature'],
                                                    formatter=formatter.std_paper_1x1_partial_width,
                                                    xscale=xscale)

    def moisture_series_separate(self):
        self.plot_figures.plot_moisture_series(folder=folders['03_time_series_moisture'],
                                               formatter=formatter.std_paper_1x1_full_width)
        self.plot_figures.plot_moisture_series(folder=folders['03_time_series_moisture'],
                                               formatter=formatter.std_paper_1x1_full_width,
                                               xaxis_type='datetime')

    def moisture_gradient_separate(self, xscale):
        self.plot_figures.plot_moisture_gradient(folder=folders['05_gradient_moisture'],
                                            formatter=formatter.std_paper_1x1_partial_width,
                                                 xscale=xscale)

    def temperature_series_combined(self):
        self.plot_figures.plot_all_temperature_series(folder=folders['01_combined_plots'],
                                                      formatter=formatter.std_paper_3x1_full_width)
        self.plot_figures.plot_all_temperature_series(folder=folders['01_combined_plots'],
                                                      formatter=formatter.std_paper_3x1_full_width,
                                                      xaxis_type='datetime')

    def temperature_gradient_combined(self, xscale):
        self.plot_figures.plot_all_temperature_gradients(folder=folders['01_combined_plots'],
                                                         formatter=formatter.std_paper_3x1_partial_width,
                                                         xscale=xscale)

    def moisture_series_combined(self):
        self.plot_figures.plot_all_moisture_series(folder=folders['01_combined_plots'],
                                                   formatter=formatter.std_paper_3x1_full_width)
        self.plot_figures.plot_all_moisture_series(folder=folders['01_combined_plots'],
                                                   formatter=formatter.std_paper_3x1_full_width,
                                                   xaxis_type='datetime')

    def moisture_gradient_combined(self, xscale):
        self.plot_figures.plot_all_moisture_gradients(folder=folders['01_combined_plots'],
                                                      formatter=formatter.std_paper_3x1_partial_width,
                                                      xscale=xscale)

    def last_24h_plots(self):
        self.plot_figures.plot_temperature_series(folder=folders['06_last_24_hours'],
                                                  formatter=formatter.std_paper_1x1_full_width,
                                                  xaxis_type='datetime',
                                                  last_day=True)
        self.plot_figures.plot_moisture_series(folder=folders['06_last_24_hours'],
                                               formatter=formatter.std_paper_1x1_full_width,
                                               xaxis_type='datetime',
                                               last_day=True)
        self.plot_figures.plot_all_temperature_series(folder=folders['06_last_24_hours'],
                                                      formatter=formatter.std_paper_3x1_full_width,
                                                      xaxis_type='datetime',
                                                      last_day=True)
        self.plot_figures.plot_all_moisture_series(folder=folders['06_last_24_hours'],
                                                   formatter=formatter.std_paper_3x1_full_width,
                                                   xaxis_type='datetime',
                                                   last_day=True)

    def plot_special_comsol_solution_plots(self, xscale):
        self.plot_figures.plot_temperature_gradient_with_comsol(folder=folders['04_gradient_temperature'],
                                                                formatter=formatter.std_paper_1x1_partial_width,
                                                                xscale=xscale,
                                                                comsol_dfs=comsol_dfs)


    def plot_everything(self, xscale):
        self.all_combined_plot(xscale)
        self.temperature_series_separate()
        self.temperature_gradient_separate(xscale)
        self.moisture_series_separate()
        self.moisture_gradient_separate(xscale)
        self.temperature_series_combined()
        self.temperature_gradient_combined(xscale)
        self.moisture_series_combined()
        self.moisture_gradient_combined(xscale)
        self.last_24h_plots()





