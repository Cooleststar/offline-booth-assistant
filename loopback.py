import spidev

# Open the SPI highway
spi = spidev.SpiDev()
spi.open(3, 0)
spi.max_speed_hz = 50000

print("Sending Data : [0xDE, 0xAD]")
# Send data out Pin 19, and simultaneously read what comes back on Pin 21
response = spi.xfer2([0xDE, 0xAD])

print(f"Received Data: [0x{response[0]:02X}, 0x{response[1]:02X}]")
spi.close()
