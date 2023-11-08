import os
import traceback
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import QFileDialog, QMessageBox, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, QSize, pyqtSlot as Slot
from src.workutils.TaskManager import TaskManager
from src.frontend.ImageButton import ImageButton
from src.frontend.GIFPopup import GIFPopup
from PyQt5.QtGui import QPixmap, QFont
from src.backend.LongitudinalRegistration import LongitudinalRegistration
#from ..backend.LongitudinalRegistration import LongitudinalRegistration

class LongitudinalTab(QWidget):
    
    def  __init__(self):
        super(LongitudinalTab, self).__init__()
        loadUi(r"src\frontend\longitudinal_widget.ui", self)
        self.task_manager = TaskManager(self)
        self.lr_button = ImageButton(QPixmap(r"GUI images\eevee.webp")) 
        self.rename_button = ImageButton(QPixmap(r"GUI images\meowth.webp")) 

        self.horizontalLayout.addWidget(self.lr_button)
        self.horizontalLayout.addWidget(self.rename_button)
        self.inputdirbutton.clicked.connect(self.open_dir_dialog)

        #self.inputdirtext.textChanged.connect(self.set_lr_object)
        self.lr_button.clicked.connect(self.on_lr_click)
        self.rename_button.clicked.connect(self.on_rename_click)

        self.lr_button.setMaximumSize(QSize(300, 280))
        self.rename_button.setMaximumSize(QSize(300, 280))
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)
        self.running = False
        self.main_dir_selected = False

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


    # determines if processes can be started based on if input dirs were selected and if the processing has been instantiated
    def longitudinal_set(self): 
        # check if both input and outputs selected 
        if (not self.main_dir_selected):
            self.show_error_message('ERROR: Input directory or output folder have not been selected ')
            return False
        # check if process already started
        elif (hasattr(self, 'longitudinal_process_object')):
            return True
        else:
            try:
                self.user_input_dir = self.inputdirtext.text()
                self.input_dir = os.path.dirname(self.user_input_dir)
                self.output_folder = os.path.basename(self.user_input_dir)
                self.longitudinal_process_object = LongitudinalRegistration(self.input_dir, self.output_folder)
                self.task_manager.set_process_object(self.longitudinal_process_object)
                self.series_recs = self.longitudinal_process_object.series_rec_names
                self.num_days = len(self.series_recs)
                # ensure folder has at least 2 days 
                if len(self.series_recs) < 2:
                    self.show_error_message("ERROR: Input Directory contains less than 2 files. Please input a directory that contains recordings for at least 2 days.")
                    self.main_dir_selected = False
                    self.inputdirtext.setText('')
                    del self.longitudinal_process_object
                    return False
                else:
                    return True 
            except ValueError:
                self.show_error_message('Could not find recording files in the selected input directory. Please check that .isxd files are in year-month-day-hour-minute-second format to continue.')
                self.inputdirtext.setText('')
                self.main_dir_selected = False
                return False
            
    def start_lr(self):
        if self.main_dir_selected:
            self.recording_names = sorted(list(set([recording for recordings in self.series_recs.values() for recording in recordings])))
            
            # Flatten the list of lists into a single list of strings
            recordings_to_process = [recording for recordings in self.series_recs.values() for recording in recordings]
            
            # Join the list of strings
            recordings_to_process_str = (', ').join(recordings_to_process)
            
            days_to_process = (', ').join(list(self.series_recs.keys()))
            self.show_complete_dialog(f"Longitudinal Registration has begun!\nDays: {days_to_process}\nRecordings: {recordings_to_process_str}")


    def on_lr_click(self):
        can_start = self.longitudinal_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                if (self.longitudinal_process_object.check_all_recordings_processed(self.longitudinal_process_object.mc_files_series, self.num_days - 1)):
                    self.running = True
                    # show dialog 
                    self.start_lr()   
                    # add tasks to queue
                    self.task_manager.add_task('calculate_dff')
                    self.task_manager.add_task('longitudinal_registration')
                    self.task_manager.start_tasks()
                    # create GIF dialog to play 
                    self.eevee_gif = GIFPopup(r'GUI images\eevee.gif', parent=self)
                    self.eevee_gif.show()
                    self.task_manager.tasks_completed.connect(self.lr_finish)
                else:
                    self.show_error_message('"ERROR: previous steps have not yet been completed"')
            elif self.running:
                self.show_error_message('ERROR: process still running.')
                return
        except Exception as e:
            self.show_error_message(f'ERROR: {e}')
            traceback.print_exc()
            return
    
    def on_rename_click(self):
        can_start = self.longitudinal_set()
        if not can_start:
            return
        try:
            if (not self.running & can_start):
                # make sure that previous preprocessing tasks have been completed 
                if os.path.exists(self.longitudinal_process_object.lr_csv_file):
                    self.running = True
                    self.show_complete_dialog('Renaming cellset...')
                    # add task to queue
                    self.task_manager.add_task('store_cnmfe_cellset_output')
                    self.task_manager.add_task('rename_cells_from_timeseries')
                    self.task_manager.start_tasks()
                    self.meowth_gif = GIFPopup(r'GUI images\meowth.gif', parent=self)
                    self.meowth_gif.show()
                    self.task_manager.tasks_completed.connect(self.rename_finish)
                else:
                    self.show_error_message("ERROR: longitudinal registration has not yet been completed or an error occured while creating.")
            elif self.running:
                self.show_error_message("ERROR: process still running")
        except Exception as e:
            self.show_error_message(f'ERROR: {e}')
            traceback.print_exc()
            return

    @Slot()
    def lr_finish(self):
        self.eevee_gif.close_dialog()
        self.show_complete_dialog('Longitudinal registration complete!')
        self.running = False
        self.task_manager.tasks_completed.disconnect(self.lr_finish)

    @Slot()
    def rename_finish(self):
        self.meowth_gif.close_dialog()
        self.show_complete_dialog('Cellset output complete!')
        self.running = False
        self.task_manager.tasks_completed.disconnect(self.rename_finish)
