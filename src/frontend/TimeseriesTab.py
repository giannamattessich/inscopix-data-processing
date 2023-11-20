import traceback
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QHBoxLayout
from PyQt5.QtCore import QSize, pyqtSlot as Slot, Qt
from src.workutils.TaskManager import TaskManager
from src.frontend.ImageButton import ImageButton
from src.frontend.GIFPopup import GIFPopup
from PyQt5.QtGui import QPixmap, QFont
from src.backend.Timeseries import Timeseries

class TimeseriesTab(QWidget):

    def  __init__(self):
        super(TimeseriesTab, self).__init__()
        loadUi(r"src\frontend\timeseries_widget.ui", self)
        self.task_manager = TaskManager(self)
        self.prepro_button = ImageButton(QPixmap(r"GUI images\snorlax.webp")) 
        self.prepro_button.setMaximumSize(QSize(280, 200))
        self.cnmfe_button = ImageButton(QPixmap(r"GUI images\jigglypuff.png"))
        self.cnmfe_button.setMaximumSize(QSize(280, 200))
        self.export_button = ImageButton(QPixmap(r"GUI images\bulbasaur.png"))
        self.export_button.setMaximumSize(QSize(280,200))

        self.tpdownsamplespin.setValue(2)
        self.spdownsamplespin.setValue(4)
        self.tp_value = self.tpdownsamplespin.value()
        self.sp_value = self.spdownsamplespin.value()

        self.inputdirbutton.clicked.connect(self.open_dir_dialog)
        self.prepro_button.clicked.connect(self.on_prepro_click)
        self.cnmfe_button.clicked.connect(self.on_cnmfe_click)
        self.export_button.clicked.connect(self.on_export_click)

        self.inputdirtext.textChanged.connect(self.set_timeseries_object)
        self.outputfoldertext.textChanged.connect(self.set_timeseries_object)

        self.horizontalLayout.addWidget(self.prepro_button)
        self.horizontalLayout.addWidget(self.cnmfe_button)
        self.horizontalLayout.addWidget(self.export_button)
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)


        self.running = False
        self.main_dir_selected = False
        self.output_dir_selected = False


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
            self.input_dir = self.inputdirtext.text()
            self.main_dir_selected = True
            

    @Slot()
    # create a timeseries object to perform operations on when a main_dir is selected based on user input 
    def set_timeseries_object(self):
        self.output_folder = self.outputfoldertext.text()
        if (len(self.output_folder) > 0):
            self.output_dir_selected = True

    # determines if processes can be started based on if input/output dirs were selected and if the processing has been instantiated
    def timeseries_set(self): 
        # check if both input and outputs selected 
        if (not self.main_dir_selected) | (not self.output_dir_selected):
            self.show_error_message('ERROR: Input directory or output folder have not been selected ')
            return False
        # check if process already started
        elif (hasattr(self, 'timeseries_process_object')):
            return True
        else:
            try:
                self.timeseries_process_object = Timeseries(self.input_dir, self.output_folder)
                self.task_manager.set_process_object(self.timeseries_process_object)
                self.series_recs = self.timeseries_process_object.series_rec_names
                self.num_days = len(self.series_recs)
                return True
            except ValueError:
                self.show_error_message('Could not find recording files in the selected input directory. Please check that .isxd files are in year-month-day-hour-minute-second format to continue.')
                self.inputdirtext.setText('')
                self.main_dir_selected = False
                return False
            
    def start_timeseries(self):
        if self.main_dir_selected and self.output_dir_selected:
            self.recording_names = sorted(list(set([recording for recordings in self.series_recs.values() for recording in recordings])))
            
            # Flatten the list of lists into a single list of strings
            recordings_to_process = [recording for recordings in self.series_recs.values() for recording in recordings]
            
            # Join the list of strings
            recordings_to_process_str = (', ').join(recordings_to_process)
            
            days_to_process = (', ').join(list(self.series_recs.keys()))
            self.show_complete_dialog(f"Preprocessing has begun!\nDays: {days_to_process}\nRecordings: {recordings_to_process_str}")


    #events when 'preprocess' snorlax button is clicked
    def on_prepro_click(self):
        can_start = self.timeseries_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                self.running = True
                # show dialog 
                self.start_timeseries()   
                # add tasks to queue
                self.task_manager.add_task('preprocess', self.tp_value, self.sp_value)
                self.task_manager.add_task('bandpass_filter')
                self.task_manager.add_task('mean_projection_frame')
                self.task_manager.add_task('motion_correct')
                self.task_manager.start_tasks()
                # create GIF dialog to play 
                self.snorlax_gif = GIFPopup(r'GUI images\snorlax.gif', parent=self)
                self.snorlax_gif.show()
                self.task_manager.tasks_completed.connect(self.prepro_finish)
            elif self.running:
                self.show_error_message('ERROR: process still running.')
                return
        except Exception as e:
            self.show_error_message(f'ERROR: {e}')
            traceback.print_exc()
            return
    
    def on_cnmfe_click(self):
        can_start = self.timeseries_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                # make sure that previous preprocessing tasks have been completed 
                if (self.timeseries_process_object.check_all_recordings_processed(self.timeseries_process_object.mc_files_series, self.num_days - 1)):
                    self.running = True
                    self.show_complete_dialog('Applying CNMFe...')
                    # add task to queue
                    self.task_manager.add_task('cnmfe_apply')
                    self.task_manager.start_tasks()
                    self.jiggly_gif = GIFPopup(r'GUI images\jiggly.gif', parent=self)
                    self.jiggly_gif.show()
                    self.task_manager.tasks_completed.connect(self.cnmfe_finish)
                else:
                    self.show_error_message("ERROR: previous steps have not yet been completed")
                    return
            elif self.running:
                self.show_error_message("ERROR: process still running")
                return
        except Exception as e:
            self.show_error_message(f"ERROR:{e}")
            traceback.print_exc()
            return

    def on_export_click(self):
        can_start = self.timeseries_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                if (self.timeseries_process_object.check_all_recordings_processed(self.timeseries_process_object.cnmfe_files_series, self.num_days - 1)):
                    self.running = True
                    self.show_complete_dialog('Exporting spikes...')
                    self.task_manager.add_task('export_cell_set_to_tiff')
                    self.task_manager.add_task('event_detection_auto_classification')
                    self.task_manager.add_task('deconvolve_cells')
                    self.task_manager.add_task('export_spike_events_to_csv')
                    self.task_manager.add_task('vertical_csv_alignment')
                    self.task_manager.start_tasks()
                    self.bulbasaur_gif = GIFPopup(r'GUI images\bulbasaur.gif', parent=self)
                    self.bulbasaur_gif.show()
                    self.task_manager.tasks_completed.connect(self.export_finish)
                else:
                    self.show_error_message("ERROR: previous steps have not yet been completed.")
                    return
            else:
                self.show_error_message('ERROR: process still running')
                return
        except Exception as e:
            self.show_error_message(f"ERROR:{e}")
            traceback.print_exc()
            return

    @Slot()
    def prepro_finish(self):
        self.snorlax_gif.close_dialog()
        self.show_complete_dialog('Preprocess, bandpass, and motion correction complete!')
        self.running = False
        self.task_manager.tasks_completed.disconnect(self.prepro_finish)

    
    @Slot()
    def cnmfe_finish(self):
        self.jiggly_gif.close_dialog()
        self.show_complete_dialog('CNMFe complete!')
        self.running = False
        self.task_manager.tasks_completed.disconnect(self.cnmfe_finish)

    @Slot()
    def export_finish(self):
        self.bulbasaur_gif.close_dialog()
        self.show_complete_dialog('Spike event export complete!')
        self.running = False
        self.task_manager.tasks_completed.disconnect(self.export_finish)
    
        # set all buttons to either enabled or disabled
    def set_buttons_status(self, bool):
        self.cnmfe_button.setEnabled(bool)
        self.export_button.setEnabled(bool)
        self.prepro_button.setEnabled(bool)    



