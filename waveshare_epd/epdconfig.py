import spidev
import time
from periphery import GPIO

RST_PIN         = 17
DC_PIN          = 25
CS_PIN          = 8
BUSY_PIN        = 24

SPI = spidev.SpiDev()
SPI.open(3, 0)
SPI.max_speed_hz = 2000000
SPI.mode = 0b00

# Keep the Bank 3 math!
rst_pin  = GPIO("/dev/gpiochip3", 1, "out")  # Physical Pin 11
busy_pin = GPIO("/dev/gpiochip3", 10, "in")  # Physical Pin 18
dc_pin   = GPIO("/dev/gpiochip3", 17, "out") # Physical Pin 22
cs_pin   = GPIO("/dev/gpiochip3", 14, "out") # Physical Pin 16 (Manual Door Control)

def module_init():
    return 0

def digital_write(pin, value):
    if pin == RST_PIN:
        rst_pin.write(bool(value))
    elif pin == DC_PIN:
        dc_pin.write(bool(value))
    elif pin == CS_PIN:
        cs_pin.write(bool(value)) # Python manually holds the door open

def digital_read(pin):
    if pin == BUSY_PIN:
        return int(busy_pin.read())
    return 0

def delay_ms(delaytime):
    time.sleep(delaytime / 1000.0)

def spi_writebyte(data):
    SPI.writebytes(data)

def spi_writebyte2(data):
    SPI.writebytes2(data)

def module_exit():
    SPI.close()
    rst_pin.close()
    dc_pin.close()
    cs_pin.close()
    busy_pin.close()
