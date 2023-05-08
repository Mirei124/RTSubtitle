import logging
import queue
import threading
import time

from .recognize import Recognizer, Recorder


class Manager:

    def __init__(self, per_record_second: int | float, reco_nums: int,
                 model_path: str, target_source: str):
        self.per_record_second = per_record_second
        self.reco_nums = reco_nums

        self._recorder = Recorder(target_source=target_source)
        self._recognizer = Recognizer(model_path)
        self._record_thread = None
        self._recog_thread = None

        self._wav_queue = queue.Queue(10)
        self.is_running = False

        self.last_result = ""
        self.current_result = ""

    def _record_task(self):
        logging.debug("start record task")
        while self.is_running:
            data = self._recorder.record(self.per_record_second)
            try:
                self._wav_queue.put(data, block=False)
            except queue.Full:
                logging.info("wav queue is full")
        logging.debug("quit record task")

    def _recognize_task(self):
        logging.debug("start recognize task")
        align_size = Recognizer.ALIGN_SIZE
        recog_count = 0
        while self.is_running:
            try:
                data = self._wav_queue.get(block=True,
                                           timeout=self.per_record_second * 2)
            except queue.Empty:
                logging.info("wav queue is empty")
                continue

            recog_count += 1
            if recog_count % self.reco_nums == 0:
                for i in range(0, data.size - align_size, align_size):
                    self._recognizer.recognize(data[i:i + align_size])
                self.last_result = self._recognizer.recognize_final(
                    data[-align_size])
                self.current_result = ""
            else:
                msg = ""
                for i in range(0, data.size, align_size):
                    msg = self._recognizer.recognize(data[i:i + align_size])
                self.current_result = msg
        logging.debug("quit recognize task")

    def run(self):
        self.is_running = True
        self._record_thread = threading.Thread(target=self._record_task,
                                               daemon=True)
        self._recog_thread = threading.Thread(target=self._recognize_task,
                                              daemon=False)
        self._record_thread.start()
        self._recog_thread.start()

    def switch_source(self, new_source: str):
        if not new_source:
            return
        if new_source == self._recorder.connected_source:
            return
        self._recorder.unlink_source()
        time.sleep(1)
        self._recorder.link_source(new_source)

    def stop(self):
        self.is_running = False
        self._recorder.write_dummy_data(int(self.per_record_second) + 1)

    def destroy(self):
        if self.is_running:
            raise Exception("please stop task first")
        self._recorder.destroy()
