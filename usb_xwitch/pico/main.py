from machine import Pin, ADC, UART, I2C
from conf import HUBAddr
import time
from collections import deque
import _thread

__version__ = '0.2'

HIGH = 1
LOW = 0

IND_LED = 25  # Indicator LED, Using same pin as Pico board default led
# Switch Pins
PD_U2 = 8  # PD (power down) USB2 Mux pin
SEL_U2 = 9  # SEL (selection) USB2 Mux pin
PD_U3 = 10  # PD (power down) USB3 Mux pin
SEL_U3 = 11  # SEL (selection) USB3 Mux pin
SW_REL = 19  # Switch channel power switching pin
SW_MAN = 7  # Manual channel switch pin
# HUB Pins
HUB_RST = 18  # HUB IC RESETn control
HUB_SCL = 17
HUB_SDA = 16
# Comms
UART_U_TX = 0  # UART upstream tx
UART_U_RX = 1  # UART upstream rx
UART_D_TX = 4  # UART downstream tx
UART_D_RX = 5  # UART downstream rx
UART_BAUD = 9600  # UART default baud rate
# ADC Pins
ADC_1_1 = 26  # CHA mus 2-1 VBus voltage
ADC_1_2 = 27  # CHA mus 2-2 VBus voltage
# Conversion
ADC_RATIO = 18/33  # ADC voltage divider ratio
ADC_REF_V = 3.3  # ADC reference voltage
# Software params
Q_LEN = 10
DATA_SIZE = 20  # data payload read size

led_ind_stat = False


def _intr_flip_pico_led(pin) -> None:
    pass


def ind_led(en: bool) -> None:
    """
    toggle on off of pico onboard led
    """
    _led_ind.value(en)


def flip_indicator_led() -> None:
    """
    flip indicator led status
    """
    global led_ind_stat
    led_ind_stat = not led_ind_stat
    ind_led(led_ind_stat)


def get_adc(no: int) -> float:
    """
    get adc reading from adc channel
    """
    adc = {1: _adc_a1, 2: _adc_a2}
    if adc.get(no) is None:
        raise ValueError(f'adc {no} invalid')
    return adc.get(no).read_u16() * ADC_REF_V / 65536 / ADC_RATIO


def set_switch(ch_no: int) -> None:
    """
    set usb switch position. switch to 1 or 2
    """
    if ch_no not in [1, 2]:
        raise ValueError(f'cannot switch cha to port {ch_no}. Only 2 channels supported')
    _sw2_sel.value(ch_no - 1)
    _sw3_sel.value(ch_no - 1)
    _sw_rel.value(ch_no - 1)


def get_switch() -> int:
    """
    get current usb switch position. Expect 1 or 2.
    """
    switch_ctrl = [_sw2_sel.value(), _sw3_sel.value(), _sw_rel.value()]
    if len(set(switch_ctrl)) > 1:  # if not all 0 or all 1
        raise ValueError(f'internal error. ICs selection or Relay selection error. sel_2, sel_3, rel: {switch_ctrl}')
    return switch_ctrl[1] + 1  # return any value from switch list


def set_hub(on_off_lst: list) -> None:
    """
    set usb hub channels using a list of bool values.
    e.g. set_hub([False, True, True, False]) set hub channel 2 & 3 on and 1 & 4 off
    """
    if len(on_off_lst) != 4:
        raise ValueError('on off list should be a length of 4 (channels)')
    _hub.reset()
    _hub._init_hub()
    vals = [v for k, v in zip(on_off_lst, HUBAddr.PORTS_MASK) if not k]
    _hub._bw(HUBAddr.PORT_DISABLE_SELF.addr, [sum(vals)])
    _hub.attach()


def get_hub() -> tuple:
    """
    get usb hub current channels status in tuple of bools.
    """
    data = _hub._br(HUBAddr.PORT_DISABLE_SELF.addr)[1]
    return not bool(data & HUBAddr.PORT_MSK_1), not bool(data & HUBAddr.PORT_MSK_2), \
        not bool(data & HUBAddr.PORT_MSK_3), not bool(data & HUBAddr.PORT_MSK_4)


