import os
import time
import utime
from machine import Pin, Timer, SoftI2C, ADC, Timer, RTC, SDCard
import machine
import bme680
import struct
import ujson as json

# LDR SENSOR (ANALOGIC INTERFACE)
adc = ADC(Pin(34), atten=ADC.ATTN_6DB) #10kOhm - 3.3v
_MAXL = 65535

# BMP680 SENSOR (I2C INTERFACE)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
bme = bme680.BME680_I2C(i2c=i2c)

lumin, temp, hum, pres, gas = 0,0,0,0,0

#SDCard Controller
_SD=None
try:
     _SD = SDCard(slot=2)
     os.mount(_SD, "/sd") 
except:_SD=None

#MAIN SENSOR CYCLE
def read_sensors():
    global lumin, temp, hum, pres, gas, bme
    print("Collecting Sample")
    lumin = round(lumin+(adc.read_u16() / _MAXL * 100),2)
    temp = round(temp+(bme.temperature), 2)
    hum = round(hum+(bme.humidity), 2)
    pres = round(pres+(bme.pressure), 2)
    gas = round(gas+((bme.gas/1000)), 2) 
    print("Sampling: {},{},{},{},{};".format(temp,hum,pres,gas,lumin))


def read_config():
    config_path = "/sd/settings/config.json"
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        print(f"Failed to read config: {e}")
        return None


config = read_config()
read_sensors()

_SENSORS_FILE="/sd/data.csv"

_SLEEP_TIME = config.get("sleep time", 1) * 60


header=False
try:os.stat(_SENSORS_FILE)
except:header=True
pen = open(_SENSORS_FILE,"a+")
if header: pen.write('temperatura(C),umidade(%),pressao(Pa),gas(ohms),luminisidade(%)\n')
print("Saving:{},{},{},{},{};".format(temp,hum,pres,gas,lumin))
pen.write("{},{},{},{},{}\n".format(temp, hum, pres, gas, lumin))        
pen.close()

print("Done")
print(_SLEEP_TIME)
machine.deepsleep(_SLEEP_TIME*1000)
