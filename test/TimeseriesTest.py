import unittest
from unittest import TestCase
import os
from backend.Timeseries import Timeseries

#output folder doesnt exist yet -> 3 days (1 rec each)
test_object_1 = Timeseries(r"F:\LR_kombucha_20231002_20231003_20231005", "test_output")
#output already exists -> 3 days (1 rec each)
test_object_2 = Timeseries(r"F:\LR_kombucha_20231002_20231003_20231005", "processed")
# output folder exists -> 1 day (1 rec)
test_object_3 = Timeseries(r"F:\LR_kombucha_20231007", "processed")
# output folder exist -> 3 days(3 recs day 1, 5 recs day 2, 3 recs day 3)
test_object_4 = Timeseries(r"F:\LR_miso_20230807_20230810_20230815", "processed-diameter-adjust")
# output folder doesnt exist yet -> 3 days(3 recs day 1, 5 recs day 2, 3 recs day 3)
test_object_5 = Timeseries(r"F:\LR_miso_20230726_20230803_20230807", "test_output")

class TestTimeseries(TestCase):

    def test_input_dir_no_isxd(self):
        dummy_dir = r'C:\Users\Gianna\Desktop\Analysis\20230214_kimchi'
        with self.assertRaises(ValueError):
            Timeseries(dummy_dir, None)
    
    
    def test_series_rec_names(self):
        assert test_object_2.series_rec_names == {"day_1": ["2023-10-02-15-15-02_video_green.isxd"],
                                                   "day_2": ["2023-10-03-14-29-16_video_green.isxd"],
                                                     "day_3": ["2023-10-05-11-19-11_video_green.isxd"]}
        
        
        assert test_object_5.series_rec_names == {"day_1": ["2023-07-26-12-23-13_video_green_processed.isxd", "2023-07-26-13-21-37_video_green.isxd",
                                                             "2023-07-26-14-08-50_video_green_processed.isxd"],
                                                        "day_2": ["2023-08-03-11-46-40_video_green_processed.isxd", "2023-08-03-12-58-19_video_green_processed.isxd",
                                                                   "2023-08-03-13-58-20_video_green_processed.isxd", "2023-08-03-15-10-35_video_green.isxd",
                                                                     "2023-08-03-16-11-41_video_green_processed.isxd"],
                                                             "day_3": ["2023-08-07-12-33-18_video_green_processed.isxd", "2023-08-07-13-44-53_video_green_processed.isxd",
                                                                        "2023-08-07-14-48-43_video_green_processed.isxd"]}
        
        assert test_object_3.series_rec_names == {"day_1": ["2023-10-07-10-25-59_video_green.isxd"]}

    def test_num_rec_series(self):
        assert test_object_1.num_rec_per_series == [1, 1, 1]
        assert test_object_3.num_rec_per_series == [1]
        assert test_object_4.num_rec_per_series == [3, 5, 3]

    def test_all_files_processed(self):
        self.assertTrue(test_object_2.check_all_recordings_processed(series=test_object_2.cnmfe_eventfiles_series,
                                                              day_i = 1))
        self.assertTrue(test_object_4.check_all_recordings_processed(series= test_object_4.mc_files_series, 
                                                             day_i = 0))
        
    def test_one_file_unprocessed(self):
        # test object with one -BP.isxd recording deleted for a singla day
        test_object_4.check_all_recordings_processed(test_object_4.bp_files_series, 0)
        assert os.path.exists(r"F:\LR_miso_20230807_20230810_20230815\processed-diameter-adjust\2023-08-07-14-48-43_video_green_processed-PP-BP.isxd") == False

        self.assertTrue(test_object_4.check_all_recordings_processed(test_object_4.bp_files_series, 1))
        self.assertTrue(test_object_4.check_all_recordings_processed(test_object_4.bp_files_series, 2))

    def test_recordings_deleted(self):
        test_object_3.check_all_recordings_processed(test_object_3.cnmfe_spike_event_series, 0)
        self.assertTrue(os.path.exists(r"F:\LR_kombucha_20231007\processed\2023-10-07-10-25-59_video_green-PP-BP-MC-cnmfe-spikes_event.isxd"))

    def test_preprocess(self):
        test_object_4.preprocess(2, 4)
        self.assertTrue(os.path.exists(r"F:\LR_miso_20230807_20230810_20230815\processed-diameter-adjust\2023-08-07-13-44-53_video_green_processed-PP.isxd"))
    
    def test_bandpass(self):
        test_object_4.bandpass_filter()
        self.assertTrue(os.path.exists(r"F:\LR_miso_20230807_20230810_20230815\processed-diameter-adjust\2023-08-07-14-48-43_video_green_processed-PP-BP.isxd"))
if __name__ == '__main__':
    unittest.main()