class HUBI2C(object):
    """
    USB HUB control
    """
    MAX_BLOCK = 32  # max block read / write size for USB2514B

    def __init__(self, scl_pin=HUB_SCL, sda_pin=HUB_SDA, frequency=400000) -> None:
        self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=frequency)
        self._init_hub()
        self.attach()
    
    def _init_hub(self) -> None:
        """
        Configure hub default values. t5 stage in SMBus.
        """
        for reg2init in HUBAddr.INIT_DEFAULT:
            self._bw(reg2init.addr, [reg2init.default_val])
        for reg2init in HUBAddr.MFG_AUX_DEFAULT:
            self._bw(reg2init.addr, [reg2init.default_val])
        for mfg in HUBAddr.MFG_DEFAULT:
            self._bw_lot(mfg.addr, mfg.default_val)

    def _br(self, reg_addr: int, byte_ct=33) -> bytearray:
        """
        Block read. byte_ct max 33 (i.e. ct + max 32 bytes data)
        """
        buf_reg = bytes([reg_addr])
        self.i2c.writeto(HUBAddr.SLAVE, buf_reg, False)
        return self.i2c.readfrom(HUBAddr.SLAVE, byte_ct)

    def _bw(self, reg_addr: int, bytes2write: list) -> None:
        """
        Block write
        """
        data = [reg_addr, len(bytes2write)]
        data.extend(bytes2write)
        bw_data = bytes(data)
        self.i2c.writeto(HUBAddr.SLAVE, bw_data)

    def _bw_lot(self, ref_addr: list, bytes2write: list) -> None:
        """
        Block write a lot longer than expected
        """
        if len(bytes2write) > 32:
            chunks = [bytes2write[i : i+32] for i in range(0, len(bytes2write), 32)]
            for idx in range(len(chunks)):
                self._bw(ref_addr[idx], chunks[idx])
        else:
            self._bw(ref_addr[0], bytes2write)  # Blindly take 1st 
   
    def attach(self) -> None:
        """
        Aply hub configs and make it online
        """
        self._bw(HUBAddr.STAT_CMD.addr, [0x01])

    def reset(self, seconds=1) -> None:
        """
        Reset HUB
        """
        _hub_rst.value(HIGH)
        time.sleep(seconds)
        _hub_rst.value(LOW)
        time.sleep(seconds/2)
        self._init_hub()


class UARTController(object):
    CRC_KEY = '1101'  # polynomial x^3 + x^2 + x^0

    def __init__(self, tx_upstream: int, rx_upstream: int, tx_downstream: int, rx_downstream: int, baudrate=UART_BAUD):
        self.q_us = deque((), Q_LEN)
        self.uart_us = UART(0, baudrate=baudrate, tx=Pin(tx_upstream), rx=Pin(rx_upstream))
        self.q_ds = deque((), Q_LEN)
        self.uart_ds = UART(1, baudrate=baudrate, tx=Pin(tx_downstream), rx=Pin(rx_downstream))
        self.rx_flag = True
        self.q_lock = _thread.allocate_lock()
        _thread.start_new_thread(self.rx_thread, ())
 
    @staticmethod
    def _get_crc_field(bit_str: str, poly_str: str, init_filter_str='0') -> str:
        poly_str = poly_str.lstrip('0')
        initial_pad = (len(poly_str) - 1) * init_filter_str
        input_pad_arr = list(bit_str + initial_pad)
        while '1' in input_pad_arr[:len(bit_str)]:
            cur_shift = input_pad_arr.index('1')
            for i in range(len(poly_str)):
                input_pad_arr[cur_shift + i] = str(int(poly_str[i] != input_pad_arr[cur_shift + i]))
        return ''.join(input_pad_arr)[len(bit_str):]
    
    @staticmethod
    def _check_crc(bit_str: str, poly_str: str, crc_value: str):
        poly_str = poly_str.lstrip('0')
        input_pad_arr = list(bit_str + crc_value)
        while '1' in input_pad_arr[:len(bit_str)]:
            cur_shift = input_pad_arr.index('1')
            for i in range(len(poly_str)):
                input_pad_arr[cur_shift + i] = str(int(poly_str[i] != input_pad_arr[cur_shift + i]))
        return '1' not in ''.join(input_pad_arr)[len(bit_str):]

    def send_upstream(self, data: str) -> int:
        return self.uart_us.write(data)

    def send_downstream(self, data: str) -> int:
        return self.uart_ds.write(data)

    def rx_thread(self):
        while self.rx_flag:
            if self.uart_us.any() > 0:  # if there's any data in rx thread
                self.q_lock.acquire()
                self.q_us.append(self.uart_us.read(DATA_SIZE))
                self.q_lock.release()
            if self.uart_ds.any() > 0:
                self.q_lock.acquire()
                self.q_ds.append(self.uart_ds.read(DATA_SIZE))
                self.q_lock.release()


def version() -> str:
    return f'usb-xwitch ver:{__version__}'


_led_ind = Pin(IND_LED, Pin.OUT)
_adc_a1 = ADC(ADC_1_1)
_adc_a2 = ADC(ADC_1_2)
# switch ICs pin power up pre-condition
_sw2_pd = Pin(PD_U2, Pin.OUT)
_sw2_pd.value(LOW)
_sw2_sel = Pin(SEL_U2, Pin.OUT)
_sw3_pd = Pin(PD_U3, Pin.OUT)
_sw3_pd.value(LOW)
_sw3_sel = Pin(SEL_U3, Pin.OUT)
_sw_rel = Pin(SW_REL, Pin.OUT)
# switch manual button control pre-condition
_sw_man = Pin(SW_MAN, Pin.IN, Pin.PULL_UP)
_sw_man.irq(trigger=Pin.IRQ_FALLING, handler=_intr_flip_pico_led)
# HUB IC pin pre-condition
_hub_rst = Pin(HUB_RST, Pin.OUT)
_hub_rst.value(LOW)
# Daisy chain UART set up
_uart = UARTController(UART_U_TX, UART_U_RX, UART_D_TX, UART_D_RX)
_hub = HUBI2C()
