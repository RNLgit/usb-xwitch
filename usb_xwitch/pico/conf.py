from ucollections import namedtuple

RegAddr = namedtuple("RegisterAddr", ("name", "addr", "default_val"))
DCMSG = namedtuple("DaisychainMsg", ("raw", "cmd", "hub_no", "hub_stat", "rsvd"))


class HUBAddr(object):
    """
    USB2514 Address constants
    """
    # USB2514B I2C slave address. USB251x must transmitted MSB first
    SLAVE = 0x2C
    DATA_MFG_STR = b'B\x00M\x00D\x00-\x00Q\x00A\x00'  #TODO: utf-16le byte order
    DATA_PDT_STR = b'u\x00s\x00b\x00-\x00x\x00w\x00i\x00t\x00c\x00h\x00'
    DATA_SN_STR = b'B\x00Q\x00A\x002\x005\x001\x004\x002\x000\x002\x002\x000\x002\x000\x001\x00'
    HW_VER = 0.2  # only one decimal point

    PORT_MSK_1 = 0x02
    PORT_MSK_2 = 0x04
    PORT_MSK_3 = 0x08
    PORT_MSK_4 = 0x10
    PORTS_MASK = [PORT_MSK_1, PORT_MSK_2, PORT_MSK_3, PORT_MSK_4]

    # Register Address Defaults
    VENDOR_ID_LSB = RegAddr("VENDOR_ID_LSB", 0x00, 0xDB)  # vendor ID LSB
    VENDOR_ID_MSB = RegAddr("VENDOR_ID_MSB", 0x01, 0x1E)  # vendor ID MSB
    PRODUCT_ID_LSB = RegAddr("PRODUCT_ID_LSB", 0x02, 0x14)  # product ID LSB
    PRODUCT_ID_MSB = RegAddr("PRODUCT_ID_MSB", 0x03, 0x25)  # product ID MSB
    DEVICE_ID_LSB = RegAddr("DEVICE_ID_LSB", 0x04, 0x20)  # device ver LSB
    DEVICE_ID_MSB = RegAddr("DEVICE_ID_MSB", 0x05, 0x00)  # device ver MSB
    CONFIG_DATA_B1 = RegAddr("CONFIG_DATA_B1", 0x06, 0x9B)  # Configuration data byte 1
    CONFIG_DATA_B2 = RegAddr("CONFIG_DATA_B2", 0x07, 0x30)
    CONFIG_DATA_B3 = RegAddr("CONFIG_DATA_B3", 0x08, 0x02)
    NON_REMOVABLE_DEV = RegAddr("NON_REMOVABLE_DEV", 0x09, 0x00)  # Non-removable devices
    PORT_DISABLE_SELF = RegAddr("PORT_DISABLE_SELF", 0x0A, 0x00)  # Port disable self
    PORT_DISABLE_BUS = RegAddr("PORT_DISABLE_BUS", 0x0B, 0x1E)  # Port disable bus
    MAX_POWER_SELF = RegAddr("MAX_POWER_SELF", 0x0C, 0x50)  # max power self
    MAX_POWER_BUS = RegAddr("MAX_POWER_BUS", 0x0D, 0x50)
    MAX_CURR_SELF = RegAddr("MAX_CURR_SELF", 0x0E, 0x50)  # hub controller max current (self)
    MAX_CURR_BUS = RegAddr("MAX_CURR_BUS", 0x0F, 0x50)
    PWR_ON_TIME = RegAddr("PWR_ON_TIME", 0x10, 0x00)  # power on time
    LANG_ID_HIGH = RegAddr("LANG_ID_HIGH", 0x11, 0x04)  # language ID high (upper)
    LANG_ID_LOW = RegAddr("LANG_ID_LOW", 0x12, 0x09)  # language ID low
    MFG_STR_LEN = RegAddr("MFG_STR_LEN", 0x13, 0x0C)  # manufacturer string length
    PDT_STR_LEN = RegAddr("PDT_STR_LEN", 0x14, 0x14)  # product string length
    SN_STR_LEN = RegAddr("SN_STR_LEN", 0x15, 0x1E)  # serial string length
    MFG_STR = RegAddr("MFG_STR", list(range(0x16, 0x53)), list(DATA_MFG_STR))  #TODO: manufacturer string length
    PDT_STR = RegAddr("PDT_STR", list(range(0x54, 0x91)), list(DATA_PDT_STR))  #TODO: product string
    SN_STR = RegAddr("SN_STR", list(range(0x92, 0xCF)), list(DATA_SN_STR))  #TODO: serial string
    BATT_CHG_EN = RegAddr("BATT_CHG_EN", 0xD0, 0x00)  # battery charging enable
    BOOST_UP = RegAddr("BOOST_UP", 0xF6, 0x00)  # boost up
    BOOST_4_0 = RegAddr("BOOST_4_0", 0xF8, 0x00)
    PORT_SWAP = RegAddr("PORT_SWAP", 0xFA, 0x00)
    PORT_MAP_12 = RegAddr("PORT_MAP_12", 0xFB, 0x00)
    PORT_MAP_34 = RegAddr("PORT_MAP_34", 0xFC, 0x00)
    STAT_CMD = RegAddr("STAT_CMD", 0XFF, 0x00)  # Status / Command (SMBus only)

    # Default Load List
    INIT_DEFAULT = [VENDOR_ID_LSB, VENDOR_ID_MSB, PRODUCT_ID_LSB, PRODUCT_ID_MSB, DEVICE_ID_LSB,
                    DEVICE_ID_MSB, CONFIG_DATA_B1, CONFIG_DATA_B2, CONFIG_DATA_B3, MAX_POWER_BUS,
                    MAX_POWER_BUS, MAX_POWER_SELF, MAX_CURR_SELF, BATT_CHG_EN]
    MFG_AUX_DEFAULT = [MFG_STR_LEN, PDT_STR_LEN, SN_STR_LEN, LANG_ID_HIGH, LANG_ID_LOW]
    MFG_DEFAULT = [MFG_STR, PDT_STR, SN_STR]


