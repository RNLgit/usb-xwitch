from machine import Pin, ADC

__version__ = '0.1'

HIGH = 1
LOW = 0

PICO_LED = 25  # Pico board default led
PD_A = 10  # CHA power down enable MUX IC
SEL_A = 11  # CHA MUX selection pin
REL_A = 12  # CHA USB VBus relay pin
SW_A = 13  # CHA push button switch
REL_B = 21  # CHB USB VBus relay pin (upper side)
REL_C = 20  # CHC USB VBus relay pin (left side)
ADC_1_1 = 26  # CHA mus 2-1 VBus voltage
ADC_1_2 = 27  # CHA mus 2-2 VBus voltage

ADC_RATIO = 18/33  # ADC voltage divider ratio
ADC_REF_V = 3.3  # ADC reference voltage

led_pico_stat = False


def _intr_flip_pico_led(pin) -> None:
    flip_pico_led()


def pico_led(en: bool) -> None:
    """
    toggle on off of pico onboard led
    """
    _led_pico.value(en)


def flip_pico_led() -> None:
    """
    flip pico onboard led status
    """
    global led_pico_stat
    led_pico_stat = not led_pico_stat
    pico_led(led_pico_stat)


def get_adc(no: int) -> float:
    """
    get adc reading from adc channel
    """
    adc = {1: _adc_a1, 2: _adc_a2}
    if adc.get(no) is None:
        raise ValueError(f'adc {no} invalid')
    return adc.get(no).read_u16() * ADC_REF_V / 65536 / ADC_RATIO


def set_cha_pos(ch_no: int) -> None:
    """
    set cha (with mux ic channel) switch position. switch to 1 or 2
    """
    if ch_no not in [1, 2]:
        raise ValueError(f'cannot switch cha to port {ch_no}. Only 2 channels supported')
    _cha_sel.value(ch_no - 1)
    _cha_rel.value(ch_no - 1)


def get_cha_pos() -> int:
    """
    get current cha switch position. Expect 1 or 2.
    """
    sel, rel = _cha_sel.value(), _cha_rel.value()
    if sel ^ rel:  # if not all 0 or all 1
        raise ValueError(f'internal error. IC selection and Relay selection not match. sel:{sel}, rel:{rel}')
    return sel + 1


def set_chb(on_off: bool) -> None:
    """
    set channel B power on / off
    """
    _chb_rel.value(on_off)


def get_chb() -> bool:
    """
    get bool stat of channel B VBus power
    """
    return bool(_chb_rel.value())


def set_chc(on_off: bool) -> None:
    """
    set channel C power on / off
    """
    _chc_rel.value(on_off)


def get_chc() -> bool:
    """
    get bool stat of channel C VBus power
    """
    return bool(_chc_rel.value())


def version():
    return f'usb-xwitch ver:{__version__}'


_led_pico = Pin(PICO_LED, Pin.OUT)
_adc_a1 = ADC(ADC_1_1)
_adc_a2 = ADC(ADC_1_2)
_swa = Pin(SW_A, Pin.IN, Pin.PULL_UP)
_swa.irq(trigger=Pin.IRQ_FALLING, handler=_intr_flip_pico_led)
_cha_pd = Pin(PD_A, Pin.OUT)
_cha_pd.value(LOW)
_cha_sel = Pin(SEL_A, Pin.OUT)
_cha_rel = Pin(REL_A, Pin.OUT)
_chb_rel = Pin(REL_B, Pin.OUT)
_chc_rel = Pin(REL_C, Pin.OUT)
