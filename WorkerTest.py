# from PyQt5.QtCore import Qt, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QThreadPool, QRunnable

# # setup trigger signal for tasks 
# class TriggerSignals(QObject):
#     finished = Signal()
#     stop = Signal()

# # worker thread -> takes in either timeseries or longitudinal process object, its method to be called
# # in a string, and optional arguments to the function
# class Worker(QRunnable):
#     def __init__(self, process_object, method_name, *args, **kwargs):
#         super(Worker, self).__init__()
#         self.process_object = process_object
#         self.method_name = method_name
#         self.args = args
#         self.kwargs = kwargs
#         self.signals = TriggerSignals()

# # override of QRunnable run method
# # execute function provided in constructor and emit finished signal from this slot once it is done
#     @Slot()
#     def run(self):
#         func = getattr(self.process_object, self.method_name, None)
#         if func is not None and callable(func):
#             func(*self.args, **self.kwargs)
#             self.signals.finished.emit()
#             print(f'function {self.method_name} called!')
#         else:
#             raise ValueError(f"Method '{self.method_name}' was not found or is not callable on the given object.")
    
#     # @Slot()
#     # def stop_processing(self):
#     #     self.signals.stop.emit()

# # class to handle the execution of tasks in the queue-> set up finished signal
# class TaskManager(QObject):
#     tasks_completed = Signal()
# # initialize queue and index of tasks
#     def __init__(self, parent=None):
#         super(TaskManager, self).__init__(parent)
#         self.task_queue = [] # queue
#         self.current_task_index = 0
#         self.process_object = None
        
# # set the type of data process object to perform on-> either timeseries or longitudinal process
#     def set_process_object(self, process_object):
#         self.process_object = process_object
# # add the function name and optional arguments to the queue 
#     def add_task(self, method_name, *args, **kwargs):
#         self.task_queue.append((method_name, args, kwargs))
# # start at beginning of queue and execute task
#     def start_tasks(self):
#         self.current_task_index = 0
#         self.execute_next_task()
# # for each task construct a worker object that will execute the run function
# # setup finished signal (queued connection) to be emitted when worker is finished with task
# # start thread from global thread pool 
# # if at end of queue emit tasks_completed signal
#     def execute_next_task(self):
#         if self.current_task_index < len(self.task_queue):
#             method_name, args, kwargs = self.task_queue[self.current_task_index]
#             worker = Worker(self.process_object, method_name, *args, **kwargs)
#             worker.signals.finished.connect(self.on_task_finished, Qt.QueuedConnection)
#             #worker.signals.stop.connect(worker.stop_processing, Qt.QueuedConnection) 
#             QThreadPool.globalInstance().start(worker)
#         else:
#             # All tasks completed
#             self.tasks_completed.emit()

# # hook up finished signal to slot for task and execute next task in queue
#     @Slot()
#     def on_task_finished(self):
#         self.current_task_index += 1
#         self.execute_next_task()
        
#     def stop_tasks(self):
#         QThreadPool.globalInstance().clear()
#         self.tasks_completed.emit()

#     def reset_tasks(self):
#         self.task_queue.clear()
#         self.current_task_index = 0

#     # def stop_all_workers(self):
#     #     QThreadPool.globalInstance().clear()
#     #     self.tasks_completed.emit()
