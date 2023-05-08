import logging
import time
import re
import subprocess
import os
from typing import Optional

import fastasr
import numpy as np
from numpy._typing import NDArray


class Recorder:

    def __init__(self,
                 pipe_file_path: str = "/tmp/snapfifo",
                 target_source: Optional[str] = None):
        """
        :param pipe_file_path: pipe文件位置
        :param target_source: 需录制的流名称
        """
        self.connected_source = None
        self._module_id = None
        self._pipefile_path = pipe_file_path

        self.destroy()
        time.sleep(1)
        self._module_id = self._load_module(pipe_file_path)

        if target_source:
            self.link_source(target_source)

    def _load_module(self, pipe_file_path: str) -> int:
        proc = subprocess.run([
            "pactl", "load-module", "module-pipe-sink",
            f"file={pipe_file_path}", "sink_name=snapcast", "format=s16le",
            "rate=16000", "channels=1"
        ],
                              stdout=subprocess.PIPE,
                              check=True)
        return int(proc.stdout)

    @classmethod
    def get_all_source(cls) -> list[str]:
        """获取所有音频流"""
        pout = subprocess.run(["pw-link", "-o"],
                              stdout=subprocess.PIPE).stdout.decode("UTF-8")
        output_re = re.compile("^(.+?):output_FL$", re.M)
        return re.findall(output_re, pout)

    def link_source(self, target_source):
        """连接到音频流"""
        subprocess.run([
            "pw-link", f"{target_source}:output_FL", "snapcast:playback_MONO"
        ],
                       check=True)
        subprocess.run([
            "pw-link", f"{target_source}:output_FR", "snapcast:playback_MONO"
        ],
                       check=True)
        self.connected_source = target_source

    def unlink_source(self, target_source=None):
        """断开音频流"""
        if not target_source:
            if not self.connected_source:
                return
            target_source = self.connected_source
        subprocess.run([
            "pw-link", "-d", f"{target_source}:output_FL",
            "snapcast:playback_MONO"
        ],
                       check=True)
        subprocess.run([
            "pw-link", "-d", f"{target_source}:output_FR",
            "snapcast:playback_MONO"
        ],
                       check=True)
        self.connected_source = None

    def record(self, second: int) -> NDArray:
        '''录制指定长度音频并转换为numpy array'''
        with open(self._pipefile_path, "rb") as fp:
            # channels=1 * sample_rate=16000 * sample_width=2 * second
            read_bytes = int(32000 * second)
            read_bytes = (read_bytes // Recognizer.ALIGN_SIZE +
                          1) * Recognizer.ALIGN_SIZE
            data = np.frombuffer(fp.read(read_bytes), dtype=np.int16)
            logging.debug(f"read data length: {data.size}")
        return data

    def write_dummy_data(self, second: int):
        """"""
        try:
            with open(self._pipefile_path, "ab") as fp:
                fp.write(bytearray(64000 * second))
        except Exception as e:
            logging.error(e)

    def destroy(self):
        """断开流并卸载模块"""
        if self.connected_source:
            self.unlink_source(self.connected_source)
        if self._module_id:
            subprocess.run(["pactl", "unload-module",
                            str(self._module_id)],
                           check=True)
        else:
            subprocess.run(["pactl", "unload-module", "module-pipe-sink"],
                           check=False)


class Recognizer:
    ALIGN_SIZE = 1360

    def __init__(self, model_path: str):
        if not os.path.exists(model_path):
            raise FileNotFoundError('model path is not exists')
        logging.info("start loading model")
        self._model = fastasr.Model(model_path, 1)
        logging.info("model loaded")
        self._model.reset()

    def recognize(self, data: NDArray) -> str:
        msg = self._model.forward_chunk(data, 1)
        logging.debug("Current Result: '{}'".format(msg))
        return msg

    def recognize_final(self, data: NDArray) -> str:
        msg = self._model.forward_chunk(data, 2)
        logging.debug("Current Result: '{}'".format(msg))
        msg = self._model.rescoring()
        logging.debug("Final Result: '{}'".format(msg))
        self._model.reset()
        return msg
