from machine import Pin, ADC, UART, I2C
from conf import HUBAddr, HW, DC, DCMSG
import time
from collections import deque
import _thread

__pcb__ = '0.2'
__version__ = '0.2 a1'

led_ind_stat = False
hub_chain_no = -1
total_hubs = -1
eoc = False  # end of daisy chain flag


def _intr_change_switch(pin) -> None:
    cur = get_switch()
    if cur == 1:
        set_switch(0)
    elif cur == 0:
        set_switch(1)
    else:
        raise ValueError(f'manual channel {cur} invalid position')


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
    return adc.get(no).read_u16() * HW.ADC_REF_V / 65536 / HW.ADC_RATIO


def set_switch(ch_no: int) -> None:
    """
    set usb switch position. switch to 0 or 1 (ch1 or ch2)
    """
    if ch_no not in [0, 1]:
        raise ValueError(f'cannot switch cha to {ch_no} (ch{ch_no+1}). Only 0, 1 (2 channels) supported')
    _sw2_sel.value(ch_no)
    _sw3_sel.value(ch_no)
    _sw_rel.value(ch_no)


def get_switch() -> int:
    """
    get current usb switch position. Expect 1 or 2.
    """
    switch_ctrl = [_sw2_sel.value(), _sw3_sel.value(), _sw_rel.value()]
    if len(set(switch_ctrl)) > 1:  # if not all 0 or all 1
        raise ValueError(f'internal error. ICs selection or Relay selection error. sel_2, sel_3, rel: {switch_ctrl}')
    return switch_ctrl[1]  # return any value from switch list


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

    def __init__(self, scl_pin=HW.HUB_SCL, sda_pin=HW.HUB_SDA, frequency=400000) -> None:
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
        _hub_rst.value(HW.HIGH)
        time.sleep(seconds)
        _hub_rst.value(HW.LOW)
        time.sleep(seconds/2)
        self._init_hub()


class UARTController(object):
    CRC_KEY = '1101'  # polynomial x^3 + x^2 + x^0
    MSG_SCAN = DC.make_data(DC.SCAN, DC.DATA_DEF, DC.DATA_DEF)

    def __init__(self, tx_upstream: int, rx_upstream: int, tx_downstream: int, rx_downstream: int, baudrate=HW.UART_BAUD):
        self.q_us = deque((), HW.Q_LEN)
        self.uart_us = UART(0, baudrate=baudrate, tx=Pin(tx_upstream), rx=Pin(rx_upstream))
        self.q_ds = deque((), HW.Q_LEN)
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
    
    def _read_data(self, ds_us_obj) -> DCMSG:
        """
        read a daisy chain data outside rx thread function
        """
        if ds_us_obj.any() > 0:
            self.q_lock.acquire()
            data = self.uart_us.read(HW.DATA_SIZE)
            self.q_lock.release()
            if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
                return  # invalid ack data return None
            return DCMSG(data, data[1], data[2], data[3], data[4])
        
    def _wait_next_ack(self):
        """
        wait for next daisy chain hub to ack upstream scan command been sent
        """
        start_t = time.ticks_ms()
        while time.ticks_ms() - start_t < DC.END_CHAIN_TIMEOUT:
            ack = self._read_data(self.uart_ds)
            if ack:
                if ack.hub_stat == DC.SCAN_ACK:
                    return True
        return False

    def send_upstream(self, data: bytes, no_crc=True) -> int:
        if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
            raise ValueError('Invalid daisy chain data')
        return self.uart_us.write(data)

    def send_downstream(self, data: bytes, no_crc=True) -> int:
        if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
            raise ValueError('Invalid daisy chain data')
        return self.uart_ds.write(data)
    
    def dc_broadcast(self) -> int:
        """
        Initiate a broadcast daisy chain signal to query for avaiable chain-able hubs. The current hub (issuer) will 
        be the first device of the chain.
        """
        global hub_chain_no
        global total_hubs
        hub_chain_no = 0
        msg_nxt_relay = DC.make_data(DC.SCAN, hub_chain_no, DC.DATA_DEF)
        self.send_downstream(msg_nxt_relay)
        time_s = time.ticks_ms()
        if self._wait_next_ack():
            while time.ticks_ms() - time_s < DC.BROADCAST_TIMEOUT:
                hubs_data = self._read_data(self.uart_ds)
                if hubs_data.cmd == DC.SCAN_RTN:
                    return hubs_data.hub_no
        total_hubs = -1
        hub_chain_no = -1
    
    def msg_relay_broadcast(self, dcmsg: DCMSG) -> int:
        """
        downstream hubs for relaying or returning daisy chain message
        """
        if dcmsg.cmd == DC.SCAN:  # relay dc signal to next downstream with chain no +1
            global hub_chain_no
            hub_chain_no = dcmsg.hub_no + 1
            msg_nxt_relay = DC.make_data(DC.SCAN, hub_chain_no, DC.DATA_DEF)
            self.send_downstream(msg_nxt_relay)
            if not self._wait_next_ack():  # end of chain found
                DC.make_data(DC.SCAN_RTN, hub_chain_no, DC.DATA_DEF)
                self.send_upstream()
        elif dcmsg.cmd == DC.SCAN_RTN:  # return signal from downstream back to upstream broadcaster
            global total_hubs
            total_hubs = dcmsg.hub_no
            self.send_upstream(dcmsg.raw)
    
    def msg_switch(self, data: bytes) -> None:
        """
        routing message to its owm execution function
        """
        if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
            return
        msg = DCMSG(data, data[1], data[2], data[3], data[4])
        if msg.cmd == DC.SCAN or msg.cmd == DC.SCAN_RTN:
            self.msg_relay_broadcast(msg)

    def rx_thread(self):
        while self.rx_flag:
            if self.uart_us.any() > 0:  # if there's any data in rx buffer
                self.q_lock.acquire()
                self.q_us.append(self.uart_us.read(HW.DATA_SIZE))
                self.q_lock.release()
            if self.uart_ds.any() > 0:
                self.q_lock.acquire()
                self.q_ds.append(self.uart_ds.read(HW.DATA_SIZE))
                self.q_lock.release()
            if len(self.q_us) > 0:  # processing message from upstream
                self.q_lock.acquire()
                data_raw = self.q_us.popleft()
                self.q_lock.release()
                self.msg_switch(data_raw)
            if len(self.q_ds) > 0:  # processing message from downstream
                self.q_lock.acquire()
                data_raw = self.q_ds.popleft()
                self.q_lock.release()
                self.msg_switch(data_raw)


