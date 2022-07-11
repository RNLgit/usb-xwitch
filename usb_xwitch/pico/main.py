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

led_pico = Pin(PICO_LED, Pin.OUT)
adc_a1 = ADC(ADC_1_1)
adc_a2 = ADC(ADC_1_2)

print('usb-xwitch v0.1\nby RNL\n')


def pico_led(en: bool) -> None:
    led_pico.value(en)


def get_adc(no: int) -> float:
    adc = {1: adc_a1, 2: adc_a2}
    if adc.get(no) is None:
        raise ValueError(f'adc {no} invalid')
    return adc.get(no).read_u16() * ADC_REF_V / 65536 / ADC_RATIO
