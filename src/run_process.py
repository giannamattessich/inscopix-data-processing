import sys
sys.path.append(r"C:\Users\Gianna\Documents\Python Scripts\time_series_and_LR_processing")
from src.backend.Timeseries import Timeseries
from src.backend.LongitudinalRegistration import LongitudinalRegistration

# command line functions to run without using GUI and manually entering paths
def run_timeseries(data_dir, output_folder):
    t = Timeseries(data_dir, output_folder_name=output_folder)
    t.preprocess(2,4)
    t.bandpass_filter()
    t.mean_projection_frame()
    t.motion_correct()
    t.cnmfe_apply()
    t.export_cell_set_to_tiff()
    t.event_detection_auto_classification()
    t.deconvolve_cells()
    t.export_spike_events_to_csv()
    t.vertical_csv_alignment()

def run_lr(data_dir, output_folder):
    l = LongitudinalRegistration(data_dir, output_folder)
    l.calculate_dff()
    l.longitudinal_registration()
    l.store_cnmfe_cellset_output()
    l.rename_cells_from_timeseries()

####** change data_dir variable to the folder path that contains .isxd files**####
####** change output_folder_name to the name of the subfolder you want to create within the provided data_dir **####
data_directory = r"H:\Miso\20231007_redownload"
#t = Timeseries(data_directory, 't')
run_timeseries(data_directory, 'processed')
#run_lr(data_directory, 'wait')