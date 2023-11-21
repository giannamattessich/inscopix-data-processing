import os 
import json 
import re # regex
from pathlib import Path  
from itertools import islice  # list manipulation
from functools import partial  # modify function default parameters
import numpy as np

# Interface to abstract Timeseries and Longitudinal Registration processing
class Process(object):
    def __init__(self, data_dir, output_folder_name):
        self.data_dir = Path(data_dir)
        self.output_folder_name = output_folder_name
        #if self.output_folder_name is None:
        #    self.output_dir = self.data_dir / 'processed'
        #else:
        self.output_dir = self.data_dir / output_folder_name
        # create the output folder if it does not exist
        self.output_dir.mkdir(exist_ok=True)
        # store series label, list of recordings, and # of recordings in each series
        if self.get_series_recs() is None:
            raise ValueError(
                'Could not find recording files in the selected input directory. Please check that .isxd files are in year-month-day-hour-minute-second format')
        else:
            self.series_rec_names = self.get_series_recs()
        self.day_labels = list(self.series_rec_names.keys())
        self.recordings_series = list(self.series_rec_names.values())
        self.num_rec_per_series = [len(child_list) for child_list in self.recordings_series]
        self.rec_dir_series = self.series_suffix('.isxd', self.recordings_series, output_dir=self.data_dir)
        self.total_num_recordings = np.sum(self.num_rec_per_series)
        self.series_suffix = partial(self.series_suffix, dir_series= self.rec_dir_series)
        #create file names for each series
        self.pp_files_series = self.series_suffix('-PP.isxd')
        self.bp_files_series = self.series_suffix('-PP-BP.isxd')
        self.mc_files_series = self.series_suffix('-PP-BP-MC.isxd')
        self.cnmfe_files_series = self.series_suffix('-PP-BP-MC-cnmfe-cellset.isxd')
        self.cnmfe_eventfiles_series = self.series_suffix('-PP-BP-MC-cnmfe_event.isxd')
        self.cnmfe_spike_event_series = self.series_suffix('-PP-BP-MC-cnmfe-spikes_event.isxd')
        self.dff_files_series = self.series_suffix('-PP-BP-MC-dff.isxd')
        #create files for event detection
        self.mean_proj_files = self.series_label_prefix('-mean_image.isxd')
        self.crop_rect_files = self.series_label_prefix('-crop_rect.csv')
        self.translation_files = self.series_label_prefix('-trans.csv')
        self.maxdff_files = self.series_label_prefix('-maxdff.isxd')
        self.cnmfe_csv = self.series_label_prefix('-cnmfe-cellset.csv')
        self.cnmfe_tiff = self.series_label_prefix('-cnmfe-cellset.tiff')
        self.cnmfe_spike_event_csvs = self.series_label_prefix('-cnmfe-spike-events.csv')
        self.timeseries_events = self.series_label_prefix('-timeseries-spikes.csv')
        #write and read json files that contain series
        self.series_rec_json = self.write_read_json('series_rec_names.json', self.series_rec_names)
        self.rec_dir_json = self.write_read_json('rec_dir_series.json', self.rec_dir_series)
        self.pp_files_json = self.write_read_json('pp_files_series.json', self.pp_files_series)
        self.bp_files_json = self.write_read_json('bp_files_series.json', self.bp_files_series)
        self.mc_files_json = self.write_read_json('mc_files_series.json', self.mc_files_series)
        self.cnmfe_files_json = self.write_read_json('cnmfe_files_series.json', self.cnmfe_files_series)
        self.cnmfe_events_json = self.write_read_json('cnmfe_eventfiles_series.json', self.cnmfe_eventfiles_series)
        self.cnmfe_spikes_json = self.write_read_json('cnmfe_spike_event_series.json', self.cnmfe_spike_event_series)
        print(f'{self.total_num_recordings} recordings found !')

    # store recordings for each day in a dictionary with day labels as keys and an array of recording files for that day as values
    # using the file directory, find the files that match the raw recording naming scheme using regex year-month-day-hour-minute-second format and '.isxd' ending
    # recording files should be named in the usual raw-recording output scheme or this function will break
    # to account for files with dropped frames-> if the dates match replace the unprocessed file found with the processed one
    def get_series_recs(self):
        directory = os.listdir(self.data_dir)
        # create dictionary with dates as the keys (ex. 2023-08-04) and array of recordings for that day as values
        series_recs_dates = {}
        # create dictionary to be used for processing with the days as day labels (ex. day_1, day_2...)
        series_rec_names = {}
        days = set()
        # regex pattern to match the .isxd files using year-month-day-hour-minute-hour-second 
        pattern = re.compile(pattern=r'\d{4}-\d{2}-\d{2}')
        num_day = 1
        for file in directory:
            if (bool(pattern.search(file)) & file.endswith('.isxd')):
                m = pattern.search(file)
                if m:
                    date = m.group()
                    # case where day has not been added as key to the dates dictionary yet
                    if date not in days:
                        days.add(date)
                        recs = [file]
                        series_recs_dates[date] = recs
                    # otherwise append to already created value 
                    else:
                        date_rec_list = series_recs_dates[date] + [file]
                        series_recs_dates[date] = date_rec_list
        #create a new dictionary that has 'day_i' as key label rather than the date itself
        for day in series_recs_dates.keys():
            label = f'day_{num_day}'
            series_rec_names[label] = series_recs_dates[day]
            num_day += 1
        if len(series_rec_names) == 0:
            return None
        return series_rec_names
    

    def split2series(self, Input, length_to_split=None):
        """
        Convert a straight list into a nested one, a list of time series.
        for example: [1, 2, 3, 4] --> [[1, 2], [3, 4]]
        given an input length [2, 2]
        Args:
            Input: straight list such as [1, 2, 3, 4]
            length_to_split: No. of elements to be distributed into nested lists
        Return:
            Output: Nested list such as [[1, 2], [3, 4]]
        """
        if not length_to_split:
            length_to_split = self.num_rec_per_series
        # Using islice to redistribute the elements from the input list
        Inputt = iter(Input)
        Output = [list(islice(Inputt, elem)) for elem in length_to_split]
        return Output

    def merge_series(self, Input):
        """
        Flatten a nested list, a list of time series into a single list
        for example: [[1, 2], [3, 4]] --> [1, 2, 3, 4]
        Args:
            Input: Nested list
        Return:
            Output: flattened list
        """
        if any(isinstance(i, list) for i in Input):
            Output = [recording for child_list in Input for recording in child_list]
        else:
            Output = Input  # skip the conversion if input list is not nested
        return Output

    def series_suffix(self, suffix, dir_series, output_dir=None):
        """
        add suffix to series filename
        1. The input dir series are merged first
        2. The merged list is used to add suffix to filenames
        3. The new filenames list is split to new dir series
        if input list is nested
        Args:
            dir_series: input dir series
                        Default: raw recording dirs
            suffix: User input for filename suffixing
            output_dir: the output folder to store new files
                        Default: output dir specified from the previous step
        Return:
            Output: new dir series with suffixed filenames
        """
        if not output_dir:
            output_dir = self.output_dir
        old_names = self.merge_series(dir_series)  # step 1
        new_names = [str(Path(output_dir, Path(dir).stem + suffix)) for dir in old_names]  # step 2
        if any(isinstance(i, list) for i in dir_series):
            num_rec = [len(child_list) for child_list in dir_series]
            Output = self.split2series(new_names, length_to_split=num_rec)
        else:
            Output = new_names  # step 3 skipped
        return Output
    

    def series_label_prefix(self, suffix, prefix=None, output_dir=None):
        """
        join series label prefix with suffix input
        Args:
            suffix: input, filename suffix to be joined
            prefix: series labels as prefix
            output_dir: the output folder to store dirs with new names
                        Default: output dir specified from the previous step
        Return:
            Output: new dir list with prefixed filenames
        """
        if not prefix:
            prefix = self.day_labels
        if not output_dir:
           output_dir = self.output_dir
        return [str(Path(output_dir, name + suffix)) for name in prefix]
    
     #define functions to read and write JSON files
    def write_json(self, file_string, file):
        with open(self.output_dir / file_string, 'w') as write:
            json.dump(file, write)

    #return the read output json 
    def read_json(self, file_string):
        with open(self.output_dir / file_string, 'r') as read:
            return json.load(read)
        
    #provide the file and its name (file_string) to be written and read  
    def write_read_json(self, file_string, file):
        file_to_write_read = os.path.join(self.output_dir, file_string)
        if not os.path.exists(file_to_write_read):
            with open(file_to_write_read, 'w') as write:
                json.dump(file, write)
        with open(file_to_write_read, 'r') as read:
            return json.load(read)

    # isx api will not process files for a day if one of them exists already, this function is a work-around to skip processing tasks if the
    # file outputs already exist, if not all of the recordings from that day have gone through processing delete the files that exist and reprocess them all
    
    # check whether all the files from a single day have output a file from a task
    # if one of the processed file exists in the dir but the other ones dont then delete those files and reprocess the entire day
    # compare list of files for a day from the file series JSON for that task with the main directory     
    def check_all_recordings_processed(self, series, day_i):
        if not series:
            raise ValueError('Provided series does not exist')
        if not series[day_i]:
            raise IndexError('Day index provided is not in the series')
        list_of_output_files = [os.path.basename(file) for file in series[day_i]]
        directory = os.listdir(self.output_dir)
        in_dir = [file in directory for file in list_of_output_files]
        # case -> all files for that day and series have already been processed
        if all(in_dir):
            return True
        # case -> only one of the recordings from that day has been processed -> delete from day and reprocess 
        elif any(in_dir):
            try:
                files_to_delete_in_dir = list_of_output_files
                file_num = 0
                for file in files_to_delete_in_dir:
                    file_exists = in_dir[file_num]
                    if file_exists:
                        path = os.path.join(str(self.output_dir), file)
                        os.remove(path)
                        print(f'File deleted: {path}')
                    file_num += 1
                return False
            except OSError as e:
                print(f'Could not delete {path}: {e}')     
        # case -> there are no recordings for that day that have been processed and processing can continue    
        else:
            return False
        