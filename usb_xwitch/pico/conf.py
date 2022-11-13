from ucollections import namedtuple

RegAddr = namedtuple("RegisterAddr", ("name", "addr", "default_val"))


class HUBAddr(object):
    # USB2514B I2C slave address. USB251x must transmitted MSB first
    SLAVE = 0x2C

    # Register Address
    VENDOR_ID_LSB = RegAddr("VENDOR_ID_LSB", 0x00, 0x24)  # vendor ID LSB
    VENDOR_ID_MSB = RegAddr("VENDOR_ID_MSB", 0x01, 0x04)  # vendor ID MSB
    PRODUCT_ID_LSB = RegAddr("PRODUCT_ID_LSB", 0x02, 0x14)  # product ID LSB
    PRODUCT_ID_MSB = RegAddr("PRODUCT_ID_MSB", 0x03, 0x25)  # product ID MSB
    DEVICE_ID_LSB = RegAddr("DEVICE_ID_LSB", 0x04, 0xB3)  # device ID LSB
    DEVICE_ID_MSB = RegAddr("DEVICE_ID_MSB", 0x05, 0x0B)
    CONFIG_DATA_B1 = RegAddr("CONFIG_DATA_B1", 0x06, 0x9B)  # Configuration data byte 1
    CONFIG_DATA_B2 = RegAddr("CONFIG_DATA_B2", 0x07, 0x20)
    CONFIG_DATA_B3 = RegAddr("CONFIG_DATA_B3", 0x08, 0x02)
    NON_REMOVABLE_DEV = RegAddr("NON_REMOVABLE_DEV", 0x09, 0x00)  # Non-removable devices
    PORT_DISABLE_SELF = RegAddr("PORT_DISABLE_SELF", 0x0A, 0x00)  # Port disable self
    PORT_DISABLE_BUS = RegAddr("PORT_DISABLE_BUS", 0x0B, 0x00)  # Port disable bus
    MAX_POWER_SELF = RegAddr("MAX_POWER_SELF", 0x0C, 0x01)  # max power self
    MAX_POWER_BUS = RegAddr("MAX_POWER_BUS", 0x0D, 0x32)
    MAX_CURR_SELF = RegAddr("MAX_CURR_SELF", 0x0E, 0x00)  # hub controller max current (self)
    MAX_CURR_BUS = RegAddr("MAX_CURR_BUS", 0x0F, 0x00)
    PWR_ON_TIME = RegAddr("PWR_ON_TIME", 0x10, 0x00)  # power on time
    LANG_ID_HIGH = RegAddr("LANG_ID_HIGH", 0x11, 0x00)  # language ID high
    LANG_ID_LOW = RegAddr("LANG_ID_LOW", 0x12, 0x00)  # language ID low
    MFG_STR_LEN = RegAddr("MFG_STR_LEN", 0x13, 0x00)  # manufacturer string length
    PDT_STR_LEN = RegAddr("PDT_STR_LEN", 0x14, 0x00)  # product string length
    SN_STR_LEN = RegAddr("SN_STR_LEN", 0x15, 0x00)  # serial string length
    MFG_STR = RegAddr("MFG_STR", range(0x16, 0x53), 0x00)  # manufacturer string length
    PDT_STR = RegAddr("PDT_STR", range(0x54, 0x91), 0x00)  # product string
    SN_STR = RegAddr("SN_STR", range(0x92, 0xCF), 0x00)  # serial string
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
                    MAX_POWER_BUS]
