import os 
import isx
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from src.backend.process import Process


class LongitudinalRegistration(Process):
    def __init__(self, data_dir, output_folder_name):
        super().__init__(data_dir, output_folder_name)
        #make new input/output files for longitudinal registratiohn processing
        """
        A movie list can be used as an optional second input to cnmfe lr output
        to apply the same transformation resulting from cnmfe cellset registration.
        """
        self.cnmfe_cellset_lr_input = self.merge_series(self.cnmfe_files_series)
        self.cnmfe_cellset_lr_output = self.series_suffix('-LR.isxd', dir_series= self.cnmfe_cellset_lr_input)
        self.dff_files_lr_input = self.merge_series(self.dff_files_series)
        self.dff_files_lr_output = self.series_suffix('-LR.isxd', dir_series= self.dff_files_lr_input)  
        self.maxdff_files_lr = self.series_label_prefix('-maxdff-LR.isxd')
        self.maxcnmfe_files_lr = self.series_label_prefix('-maxcnmfe-LR.isxd')
        self.lr_cells_from_day = self.series_label_prefix("-longitudinal_spikes.csv")

        self.cnmfe_cellset_lr_series = {}
        self.dff_lr_series = {}
        self.maxdff_files_series = {}
        #self.lr_csv_file = str(self.output_dir / 'lr_index_table.csv')

        #self.cnmfe_cellset_lr_series_json = None
        #self.dff_lr_series_json = None
        self.lr_csv_file = os.path.join(self.output_dir,'lr_index_table.csv')
        
    # calculate delta f/f from motion corrected recordings 
    def calculate_dff(self):
        print('Calculating deltaf/f0, please wait...\n')
        try:
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.dff_files_series, day_i):
                    isx.dff(input_movie_files= self.mc_files_json[day_i],
                            output_movie_files=self.dff_files_series[day_i],
                            f0_type='mean')
                    print('A new df/f movie has been generated for',
                        day_label)
        except Exception as e:
            print(f'ERROR: {e}')

    def longitudinal_registration(self):
        print('Longitudinal Registration begin...')
        try:
            if not os.path.exists(self.lr_csv_file):  # skip if output file already exists
                isx.longitudinal_registration(
                    self.cnmfe_cellset_lr_input,
                    self.cnmfe_cellset_lr_output,
                    input_movie_files=self.dff_files_lr_input,
                    output_movie_files=self.dff_files_lr_output,
                    csv_file=self.lr_csv_file, accepted_cells_only=False)
                print('Longitudinal registration for {} and {} time series completed'.format(self.day_labels[0], self.day_labels[0]))
                print(os.path.exists(self.lr_csv_file))
        except Exception as e:
            print(f"ERROR: {e}")

    def store_cnmfe_cellset_output(self):
        for day_i, key in enumerate(self.series_rec_names):
            self.cnmfe_cellset_lr_series[key] = self.split2series(self.cnmfe_cellset_lr_output)[day_i]
            self.dff_lr_series[key] = self.split2series(self.dff_files_lr_output)[day_i]
        self.write_json('cnmfe_cellset_lr.json', self.cnmfe_cellset_lr_series)
        self.write_json('dff_files_lr.json', self.dff_lr_series)


    def calculate_max_projection(self):
        for day_i, day_label in enumerate(self.day_labels):
            if not self.check_all_recordings_processed(self.maxdff_files_series, day_i):  # skip if file exists
                isx.project_movie(
                    input_movie_files=self.split2series(self.dff_files_lr_output)[day_i],
                    output_image_file= self.maxdff_files_lr[day_i],
                    stat_type='max')  # types: 'mean', 'min', or 'max'
                print("maximal projection from {} dff time series completed".\
                    format(day_label))
            else:
                print(Path(self.maxdff_files_lr[day_i]).stem + " exists, process skipped")

    #create plots for max projection after LR 
    def display_max_projections(self):
        # set subplots, matching series No.
        cols = len(self.day_labels)
        rows = int(len(self.day_labels)/cols)
        axes = []
        fig = plt.figure(figsize=(10, 6))
        fig.suptitle('showing maximal projection after LR from each time series', fontsize=20)

        # display max projection of post-LR dff movie
        for day_i, day_label in enumerate(self.day_labels):
            maxdff = isx.Image.read(self.maxdff_files_lr[day_i]).get_data()
            axes.append(fig.add_subplot(rows, cols, day_i+1))
            subplot_title = day_label+"_LR"
            axes[-1].set_title(subplot_title, fontsize=20)
            plt.imshow(maxdff, 'gray')
            plt.xticks([])
            plt.yticks([])

        fig.tight_layout()
        fig.savefig(destination= self.output_dir)
        plt.close()

        for day_i, key in enumerate(self.series_rec_names):
            self.maxdff_files_series[key] = self.maxdff_files_lr[day_i]
        self.write_json('maxdff_lr.json', self.maxdff_files_series)


    #get the indeces in the 'local cellset' column that represents the first session of everyday that has the local cellset in order to
    # iterate over cell names
    # rename cells from timeseries to global index for cells in each day 
    def get_day_indices_from_lr(self):
        day_indexes = [0]
        i = 0
        rec_per_series = self.num_rec_per_series
        for day in range(0, len(rec_per_series) - 1):
            i += rec_per_series[day]
            day_indexes.append(i)
        return day_indexes 
     
    # for individual days, rename the local cellset name to the global cellset name for all days
    def rename_cells_from_timeseries(self):
        # read lr index table
        lr_df = pd.read_csv(self.lr_csv_file)
        num_sessions = self.num_rec_per_series
        idx = 0
        j = 0
        day_indices = self.get_day_indices_from_lr()
        cellset_idx = 0
        files = self.timeseries_events
        day_dfs = list(map(pd.read_csv, files))
        lr_realignment_output = self.lr_cells_from_day
        
        if os.path.exists(self.lr_csv_file) & os.path.exists(files[j]):
            for _ in range(0, (len(lr_df))):
                if idx > (len(lr_df)- num_sessions[-1]):
                    break
                cellset_idx = int(lr_df.loc[idx]['local_cellset_index'])
                j = day_indices.index(cellset_idx)

                local_idx = int(lr_df.loc[idx]['local_cell_index'])
                global_idx = int(lr_df.loc[idx]['global_cell_index'])
                cell_to_replace = ' C' + str(local_idx).zfill(3)
                new_cell_val = ' C' + str(global_idx).zfill(3)

                day_dfs[j][' Cell Name'] = day_dfs[j][' Cell Name'].replace(cell_to_replace, new_cell_val)
                idx += num_sessions[j]
        else:
            raise FileNotFoundError('Could not find LR index table or vertically aligned timeseries spikes files')
        for csv_i in range(0, len(day_dfs)):
            day_dfs[csv_i].sort_values(by=[' Cell Name', 'Time (s)']).to_csv(lr_realignment_output[csv_i], index=False)


