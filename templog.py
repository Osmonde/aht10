#!/usr/bin/python3
# i2cdetect -y 1
import os
import signal 
import smbus
import time
import logging
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from threading import Event

AHT10_ADDRESS = 0x38
AHT10_SOFT_RESET = 0xBA
AHT10_INITIALIZE = 0xE1
AHT10_MEASURE = 0xAC
AHT10_MEASURE_DATA = 0x33
AHT10_MEASURE_CALIB = 0x08
AHT10_NOOP = 0x00

LOG_PATH = '/var/log/templog'

SIGNALS = ('TERM', 'HUP', 'INT')
exit = Event()

if not os.path.isdir(LOG_PATH):
    os.makedirs(LOG_PATH)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = TimedRotatingFileHandler(f"{LOG_PATH}/environment_temperature.log", when='D', interval=1, backupCount=7)
file_log_format = u'%(asctime)s :: %(message)s'
file_log_date = u'%Y-%m-%d_%H:%M:%S'
file_handler.setFormatter(logging.Formatter(fmt=file_log_format, datefmt=file_log_date))

console_handler = StreamHandler()
console_log_format = u'%(asctime)s :: %(levelname)s :: %(message)s'
console_handler.setFormatter(logging.Formatter(fmt=console_log_format))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


def quit(signo, _frame):
    logger.info(f"Received exit signal: {signo}")
    exit.set()


def config_sensor(bus):
    logger.info("Initializing sensor with calibration.")
    init_param = [AHT10_MEASURE_CALIB, AHT10_NOOP]
    bus.write_i2c_block_data(AHT10_ADDRESS, AHT10_INITIALIZE, init_param)
    time.sleep(0.1)


def measure(bus):
    logger.debug("Starting measurement.")
    byt = bus.read_byte(AHT10_ADDRESS)
    #print(byt&0x68)
    measure_param = [AHT10_MEASURE, AHT10_NOOP]
    bus.write_i2c_block_data(AHT10_ADDRESS, AHT10_MEASURE, measure_param)
    logger.debug("Waiting to retrieve measurement data...")
    time.sleep(0.1)
    data = bus.read_i2c_block_data(0x38,0x00)

    return data


def get_temp(data):
    temp = ((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]
    ctemp = ((temp*200) / 1048576) - 50
    return u'Temperature: {0:.1f}°C'.format(ctemp)


def get_humidity(data):
    tmp = ((data[1] << 16) | (data[2] << 8) | data[3]) >> 4
    #print(tmp)
    ctmp = int(tmp * 100 / 1048576)
    return u'Humidity: {0}%'.format(ctmp)


def get_cpu_temp(temperature_file):
    temperature_file.seek(0)
    temp_line = temperature_file.readline().strip()
    cpu_temp = int(temp_line) / 1000

    return f"CPU Temp: {cpu_temp}°C"

def main():
    bus = smbus.SMBus(1)
    temperature_file = open('/sys/class/thermal/thermal_zone0/temp', 'r')

    config_sensor(bus)

    while not exit.is_set():
        data = measure(bus)

        temp = get_temp(data)
        humid = get_humidity(data)
        cpu = get_cpu_temp(temperature_file)
        logger.info(f"{temp} {humid} {cpu}")

        exit.wait(60)

    logger.info("Daemon is exiting...")
    temperature_file.close()

if __name__ == "__main__":
    logger.info("Starting temperature monitor.")
    for sig in SIGNALS:
        signal.signal(getattr(signal, 'SIG' + sig), quit)
 
    main()
