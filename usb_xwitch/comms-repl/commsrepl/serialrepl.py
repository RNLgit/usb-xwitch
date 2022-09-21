import serial
from threading import Thread, Event
from queue import deque
import time

RX_Q_LINES_TIMEOUT = 3  # Max expected return lines timeout from REPL
EOL = bytes('\r\n'.encode())
END = '>>> '
CR = bytes('\r'.encode())
NL = bytes('\n'.encode())
INPUT_SIGN = bytes('>>> '.encode())


class SerialREPL(object):
    def __init__(self, port_name: str, baud=115200):
        self.serial = serial.Serial(port_name, baudrate=baud, timeout=0)
        if not self.serial.isOpen():
            self.serial.open()
        self.rx_queue = deque(maxlen=10)
        self.rx_th = Thread(target=self.__rx_thread, args=())
        self.rx_th.start()

    def __is_cr_nl_consecutive(self, income_byte: bytes) -> bool:
        """
        check if \r\n received in sequence. i.e. end of a return text line
        :param income_byte:
        """
        self._eol_bytes += income_byte
        if len(self._eol_bytes) < 2:
            return False
        elif len(self._eol_bytes) == 2:
            if self._eol_bytes == EOL:
                self._eol_bytes = bytes()
                return True
            else:
                self._eol_bytes = bytes()
                return False
        else:
            self._eol_bytes = bytes()
            return False

    def __is_input_sign(self, income_byte: bytes) -> bool:
        """
        check if a python input sign received. i.e. >>> sign received. normally indicates that REPL finished text return
        :param income_byte:
        """
        self._input_sign_bytes += income_byte
        if self._input_sign_bytes == INPUT_SIGN:
            self._input_sign_bytes = bytes()
            return True
        elif len(self._input_sign_bytes) > len(INPUT_SIGN):
            self._input_sign_bytes = bytes()
            return False
        return False

    def __rx_thread(self):
        """
        Serial communication receive handling thread
        """
        while self.serial.isOpen():
            if self.serial.inWaiting() > 0:
                ts = time.time()
                line_byte = bytes()
                self._eol_bytes = bytes()
                self._input_sign_bytes = bytes()
                while time.time() - ts < RX_Q_LINES_TIMEOUT and self.serial.inWaiting() > 0:
                    byte_read = self.serial.read()
                    line_byte += byte_read
                    if byte_read in [CR, NL] and self.__is_cr_nl_consecutive(byte_read):
                        self.rx_queue.append(line_byte)
                        break
                    if byte_read in INPUT_SIGN and self.__is_input_sign(byte_read):
                        self.rx_queue.append(line_byte)
                        break

    def close(self) -> None:
        self.serial.close()

    def send(self, cmd: str):
        return self.serial.write(f'{cmd}\r\n'.encode())

    def __del__(self):
        self.close()
