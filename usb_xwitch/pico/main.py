from machine import Pin, ADC

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
# ADC Pins
ADC_1_1 = 26  # CHA mus 2-1 VBus voltage
ADC_1_2 = 27  # CHA mus 2-2 VBus voltage
# Conversion
ADC_RATIO = 18/33  # ADC voltage divider ratio
ADC_REF_V = 3.3  # ADC reference voltage

led_ind_stat = False


def _intr_flip_pico_led(pin) -> None:
    pass


def ind_led(en: bool) -> None:
    """
    toggle on off of pico onboard led
    """
    _led_ind.value(en)


def flip_pico_led() -> None:
    """
    flip pico onboard led status
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
    sel2, sel3, rel = _sw2_sel.value(), _sw3_sel.value(), _sw_rel.value()
    if sel2 ^ sel3 ^ rel:  # if not all 0 or all 1
        raise ValueError(f'internal error. IC selection and Relay selection not match. sel:{sel}, rel:{rel}')
    return sel3 + 1


def set_hub(channel: int, on_off: bool) -> None:
    """
    set usb hub channel
    """
    pass


def get_hub() -> bool:
    """
    get usb hub current channels status
    """
    pass


def version():
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