def version() -> str:
    return f'usb-xwitch ver:{__version__}'


__doc__ = f'''Functions:
         {set_hub.__name__}(list): set hub 4 channels on/off. format: [bool, bool, bool, bool]
         {get_hub.__name__}(): get current hub 4 channels in tuple
         {set_switch.__name__}(int): set switch to channel 1 / 2. starting from 0
         {get_switch.__name__}(): get current switch channel
         {get_adc.__name__}(int): get current switch bus 1 / 2 volrage reading
         {flip_indicator_led.__name__}(): flip indicator led to opposite state
         {ind_led.__name__}(bool): bool. set indicator led status
         '''


_led_ind = Pin(HW.IND_LED, Pin.OUT)
_adc_a1 = ADC(HW.ADC_1_1)
_adc_a2 = ADC(HW.ADC_1_2)
# switch ICs pin power up pre-condition
_sw2_pd = Pin(HW.PD_U2, Pin.OUT)
_sw2_pd.value(HW.LOW)
_sw2_sel = Pin(HW.SEL_U2, Pin.OUT)
_sw3_pd = Pin(HW.PD_U3, Pin.OUT)
_sw3_pd.value(HW.HIGH)  #TODO: debug USB3 comms
_sw3_sel = Pin(HW.SEL_U3, Pin.OUT)
_sw_rel = Pin(HW.SW_REL, Pin.OUT)
# switch manual button control pre-condition
_sw_man = Pin(HW.SW_MAN, Pin.IN, Pin.PULL_UP)
_sw_man.irq(trigger=Pin.IRQ_FALLING, handler=_intr_change_switch)
# HUB IC pin pre-condition
_hub_rst = Pin(HW.HUB_RST, Pin.OUT)
_hub_rst.value(HW.LOW)
# Daisy chain UART set up
_uart = UARTController(HW.UART_U_TX, HW.UART_U_RX, HW.UART_D_TX, HW.UART_D_RX)
_hub = HUBI2C()
