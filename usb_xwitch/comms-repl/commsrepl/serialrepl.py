import serial
from threading import Thread, Event
from queue import deque
import time

RX_Q_LINES_TIMEOUT = 3  # Max expected return lines timeout from REPL
EOL = '\r\n'
END = '>>> '
CR = bytes('\r'.encode())
NL = bytes('\n'.encode())
INPUT = bytes('>>> '.encode())


class SerialREPL(object):
    def __init__(self, port_name: str, baud=115200):
        self.serial = serial.Serial(port_name, baudrate=baud, timeout=0)
        if not self.serial.isOpen():
            self.serial.open()
        self.rx_queue = deque(maxlen=5)
        self.rx_th = Thread(target=self.__rx_thread, args=())
        self.rx_th.start()

    def __is_cr_nl_consecutive(self, income_byte: bytes):
        self._eol_bytes += income_byte
        if len(self._eol_bytes) < 2:
            return False
        elif len == 2:
            if self._eol_bytes == CR + NL:
                self._eol_bytes = bytes()
                return True
            else:
                self._eol_bytes = bytes()
                return False
        else:
            self._eol_bytes = bytes()
            return False

    def __is_input(self, income_byte: bytes):
        pass

    def __rx_thread(self):
        while self.serial.isOpen():
            if self.serial.inWaiting() > 0:
                ts = time.time()
                line_byte = bytes()
                self._eol_bytes = bytes()
                self._input_bytes = bytes()
                while time.time() - ts < RX_Q_LINES_TIMEOUT:
                    byte_read = self.serial.read()
                    line_byte += byte_read
                    if byte_read in [CR, NL] and self.__is_cr_nl_consecutive(byte_read):
                        break
                    if byte_read in INPUT and self.__is_input(byte_read):
                        break

    def close(self):
        self.serial.close()

    def __del__(self):
        self.close()
