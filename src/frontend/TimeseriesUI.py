import traceback
import os
import sys
import secrets
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QMainWindow, QApplication,QFileDialog, QMessageBox
from PyQt5.QtCore import QSize, pyqtSlot as Slot, Qt
from src.workutils.TaskManager import TaskManager
from src.frontend.ImageButton import ImageButton
from src.frontend.GIFPopup import GIFPopup
from PyQt5.QtGui import QPixmap, QFont
from src.backend.Timeseries import Timeseries
from src.backend.LongitudinalRegistration import LongitudinalRegistration
from src.backend.DropFrames import DropFrames

class TimeseriesUI(QMainWindow):

    def __init__(self):
        super().__init__()
        loadUi(r"src\frontend\time_series_ui.ui", self)
        # create task manager to handle worker queue
        self.task_manager = TaskManager(self)
        self.task_manager_dropped_frames = TaskManager(self)
        # get images from GUI folder and filter by images, excluding GIF files
        gui_img_folder_content = os.listdir(r'GUI Images')
        get_pics = list(filter(lambda x: not x.endswith('.gif'), gui_img_folder_content))
        # randomize button image and add button to layout
        self.button_img = secrets.choice(get_pics)
        self.process_button = ImageButton(QPixmap(fr"GUI images\{self.button_img}"))
        self.process_button.setMaximumSize(QSize(300, 250))
        self.horizontalLayout.addWidget(self.process_button)
        self.dropframesbutton.clicked.connect(self.drop_corrupt_frames)

        self.tpdownsamplespin.setValue(2)
        self.spdownsamplespin.setValue(4)
        self.celldiameterspin.setValue(7)
        self.snrspinbox.setValue(5.00)

        # connect buttons to slots
        self.inputdirtext.textChanged.connect(self.set_input_dir)
        self.outputfoldertext.textChanged.connect(self.set_output_dir)
        self.inputdirbutton.clicked.connect(self.open_dir_dialog)
        self.process_button.clicked.connect(self.on_process_button_click)
        self.longitudinal_process_button.clicked.connect(self.on_lr_button_click)
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint)

        #set GUI state
        self.running = False
        self.main_dir_selected = False
        self.output_dir_selected = False 
    
    @Slot()
    # create a timeseries object to perform operations on when a main_dir is selected based on user input 
    def set_output_dir(self):
        self.output_folder = self.outputfoldertext.text()
        if len(self.output_folder) > 0:
            self.output_dir_selected = True
            
    @Slot()
    def set_input_dir(self):
        self.input_dir = self.inputdirtext.text()
        if len(self.input_dir) > 0:
            self.main_dir_selected = True


    def drop_corrupt_frames(self):
        if not self.main_dir_selected:
            self.show_error_message('Input directory has not been selected')
            return
        if not self.output_dir_selected:
            self.show_error_message('Output folder name has not been selected.')
            return 
        if self.running:
            self.show_error_message('Process still running.')
            return
        if ((self.main_dir_selected & self.output_dir_selected) & (not self.running)):
            self.running = True
            self.slowpoke_gif = GIFPopup(r'GUI images\slowpoke.gif', parent=self)
            self.slowpoke_gif.show()
            try:
                self.df = DropFrames(self.input_dir)
                self.task_manager_dropped_frames.set_process_object(self.df)
                self.task_manager_dropped_frames.add_task('drop_frames')
                self.task_manager_dropped_frames.add_task('delete_corrupt_files')
                self.task_manager_dropped_frames.tasks_completed.connect(self.frames_dropped_finish)
                self.task_manager_dropped_frames.start_tasks()
            except Exception as e:
                self.show_error_message(f"ERROR: {e}")
                traceback.print_exc()



    def start_timeseries(self):
        if self.main_dir_selected and self.output_dir_selected:
            self.recording_names = sorted(list(set([recording for recordings in self.series_recs.values() for recording in recordings])))
            
            # Flatten the list of lists into a single list of strings
            recordings_to_process = [recording for recordings in self.series_recs.values() for recording in recordings]
            
            # Join the list of strings
            recordings_to_process_str = (', ').join(recordings_to_process)
            
            days_to_process = (', ').join(list(self.series_recs.keys()))
            self.show_complete_dialog(f"Preprocessing has begun!\nDays: {days_to_process}\nRecordings: {recordings_to_process_str}")


    # determines if processes can be started based on if input/output dirs were selected and if the processing has been instantiated
    def timeseries_set(self):                          
        # check if both input and outputs selected 
        if (not self.main_dir_selected) | (not self.output_dir_selected):
            self.show_error_message('ERROR: Input directory or output folder have not been selected ')
            return False
        else:
            if (len(self.mousenametext.text()) > 0):
                try:
                    self.timeseries_process_object = Timeseries(self.input_dir, self.output_folder, self.mousenametext.text())
                    self.task_manager.set_process_object(self.timeseries_process_object)
                    self.series_recs = self.timeseries_process_object.series_rec_names
                    self.num_days = len(self.series_recs)
                    return True
                except ValueError:
                    self.show_error_message('Could not find recording files in the selected input directory. Please check that .isxd files are in year-month-day-hour-minute-second format to continue.')
                    self.inputdirtext.setText('')
                    self.main_dir_selected = False
                    return False
            else:
                self.show_error_message('Mouse name has not been selected for file naming. ')
                return False
            
    # determines if longitudinal object can be started 
    def longitudinal_set(self):
        if not self.main_dir_selected:
            self.show_error_message('ERROR: Input directory not selected')
            return
        elif not self.output_dir_selected:
            self.show_error_message('ERROR: Output directory was not selected')
            return
        elif (len(self.mousenametext.text()) < 0):
            self.show_error_message('ERROR: mouse name not selected')
            return
        else:
            try:
                if os.path.exists(os.path.join(self.input_dir, self.output_folder)):
                    self.lr_process_object = LongitudinalRegistration(self.input_dir, self.output_folder, self.mousenametext.text())
                    self.task_manager.set_process_object(self.lr_process_object)
                    self.series_recs = self.lr_process_object.series_rec_names
                    self.num_days = len(self.series_recs)
                    if len(self.series_recs) < 2:
                        self.show_error_message("ERROR: Input Directory contains less than 2 files. Please input a directory that contains recordings for at least 2 days.")
                        self.main_dir_selected = False
                        self.inputdirtext.setText('')
                        return False
                    for day_i in range(self.num_days):
                        if not self.lr_process_object.check_all_recordings_processed(self.lr_process_object.mc_files_series, day_i):
                            self.show_error_message(
                                'Longitudinal registration could not begin because the output folder selected does not contain motion corrected files. Please rerun processing steps before proceeding to longitudinal registration.')
                            return False
                    return True
                else:
                    self.show_error_message('Selected input and output folder does not exist. Please provide folders that contain the output of timeseries processing.')
                    return False

            except ValueError:
                    self.show_error_message('Could not find recording files in the selected input directory. Please check that .isxd files are in year-month-day-hour-minute-second format to continue.')
                    self.inputdirtext.setText('')
                    self.main_dir_selected = False
                    return False
        
            

    def start_preprocess(self):
        # add preprocess tasks to queue
        self.snorlax_gif = GIFPopup(r'GUI images\snorlax.gif', parent=self)
        self.task_manager.add_task('preprocess', int(self.tpdownsamplespin.value()), int(self.spdownsamplespin.value()))
        self.task_manager.add_task('bandpass_filter')
        self.task_manager.add_task('mean_projection_frame')
        self.task_manager.add_task('motion_correct')

    def start_cnmfe(self):
        self.task_manager.add_task('cnmfe_apply', int(self.celldiameterspin.value()))

    def start_cell_export(self):
        self.task_manager.add_task('export_cell_set_to_tiff')
        self.task_manager.add_task('event_detection_auto_classification')
        self.task_manager.add_task('deconvolve_cells', float(self.snrspinbox.value()))
        self.task_manager.add_task('export_spike_events_to_csv')
        self.task_manager.add_task('vertical_csv_alignment')

    def start_longitudinal_registration(self):
        self.eevee_gif = GIFPopup(r'GUI images\eevee.gif', parent=self)
        self.task_manager.add_task('calculate_dff')
        self.task_manager.add_task('longitudinal_registration')
        self.task_manager.add_task('store_cnmfe_cellset_output')
        self.task_manager.add_task('rename_cells_from_timeseries')

        
    #events when 'preprocess' snorlax button is clicked
    def on_process_button_click(self):
        can_start = self.timeseries_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                self.running = True
                # show dialog 
                self.start_timeseries()   
                self.task_manager.snorlax_closed.connect(self.prepro_finish)
                self.task_manager.jiggly_closed.connect(self.cnmfe_finish)
                self.task_manager.bulbasaur_closed.connect(self.export_finished)
                #self.task_manager.tasks_completed.connect(self.process_finish)
                self.start_preprocess()
                self.start_cnmfe()
                self.start_cell_export()
                self.task_manager.start_tasks()
                self.snorlax_gif.show()
            elif self.running:
                self.show_error_message('ERROR: process still running.')
                return
        except Exception as e:
            self.show_error_message(f'ERROR: {e}')
            traceback.print_exc()
            return
    
    def on_lr_button_click(self):
        can_start = self.longitudinal_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                self.running = True
                # show dialog    
                self.task_manager.eevee_closed.connect(self.lr_finish)
                self.task_manager.meowth_closed.connect(self.rename_finish)
                self.start_longitudinal_registration()
                self.task_manager.start_tasks()
                self.eevee_gif.show()
            elif self.running:
                self.show_error_message('ERROR: process still running.')
                return
        except Exception as e:
            self.show_error_message(f'ERROR: {e}')
            traceback.print_exc()
            return
        
        #display error
    def show_error_message(self, message):
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle('Error')
        error_dialog.setText(message)
        font = QFont("Cascadia Code", 9)
        error_dialog.setFont(font)
        error_dialog.setStyleSheet('background-color: #7d0b02')
        error_dialog.exec_()

    #show pop-up dialog boxes
    def show_complete_dialog(self, message):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle('Message')
        msg_box.setText(message)
        msg_box.setStyleSheet('background-color: #d2c5db')
        font = QFont("Cascadia Code", 9)
        msg_box.setFont(font)
        msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_box.exec_()

    #use to open file explorer to select input dir file
    def open_dir_dialog(self):
        options = QFileDialog.Options() 
        options |= QFileDialog.ReadOnly
        #set F drive as default, this 3rd argument can be changed to open the default directory
        self.dir_path= QFileDialog.getExistingDirectory(self, "Open Dictionary", "F:", options=options)
        if self.dir_path:
            self.inputdirtext.setText(self.dir_path)

    @Slot()
    def prepro_finish(self):
        self.snorlax_gif.close_dialog()
        self.jiggly_gif = GIFPopup(r"GUI images\jiggly.gif", parent=self)
        self.jiggly_gif.show()
        self.task_manager.snorlax_closed.disconnect(self.prepro_finish)

    @Slot()
    def frames_dropped_finish(self):
        self.running = False
        self.slowpoke_gif.close_dialog()
        self.show_complete_dialog("Corrupt frames dropped!")
        self.task_manager_dropped_frames.tasks_completed.disconnect(self.frames_dropped_finish)

    @Slot()
    def cnmfe_finish(self):
        print('is this being emitted')
        self.jiggly_gif.close_dialog()
        self.bulbasaur_gif = GIFPopup(r"GUI images\bulbasaur.gif", parent=self)
        self.bulbasaur_gif.show()
        self.task_manager.jiggly_closed.disconnect(self.cnmfe_finish)

    @Slot()
    def export_finished(self):
        self.bulbasaur_gif.close_dialog()
        self.show_complete_dialog("Processing completed!")
        self.running = False
        self.task_manager.bulbasaur_closed.disconnect(self.export_finished)

    #@Slot()
    #def process_finish(self):
    #    self.running = False
    #    self.task_manager.tasks_completed.disconnect(self.process_finish)
    
    @Slot()
    def lr_finish(self):
        self.eevee_gif.close_dialog()
        self.meowth_gif = GIFPopup(r'GUI images\meowth.gif', parent=self)
        self.meowth_gif.show()
        self.task_manager.eevee_closed.disconnect(self.lr_finish)

    @Slot()
    def rename_finish(self):
        self.meowth_gif.close_dialog()
        self.show_complete_dialog('Longitudinal registration complete!')
        self.running = False
        self.task_manager.meowth_closed.disconnect(self.rename_finish)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = TimeseriesUI()
    mainWindow.show()
    sys.exit(app.exec_())