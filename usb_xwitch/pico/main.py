from machine import Pin, ADC

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


def pico_led(en: bool) -> None:
    """
    toggle on off of pico onboard led
    """
    _led_pico.value(en)


def flip_pico_led():
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


_led_pico = Pin(PICO_LED, Pin.OUT)
_adc_a1 = ADC(ADC_1_1)
_adc_a2 = ADC(ADC_1_2)
_swa = Pin(SW_A, Pin.IN, Pin.PULL_DOWN)
_swa.irq(trigger=Pin.IRQ_RISING, handler=flip_pico_led)
