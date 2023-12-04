from genericpath import isfile
import isx
import sys
import os,glob
from matplotlib import pyplot as plt
import numpy as np
import random
import time
import multiprocessing

"""SOURCE AUTHOR: Mahir Patel, @mahir1010"""

# Number of parallel processes
NUM_PROCESSES = 2

# ROI 
Left = 450 
Top = 0
Width = 50
Height = 800

roi = [[Top, Top + Height], [Left, Left + Width]]
normalize = lambda x: (((x - x.min()) / (x.max() - x.min()))*255).astype(np.uint8)
# normalize = lambda x: x

def get_thresholds(movie: isx.Movie, test_n=10, padding_fraction=0.01) -> int:
    indices = [random.randint(0, movie.timing.num_samples) for i in range(test_n)]
    max_hist = []
    max_hist_white = []
    for index in indices:
        try:
            img = normalize(movie.get_frame_data(index)[roi[0][0]:roi[0][1], roi[1][0]:roi[1][1]])
        except:
            continue
        histogram = np.histogram(img.flatten(), range(0, 257))[0]
        max_hist.append(histogram[0])
        max_hist_white.append(np.mean(histogram[-15:]))
    padding = (Height * Width * padding_fraction)
    return np.median(max_hist) + padding, np.median(max_hist_white) + padding




def process_isxd(file_path):
    file_name = os.path.basename(file_path)
    movie = None
    try:
        movie = isx.Movie.read(file_path)
    except:
        print("Invalid inscopix file")
        return
    segments = []
    segment = None
    is_corrupt = False
    threshold,threshold_2 = get_thresholds(movie,test_n=30,padding_fraction=0.001)
    print("Threshold Set to ", threshold, ' and',threshold_2)
    total_frames = movie.timing.num_samples
    print(f"{file_path} Total Frames:{movie.timing.num_samples}")
    avg_fps = []
    for frame_number in range(0, movie.timing.num_samples):
        try:
            start = time.time()
            print(f'\r Frame:{frame_number}', end=' ')
            frame = None
            try:
                frame = normalize(movie.get_frame_data(frame_number)[roi[0][0]:roi[0][1], roi[1][0]:roi[1][1]])
                histogram = np.histogram(frame.flatten(), range(0, 257))[0]
            except:
                frame = None
            if frame is None or histogram[0] > threshold or np.mean(histogram[-15:]) > threshold_2:
                if is_corrupt:
                    segment[1] = frame_number
                else:
                    if segment is None:
                        segment = [frame_number, frame_number]
                    else:
                        segments.append(segment.copy())
                        segment[0] = frame_number
                        segment[1] = frame_number
                    is_corrupt = True
            else:
                is_corrupt = False
            FPS = round(1 / (time.time() - start))
            avg_fps.append(FPS)
            if len(avg_fps) > 5:
                avg_fps.pop(0)
            FPS = np.mean(avg_fps)
            print(f'{file_name}  FPS:{FPS} ETA:{round((total_frames - frame_number) / FPS, 2)} seconds', end='')
        except KeyboardInterrupt:
            return
        except Exception:
            continue
    print('\n')
    append_last = False
    try:
        append_last = (segments[-1][0]!=segment[0] or segments[-1][1]!=segment[1])
        segments.append(segment.copy())
    except:
        append_last = False
    if (len(segments)==0 and segment is not None):
        segments.append(segment.copy())
    if len(segments):
        final_segments = segments.copy()
        print('\n', final_segments)
        print('Trim started...')
        isx.trim_movie(file_path, file_path.replace('.isxd', '_processed.isxd'), final_segments)
    else:
        print(f"No dropped frames in {file_path}")

def run_process(root_directory):
    file_paths = glob.glob(os.path.join(root_directory,'*.isxd'))
    file_paths = [fp for fp in file_paths if '_processed' not in fp]
    file_paths = [fp for fp in file_paths if not os.path.exists(fp.replace('.isxd', '_processed.isxd'))]
    print(f"{len(file_paths)} {'file' if len(file_paths)==1 else 'files'} found!!")
    processes = []
    # process_isxd(file_paths[0])
    with multiprocessing.Pool(processes=NUM_PROCESSES) as p:
        p.map(process_isxd,file_paths)

# if __name__ == "__main__":
#     run_process(r"F:\drop_frame_gui")


# if __name__=="__main__":
#     if len(sys.argv) != 2:
#         print("Usage 'python RemoveCorruptFrames.py <isxd_directory_path>")
#         exit(-1)
#     root_directory = sys.argv[1]
#     # root_directory = "C:\\inscopix"
#     file_paths = glob.glob(os.path.join(root_directory,'*.isxd'))
#     file_paths = [fp for fp in file_paths if '_processed' not in fp]
#     file_paths = [fp for fp in file_paths if not os.path.exists(fp.replace('.isxd', '_processed.isxd'))]
#     print(f"{len(file_paths)} {'file' if len(file_paths)==1 else 'files'} found!!")
#     processes = []
#     # process_isxd(file_paths[0])
#     with multiprocessing.Pool(processes=NUM_PROCESSES) as p:
#         p.map(process_isxd,file_paths)
#     # for file_path in file_paths:
#     #     print('\n',f'Processing {file_path}')
#     #     processes.append(multiprocessing.Process(target=process_isxd,args=(file_path,)))
#     #     processes[-1].start()
    
#     # for process in processes:
#     #     process.join()
    
