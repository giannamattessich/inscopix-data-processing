from PyQt5.QtCore import QObject, pyqtSignal as Signal, pyqtSlot as Slot, QRunnable

# setup trigger signal for tasks 
class TriggerSignals(QObject):
    finished = Signal()

# worker thread -> takes in either timeseries or longitudinal process object, its method to be called
# in a string, and optional arguments to the function
class Worker(QRunnable):
    def __init__(self, process_object, method_name, *args, **kwargs):
        super(Worker, self).__init__()
        self.process_object = process_object
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs
        self.signals = TriggerSignals()

# override of QRunnable run method
# execute function provided in constructor and emit finished signal from this slot once it is done
    @Slot()
    def run(self):
        func = getattr(self.process_object, self.method_name, None)
        try:
            if func is not None and callable(func):
                func(*self.args, **self.kwargs)
        except Exception as e:   
            print(f"{e}")
        self.signals.finished.emit()

    