class HW(object):
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


class DC(object):
    """
    Daisy chain parameters

    Daisy chain messages. When invalid message, no response.
    Message format:

    +----------+-------------+-------------+-----------+------+-------+
    |  header  |    CMD      |   Hub No    | Hub Stat  | RSVD |  CRC  |
    +----------+-------------+-------------+-----------+------+-------+
    |   0xDC   |    byte     |   byte      |   byte    | byte | byte  |
    +----------+-------------+-------------+-----------+------+-------+
    """
    DC_CH = 3  # default channel 4 as downstream daisy chain channel
    MSG_LEN = 6  # Daisy chain data message length 
    END_CHAIN_TIMEOUT = 1000  # daisy chain scan broadcast miliseconds for end of chain hub scan
    BROADCAST_TIMEOUT = 3000  # whole daisy chain hub broadcast process timeout in miliseconds
    # header and EoM
    DC_HEADER = 0xDC  # start of message

    # cmd field
    SCAN = 0x01  # Broadcast signal to scan for hubs can be daisy chained
    SCAN_RTN = 0x11
    """
    SET_HUB: 
        Hub No: hub chain no. Self hub no 0x00. Max 255 hubs
        Hub Stat: chained hub channels on/off stat. i.e. at the #HubNo hub, set / get ch 0 & 3 on, 1 & 2 off.
            which is [1, 0, 1, 0], in bits: b00000101, in hex 0x05
    """
    SET_HUB = 0x02
    GET_HUB = 0x03
    SET_SWITCH = 0x04  # Hub No is switch to MUX channel
    GET_SWITCH = 0x05
    GET_TOT_HUBS = 0x06  # get total hubs number

    # Hub stat field
    SCAN_ACK = 0x01  # used for downstream ack upscream uart dc relaying message

    # Data field
    DATA_DEF = 0x0  # Default data field value 0
    # RSVD
    RSVD = 0x0  # Reserved field

    @staticmethod
    def make_data(cmd: int, data1: int, data2: int, rsvd=RSVD) -> bytes:
        # TODO: CRC calculation for last byte
        return bytes([DC.DC_HEADER, cmd, data1, data2, rsvd, 0x0])
    
    @classmethod
    def decode_data(cls, data: bytes) -> DCMSG:
        if len(data) != cls.MSG_LEN:
            raise ValueError("Invalid data length to decode.")
        if data[0] != cls.DC_HEADER:
            raise ValueError("Invalid daisy chain message header")
        return DCMSG(data, data[1], data[2], data[3], data[4])
