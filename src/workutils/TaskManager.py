from PyQt5.QtCore import Qt, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QThreadPool
from src.workutils.WorkerThread import Worker
from src.backend.Timeseries import Timeseries
from src.backend.LongitudinalRegistration import LongitudinalRegistration
from typing import Type

# # class to handle the execution of tasks in the queue sequentially-> set up finished signal
class TaskManager(QObject):
    snorlax_closed = Signal()
    jiggly_closed = Signal()
    bulbasaur_closed = Signal()
    eevee_closed = Signal()
    meowth_closed = Signal()
    # setup finished signal
    tasks_completed = Signal()
    

# initialize queue and index of tasks
    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self.task_queue = [] # queue
        self.current_task_index = 0
        self.process_object = None
        self.workers = []
        
# set the type of data process object to perform on-> either timeseries or longitudinal process
    def set_process_object(self, process_object):
        self.process_object = process_object


# add the function name and optional arguments to the queue 
    def add_task(self, method_name, *args, **kwargs):
        self.task_queue.append((method_name, args, kwargs))

# start at beginning of queue and execute task
    def start_tasks(self):
        self.current_task_index = 0
        self.execute_next_task()
    
    def check_process_attributes(self, attribute_type: Type, target_class: Type) -> bool:
        return attribute_type == target_class


# for each task construct a worker object that will execute the run function
# setup finished signal (queued connection) to be emitted when worker is finished with task
# start thread from global thread pool 
# if at end of queue emit tasks_completed signal
# for each step in task queue index is checked to see if it corresponds with a signal to be emitted at that task -> used for signaling GIF closings
    def execute_next_task(self):
        if self.current_task_index < len(self.task_queue):
            method_name, args, kwargs = self.task_queue[self.current_task_index]
            worker = Worker(self.process_object, method_name, *args, **kwargs)
            worker.signals.finished.connect(self.on_task_finished, Qt.QueuedConnection)
            QThreadPool.globalInstance().start(worker)
            if self.current_task_index == 2:
                self.eevee_closed.emit()
            elif self.current_task_index == 4:
                 self.snorlax_closed.emit()
            elif self.current_task_index == 5:
                self.jiggly_closed.emit()
        else:
            # All tasks completed
            self.tasks_completed.emit()
            self.bulbasaur_closed.emit()
            self.meowth_closed.emit()
            self.task_queue.clear()

# hook up finished signal to slot for task and execute next task in queue
    @Slot()
    def on_task_finished(self):
        self.current_task_index += 1
        self.execute_next_task()



    












