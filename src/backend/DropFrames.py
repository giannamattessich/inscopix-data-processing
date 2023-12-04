import re
import os
import shutil
from src.backend.RemoveCorruptFrames import run_process

class DropFrames:
    def __init__(self, directory):
        super().__init__()
        self.directory = directory
        #self.finished_signal = TriggerSignal()
    
    # check if multiple versions of same file exist
    def find_file_duplicate(self, file_list):
        new_set = set()
        for file in file_list:
            if file not in new_set:
                new_set.add(file)
            else:
                # remove duplicate file
                os.remove(os.path.join(self.directory, file))

    # once corrupt files are processed, move the original corrupt file into new folder
    def delete_corrupt_files(self):
        # list directory
        file_list = os.listdir(self.directory)
        # .isxd regex -> yyyy-mm-dd-hr-mm-ss
        isxd_regex_pattern = re.compile(pattern=r'\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}')
        dropped_frame_recordings = sorted([])
        # create folder path for corrupt files to move to
        corrupt_file_folder = os.path.join(self.directory, 'corrupt_recordings')
        for file in file_list:
            if (bool(isxd_regex_pattern.search(file)) & file.endswith('.isxd')):
                recording_time = isxd_regex_pattern.search(file)
                if recording_time:
                    if file.endswith('processed.isxd'):
                        dropped_frame_recordings.append(file)
        # check if the amount of unique dropped recording values is equal to the list of recordings, otherwise, theres duplicates and one should be deleted 
        if len(set(dropped_frame_recordings)) != len(dropped_frame_recordings):
            self.find_file_duplicate(dropped_frame_recordings)
        # case if there is at least one corrupt recordings 
        if len(dropped_frame_recordings) > 0:
            corrupt_file_folder = os.path.join(self.directory, 'corrupt_recordings')
            os.mkdir(corrupt_file_folder, exist_ok=True)
            for file in dropped_frame_recordings:
                unprocessed_file = file.replace('_processed', '')
                if unprocessed_file in file_list:
                    corrupt_file_to_move = os.path.join(self.directory, unprocessed_file)
                    shutil.move(corrupt_file_to_move, corrupt_file_folder)

    def drop_frames(self):
        run_process(self.directory)
