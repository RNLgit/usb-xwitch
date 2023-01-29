from machine import Pin, ADC, UART, I2C
from conf import HUBAddr, HW, DC, DCMSG
import time
from collections import deque
import _thread

__pcb__ = '0.2'
__version__ = '0.2 a1'
_debug = False

led_ind_stat = False
hub_chain_id = -1
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


def set_hub_chain(*args) -> None:
    """
    set hub channel on off in chain giving its id. id as kwargs name and bool list as argument.
    e.g.:
        >>> set_hub_chain(None, [1,0,0])  # set 2nd hub (hub id 1) channel 1 on, 2 & 3 off, first hub unchanged (None). 
        Where channel 4 used for connecting next chain hub.
        >>> set_hub_chain(None, None, [0, 1, 0, 1])  # set 3rd hub (id 2) channel 2 & 4 on, 1 & 3 off. Total 3 hubs in 
        the chain.
    """
    if len(args) > total_hubs:
        raise IndexError(f"trying to set hub outside range. total hubs: {total_hubs}")
    for i in reversed(range(len(args))):  # from furtherest chain avoid been cycled by upstream
        if args[i]:
            if i == 0:  # daisy chain root hub
                args[i].insert(DC.DC_CH, True)  # channel to chain next hub should always set on
                set_hub(args[i])
                continue
            is_rtn_received = False
            if _debug: print(f"DaisyChain: SET_HUB: args: {args}, i: {i}")
            if len(args[i]) > len(DC.CHANNEL_MSKS) - 1 and i + 1 < total_hubs:
                raise IndexError(f"Too many channels to set hub: {i}. (mid-chain hubs need one channel for next hub)")
            _uart.send_downstream(DC.make_data(DC.SET_HUB, i,
                                               sum([ch for ch_on, ch in zip(args[i], DC.CHANNEL_MSKS) if ch_on])))
            start_ms = time.ticks_ms()
            while time.ticks_ms() - start_ms < DC.BROADCAST_TIMEOUT:  # may take longer than 1s to reset ic
                if len(_uart.q_msg) > 0:
                    msg = _uart.q_msg.popleft()
                    if hasattr(msg, "cmd"):
                        if msg.cmd == DC.SET_HUB_RTN and int(msg.hub_no) == int(i) and msg.hub_stat == DC.ACK:
                            if _debug: print(f"DaisyChain: SET_HUB_RTN message: {msg}")
                            is_rtn_received = True
                            break
            if is_rtn_received:
                continue
            raise ValueError(f"trying to set hub: {i} in chain with no ack response")


def get_hub() -> tuple:
    """
    get usb hub current channels status in tuple of bools.
    """
    data = _hub._br(HUBAddr.PORT_DISABLE_SELF.addr)[1]
    return not bool(data & HUBAddr.PORT_MSK_1), not bool(data & HUBAddr.PORT_MSK_2), \
        not bool(data & HUBAddr.PORT_MSK_3), not bool(data & HUBAddr.PORT_MSK_4)


def get_hubs() -> dict:
    """
    get available hubs all port status in dict
    """
    if hub_chain_id < 0:
        raise ValueError("HUB in standalone mode. Connect daisy chain and use dc_broadcast before use this function.")
    hub_dict = {}
    for id in range(total_hubs):
        hub_dict[id] = get_hub_chain(id)
    return hub_dict


