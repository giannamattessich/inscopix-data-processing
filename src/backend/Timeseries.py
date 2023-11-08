import os
import isx
import pandas as pd
from src.backend.process import Process
import textwrap  # to format multiline string message
import shutil  # to move files
#from functools import partial  # modify function default parameters

class Timeseries(Process):
    def __init__(self, data_dir, output_folder_name):
        super().__init__(data_dir, output_folder_name)

    # perform preprocessing and output --PP.ixsd files
    def preprocess(self, tp_downsampling, sp_downsampling):
        print('Preprocessing, please wait...\n')
        try:
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.pp_files_series, day_i):
                    isx.preprocess(
                        input_movie_files= self.rec_dir_json[day_i],  # one series per loop
                        output_movie_files= self.pp_files_json[day_i], 
                        temporal_downsample_factor=tp_downsampling,
                        spatial_downsample_factor=sp_downsampling,
                        crop_rect=None,
                        fix_defective_pixels=True,
                        trim_early_frames=True)
                    print('{} preprocessing completed'.format(day_label))
        except Exception as e:
            print(f'Error: {e}')


    # Perform spatial bandpass filtering with default values.
    def bandpass_filter(self):
        print('Applying bandpass filter, please wait...\n')
        try:
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.bp_files_series, day_i):
                    isx.spatial_filter(
                    input_movie_files= self.pp_files_json[day_i],
                    output_movie_files=self.bp_files_json[day_i],
                    low_cutoff=0.005,
                    high_cutoff=0.5,
                    retain_mean=False,
                    # leave subtract_global_minimum setting as true
                    # for correct dff display
                    subtract_global_minimum=True)
            print('{} bandpass filtering completed'.format(day_label))
        except Exception as e:
            print(f'Error: {e}')
        

    # use the mean frame as a reference to apply motion correction.    
    def mean_projection_frame(self):
        try:
            for day_i, (day_label, mean_proj_file) in enumerate(zip(self.day_labels, self.mean_proj_files)):
                if not os.path.exists(os.path.join(str(self.output_dir), f'{day_label}-mean_image.isxd')):
                    isx.project_movie(
                        input_movie_files=self.bp_files_json[day_i],
                        output_image_file=mean_proj_file,
                        stat_type='mean')  # types: 'mean', 'min', or 'max'
                    message = """
                        {} temporal projection completed.
                        A new file has been generated and will be used
                        as a reference frame for motion correction
                    """.format(day_label)
                print(textwrap.dedent(message))
        except Exception as e:
            print(f'Error:{e}')

    # use for loop to apply motion correction one series at a time
    def motion_correct(self):
        print('Applying motion correction. Please wait...\n')
        try:
            for day_i, (day_label, mean_proj_file) in enumerate(zip(self.day_labels, self.mean_proj_files)):
                #mc_files_json = self.write_read_json('mc_files_series.json', self.mc_files_series)
                #bp_files_json = self.read_json('bp_files_series.json')
                if not self.check_all_recordings_processed(self.mc_files_series, day_i):
                    isx.motion_correct(
                        input_movie_files=self.bp_files_json[day_i],
                        output_movie_files=self.mc_files_json[day_i],
                        max_translation=20,
                        low_bandpass_cutoff=None,
                        high_bandpass_cutoff=None,
                        roi=None,
                        # use movie and frame index to set a fixed frame as reference
                        # turned off if set to 0
                        reference_segment_index=0,
                        reference_frame_index=0,
                        # use the mean projection file generated in the previous step
                        # as a reference frame for motion correction
                        reference_file_name=mean_proj_file,
                        global_registration_weight=1.0,
                        output_translation_files= None,
                        #output_translation_files= self.translation_files[day_i],
                        output_crop_rect_file= self.crop_rect_files[day_i])
            print('{} motion correction completed'.format(day_label))
        except Exception as e:
            print(f'Error:{e}')

    # algorithm applies to concatenated movies, every recording has same cellmaps 
    # adjust cell_diameter, min_pnr, and min_corr values as needed 
    def cnmfe_apply(self):
        print('Applying CNMFe algorihm to detect cells, please wait...\n')
        try:
            export_path = os.path.join(self.output_dir, 'cnmfe_tmp')
            if not os.path.exists(export_path):
            # make cnmfe subfolder to store temporal files including concatenated TIFFs
                os.mkdir(export_path)
                # use motion corrected movie series as input and do not use df/f0 movie
                # since the background info will be used for noise estimation
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.cnmfe_files_series, day_i):
                    isx.run_cnmfe(
                        input_movie_files=self.mc_files_json[day_i],
                        output_cell_set_files=self.cnmfe_files_json[day_i],
                        output_dir=str(export_path),
                        cell_diameter=7,
                        min_corr=0.8,
                        min_pnr=10,
                        bg_spatial_subsampling=2,
                        ring_size_factor=1.4,
                        gaussian_kernel_size=1,
                        closing_kernel_size=1,
                        merge_threshold=0.7,
                        processing_mode='parallel_patches',
                        num_threads=4,
                        patch_size=80,
                        patch_overlap=20,
                        output_unit_type='df_over_noise')
                    message = """
                        {} CNMFe cell detection completed. A few temporary files
                        have been generated in the cnmfe_tmp subfolder\n""".format(day_label)
                    print(textwrap.dedent(message))
        except Exception as e:
            print(f'Error:{e}')

    def move_files(source, destination, type='.tiff'):
        """
        move files from source to destination, filtered by file type
        Parameters:
            source: path for source folder
            destination: path for destination folder
            type: file extension, by default only move tiff files
        Returns:
            None
        """
        if not os.path.exists(destination):
            os.mkdir(destination)  # make new subfolder
                # get file list from the source folder
            filelist = os.listdir(source)
            for file in filelist:
                if file.endswith(type):  # filter by file type
                    shutil.move(source / file, destination / file)
                else:
                    print("Tiff folder already exists, no files were moved\n")
            

    # export csv file for all cell traces
    # export multiple cell maps, one tiff image for each cell
    def export_cell_set_to_tiff(self):
        try:
            for day_i, day_label in enumerate(self.day_labels):   
                if not os.path.exists(self.cnmfe_csv[day_i]):
                    isx.export_cell_set_to_csv_tiff(
                        input_cell_set_files=self.cnmfe_files_series[day_i],
                        output_csv_file=self.cnmfe_csv[day_i],
                        output_tiff_file=self.cnmfe_tiff[day_i],
                        time_ref='start',
                        output_props_file='')
                    print("Export completed. Tiff files were stored in the tiff subfolder")
            #self.task_dict['export_to_tiff'] = True
            self.move_files(self.output_dir, self.output_dir / "cnmfe_tiff")
        except Exception as e:
            print(f'Error:{e}')
        

    # output event files
    def event_detection_auto_classification(self):
        try:
            # Run event detection on the CNMFe cell sets.
            print('Applying auto classification. Please wait...\n')
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.cnmfe_eventfiles_series, day_i):
                    isx.event_detection(
                        input_cell_set_files=self.cnmfe_files_json[day_i],
                        output_event_set_files=self.cnmfe_events_json[day_i],
                        threshold=5,  # sigma threshold
                        tau=0.2,  # default is 200ms for Gcamp6f
                        event_time_ref='beginning',  # export other timing separately
                        ignore_negative_transients=True,
                        accepted_cells_only=False)
                    print('Event detection completed for {}'.format(day_label))
                    # make name for event filter
                    events_filters = [('SNR', '>', 3), ('Event Rate', '>', 0), ('Cell Size', '>', 0)]
                    isx.auto_accept_reject(input_cell_set_files=self.cnmfe_files_json[day_i],
                                    input_event_set_files= self.cnmfe_events_json[day_i],
                                    filters=events_filters)
                    print('Auto classification completed. The cnmfe cellset has been updated.')
        except Exception as e:
            print(f'Error:{e}')

    # output spikes 
    def deconvolve_cells(self):
        try:
            print('Deconvolving...')
            for day_i, day_label in enumerate(self.day_labels):
                if not self.check_all_recordings_processed(self.cnmfe_spike_event_series, day_i):
                    isx.deconvolve_cellset(
                        input_raw_cellset_files= self.cnmfe_files_json[day_i], 
                        output_spike_eventset_files= self.cnmfe_spikes_json[day_i], 
                        accepted_only= False,
                        spike_snr_threshold= 5.00
                    )
                    print(f'Deconvolution completeted for {day_label}')
                else:
                    print(f'{day_label} already processed!')
        except Exception as e:
            print(f'Error:{e}')

    # export spike to cellset csv
    def export_spike_events_to_csv(self): 
        try:
            print('Exporting spikes to CSV...')
            for day_i, day_label in enumerate(self.day_labels):
                if not os.path.exists(self.cnmfe_spike_event_csvs[day_i]):
                    isx.export_event_set_to_csv(
                        input_event_set_files = self.cnmfe_spikes_json[day_i],
                        output_csv_file = self.cnmfe_spike_event_csvs[day_i],
                        time_ref= 'unix'
                    ) 
                    print('Event detection completed for {}'.format(day_label))
        except Exception as e:
            print(f'Error:{e}')

# input cellset with each cell as col and output new csv with time of spike, cell, and value as cols 
    def vertical_csv_alignment(self):
        try:
            print('Realigning CSV...')
            for day_i, day_label in enumerate(self.day_labels):
                if not os.path.exists(self.timeseries_events[day_i]):
                    data = []
                    df = pd.read_csv(self.cnmfe_spike_event_csvs[day_i])
                    for row in range(0, len(df)):
                        at_time = df.loc[row]
                        row_len = at_time.size
                        for col in range(1, row_len):
                            if at_time[col] > 0:
                                if df.loc[row]['Time (s)'] != 0:
                                    new_row = [df.loc[row]['Time (s)'], df.columns[col], df.loc[row][col]]
                                    data.append(new_row)
                    new_df = pd.DataFrame(data, columns = ['Time (s)', ' Cell Name', 'Value']).sort_values(by=[' Cell Name', 'Time (s)'])
                    output_path= self.timeseries_events[day_i]
                    new_df.to_csv(output_path, index=False)
        except Exception as e:
            print(f'Error:{e}')