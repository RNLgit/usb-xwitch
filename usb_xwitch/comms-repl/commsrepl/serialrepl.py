import serial
from threading import Thread, Event
from queue import deque


class SerialREPL(object):
    def __init__(self, port_name: str, baud=115200):
        self.serial = serial.Serial(port_name, baudrate=baud, timeout=0)
        if not self.serial.isOpen():
            self.serial.open()
        self.rx_queue =
        self.rx_th = Thread(target=self.__rx_thread, args=())

    def __rx_thread(self):
        while self.serial.isOpen():
            pass