def get_hub_chain(hub_id: int) -> list:
    """
    get hub channel on/off status on daisy chain
    """
    if hub_id == hub_chain_id:  # when querying current hub, not returning the channel used for daisy chain
        return [x for i, x in enumerate(get_hub()) if i != DC.DC_CH]
    _uart.send_downstream(DC.make_data(DC.GET_HUB, hub_id, DC.DATA_DEF))
    start_ms = time.ticks_ms()
    while time.ticks_ms() - start_ms < DC.END_CHAIN_TIMEOUT:
        if len(_uart.q_msg) > 0:
            msg = _uart.q_msg.popleft()
            if hasattr(msg, "cmd"):
                if msg.cmd == DC.GET_HUB_RTN:
                    if _debug: print(f"DaisyChain: get downstream chain stat: {msg}")
                    assert msg.hub_no == hub_id
                    if msg.hub_stat == DC.ERROR:
                        raise OSError(f"hub id:{hub_id} not activated yet. Please check it it is connected")
                    ch1to3 = [bool(DC.CHANNEL_MSK_1 & msg.hub_stat), bool(DC.CHANNEL_MSK_2 & msg.hub_stat),
                              bool(DC.CHANNEL_MSK_3 & msg.hub_stat)]
                    if hub_id + 1 == total_hubs:  # querying hub is end of chain, have all 4 ports available
                        ch1to3.append(bool(DC.CHANNEL_MSK_4 & msg.hub_stat))
                    return ch1to3
    raise ValueError(f"no downstream hub responding within: {DC.END_CHAIN_TIMEOUT}ms")


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
    """
    UART to communicate to upstream / downstream devices. Daisy chain function for usb hub
    """
    CRC_KEY = '1101'  # polynomial x^3 + x^2 + x^0
    MSG_SCAN = DC.make_data(DC.SCAN, DC.DATA_DEF, DC.DATA_DEF)

    def __init__(self, tx_upstream: int, rx_upstream: int, tx_downstream: int, rx_downstream: int, baudrate=HW.UART_BAUD):
        self.q_us = deque((), HW.Q_LEN)
        self.uart_us = UART(0, baudrate=baudrate, tx=Pin(tx_upstream), rx=Pin(rx_upstream))
        self.q_ds = deque((), HW.Q_LEN)
        self.uart_ds = UART(1, baudrate=baudrate, tx=Pin(tx_downstream), rx=Pin(rx_downstream))
        self.q_msg = deque((), HW.Q_LEN)
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
            data = ds_us_obj.read(HW.DATA_SIZE)
            if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
                return  # invalid ack data return None
            return DCMSG(data, data[1], data[2], data[3], data[4])
        
    def _wait_ds_ack(self):
        """
        wait for next daisy chain downstream hub to ack upstream scan command been sent
        """
        if _debug: print('DaisyChain: waiting downstream ack')
        start_t = time.ticks_ms()
        while time.ticks_ms() - start_t < DC.END_CHAIN_TIMEOUT:
            ack = self._read_data(self.uart_ds)
            if ack:
                if ack.hub_stat == DC.ACK:
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
        self.q_lock.acquire()
        global hub_chain_id
        global total_hubs
        hub_chain_id = 0
        msg_nxt_relay = DC.make_data(DC.SCAN, hub_chain_id, DC.DATA_DEF)
        if _debug: print('DaisyChain: sending broadcasting message to downstream')
        self.send_downstream(msg_nxt_relay)
        time_s = time.ticks_ms()
        if self._wait_ds_ack():
            if _debug: print('DaisyChain: Got ACK from first downstream hub, waiting daisy chain return message')
            while time.ticks_ms() - time_s < DC.BROADCAST_TIMEOUT:
                hubs_data = self._read_data(self.uart_ds)
                if hubs_data:  # prevent checking None
                    if hubs_data.cmd == DC.SCAN_RTN:
                        self.q_lock.release()
                        hub_chain_id = 0
                        total_hubs = hubs_data.hub_no
                        if _debug: print(f'DaisyChain: received return message. Total hubs are: {total_hubs}. This hub index: {hub_chain_id}')
                        return total_hubs  # return back with total number of hubs on chain (starting 0)
        total_hubs = -1
        hub_chain_id = -1
        self.q_lock.release()
        return -1
    
    def msg_relay_broadcast(self, dcmsg: DCMSG) -> int:
        """
        downstream hubs for relaying or returning daisy chain message
        """
        if _debug: print(f'DaisyChain: relaying: {dcmsg}')
        global hub_chain_id
        hub_chain_id = dcmsg.hub_no + 1
        msg_nxt_relay = DC.make_data(DC.SCAN, hub_chain_id, DC.DATA_DEF)
        self.send_downstream(msg_nxt_relay)
        ack_back = DC.make_data(DC.SCAN, DC.DATA_DEF, DC.ACK)
        self.send_upstream(ack_back)
        if not self._wait_ds_ack():  # end of chain found
            dc_rtn_msg = DC.make_data(DC.SCAN_RTN, hub_chain_id + 1, DC.DATA_DEF)  # total + 1 as id starts 0
            self.send_upstream(dc_rtn_msg)
            global total_hubs
            total_hubs = hub_chain_id + 1  # no of end chain hub is total hubs number
            if _debug: print(f'DaisyChain: this hub is end of chain, this hub id: {hub_chain_id}, sending back: {dc_rtn_msg}')
    
    def msg_return_chain(self, dcmsg: DCMSG) -> None:
        """
        returning daisy chain downstream 
        """
        if _debug: print(f'DaisyChain: returnning to upstream: {dcmsg}')
        global total_hubs
        total_hubs = dcmsg.hub_no
        self.send_upstream(dcmsg.raw)
    
    def msg_switch(self, data: bytes) -> None:
        """
        routing message to its owm execution function
        """
        if not data:  # prevent checking None
            return
        if data[0] != DC.DC_HEADER or len(data) != DC.MSG_LEN:
            return
        msg = DCMSG(data, data[1], data[2], data[3], data[4])
        if msg.cmd == DC.SCAN:
            if _debug: print(f'DaisyChain: SCAN: scan downstream message received: {msg}')
            self.msg_relay_broadcast(msg)
        elif msg.cmd == DC.SCAN_RTN:
            if _debug: print(f'DaisyChain: SCAN_RTN: returning upstream message received: {msg}')
            self.msg_return_chain(msg)
        elif msg.cmd == DC.GET_HUB:
            if _debug: print(f"DaisyChain: GET_HUB: request received: {msg}")
            if msg.hub_no == hub_chain_id:
                try:
                    if hub_chain_id + 1 == total_hubs:
                        stat = get_hub()
                    else:  # excluding the channel used for daisy chain next hub
                        stat = [x for i, x in enumerate(get_hub()) if i != DC.DC_CH]
                    self.send_upstream(DC.make_data(DC.GET_HUB_RTN, hub_chain_id, int("".join(str(int(i)) for i in reversed(stat)), 2)))
                except OSError:
                    if _debug: print("DaisyChain: GET_HUB: calling get_hub error. Possibly hub not activated yet")
                    self.send_upstream(DC.make_data(DC.GET_HUB_RTN, hub_chain_id, DC.ERROR))
            else:
                if _debug: print(f"DaisyChain: GET_HUB: {msg} not in scope of current chain, relaying msg to next hub")
                self.send_downstream(msg.raw)
        elif msg.cmd == DC.SET_HUB:
            if _debug: print(f"DaisyChain: SET_HUB: request received: {msg}")
            if msg.hub_no == hub_chain_id:
                if hub_chain_id + 1 == total_hubs:
                    set_lst = [bool(msg.hub_stat & DC.CHANNEL_MSK_1), bool(msg.hub_stat & DC.CHANNEL_MSK_2),
                               bool(msg.hub_stat & DC.CHANNEL_MSK_3), bool(msg.hub_stat & DC.CHANNEL_MSK_4)]
                    set_hub(set_lst)
                    self.send_upstream(DC.make_data(DC.SET_HUB_RTN, hub_chain_id, DC.ACK))
                else:
                    set_lst = [bool(msg.hub_stat & DC.CHANNEL_MSK_1), bool(msg.hub_stat & DC.CHANNEL_MSK_2),
                               bool(msg.hub_stat & DC.CHANNEL_MSK_3)]
                    set_lst.insert(DC.DC_CH, True)  # channel to chain next hub should always set on
                    set_hub(set_lst)
                    self.send_upstream(DC.make_data(DC.SET_HUB_RTN, hub_chain_id, DC.ACK))
            else:
                if _debug: print(f"DaisyChain: SET_HUB: {msg} not in scope of current chain, relaying cmd to next hub")
                self.send_downstream(msg.raw)
        elif msg.cmd in [DC.GET_HUB_RTN, DC.SET_HUB_RTN] and hub_chain_id > 0:
            if _debug: print(f"DaisyChain: GET/SET_HUB_RTN: {msg}")
            self.send_upstream(msg.raw)
        else:  # all the rest dump into msg queue, mainly for controlling hub to read
            self.q_msg.append(msg)

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
_sw3_pd.value(HW.HIGH)  # TODO: debug USB3 comms
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
