import os
import time
import utime
from machine import Pin, Timer, SoftI2C, ADC, Timer, RTC, SDCard
import machine
import bme680 
import RGBLib
import i2smic
import random
import struct
import ujson as json

# LED CONTROLLER
LED = RGBLib.Controller(4,26,27)

# LDR SENSOR (ANALOGIC INTERFACE)
adc = ADC(Pin(34), atten=ADC.ATTN_6DB) #10kOhm - 3.3v
_MAXL = 65535

# BMP680 SENSOR (I2C INTERFACE)
i2c = SoftI2C(scl=Pin(22), sda=Pin(21))
bme = bme680.BME680_I2C(i2c=i2c)

#TIMERS
UPDTimer=Timer(2)
lumin, temp, hum, pres, gas = 0,0,0,0,0

#SDCard Controller
_SD=None
try:
     _SD = SDCard(slot=2)
     os.mount(_SD, "/sd") 
except:_SD=None

IMUTimer=Timer(2)
random.seed(123)

#MAIN SENSOR CYCLE
def read_sensors(t):
    global lumin, temp, hum, pres, gas, bme
    print("Collecting Sample")
    lumin = round(lumin+(adc.read_u16() / _MAXL * 100),2)
    temp = round(temp+(bme.temperature), 2)
    hum = round(hum+(bme.humidity), 2)
    pres = round(pres+(bme.pressure), 2) #avg sea level: 1013,25 
    gas = round(gas+((bme.gas/1000)), 2) #values ranges in https://cdn-shop.adafruit.com/product-files/3660/BME680.pdf
    #print("Sampling: {},{},{},{},{},{};".format(time.time(),temp,hum,pres,gas,lumin))

def mean_sensor():
    global lumin, temp, hum, pres, gas, bme
    print("Mean Sample")
    lumin = round(lumin/_SAMPLES_LOOPS,2)
    temp = round(temp/_SAMPLES_LOOPS, 2)
    hum = round(hum/_SAMPLES_LOOPS, 2)
    pres = round(pres/_SAMPLES_LOOPS, 2) #avg sea level: 1013,25 
    gas = round(gas/_SAMPLES_LOOPS, 2) 

#Gets the last record on the SDCard and return the new filename
def new_file():
     FCount = 0
     FPath="/sd/record_{}.wav"
     try: 
          while os.stat(FPath.format(FCount)):
               FCount+=1
     except:pass
     return FPath.format(FCount)

def read_config():
    config_path = "/sd/settings/config.json"
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
            return config
    except Exception as e:
        print(f"Failed to read config: {e}")
        return None

#Customizando o time
def custom_strftime(format, t):
    # Dicionário para mapear os códigos de formatação
    formats = {
        "%Y": str(t[0]),
        "%m": '{:02}'.format(t[1]),
        "%d": '{:02}'.format(t[2]),
        "%H": '{:02}'.format(t[3]),
        "%M": '{:02}'.format(t[4]),
        "%S": '{:02}'.format(t[5]),
    }
    
    # Substituir os códigos no formato fornecido
    for key, value in formats.items():
        format = format.replace(key, value)
    
    return format

#LOAD BLE

cond = False

_CLOCK=RTC()

try:
     _=os.stat("/timeflag.tmp")
     cond = True 
except:
     with open("/timeflag.tmp","w") as fp:
          fp.write("ok")
     pass
        

if(cond == True):
     #I2s Microphone
     _MIC = i2smic.Controller()
     _SENSORS_FILE="/sd/data.csv"

     obj_time = utime.localtime()
     time_record = custom_strftime("%H_%M_%S", obj_time)

     _AUDIO_FILE="/sd/record-{}".format(time_record)

     config = read_config()
     if config:
          _AUDIO_LENGTH = config.get("duty cicle", 1) * 60  # Captura em minutos convertida para segundos
          _SLEEP_TIME = config.get("sleep cicle", 5) * 60  # Tempo de sono em minutos convertido para segundos
          _SAMPLES_LOOPS = 5

     else:
          _AUDIO_LENGTH = 300  # Padrão de 5 minutos de coleta se o arquivo config não for lido
          _SAMPLES_LOOPS = 5
          _SLEEP_TIME = 900  # Padrão de 15 minutos de sleep se o arquivo config não for lido
     
     _READINGS_INTERVAL = int(((_AUDIO_LENGTH/60) / _SAMPLES_LOOPS)*60)

     print("Now is",time_record)
     LED.off()

     UPDTimer.init(period=_READINGS_INTERVAL*1000, mode=Timer.PERIODIC, callback=read_sensors)

     _MIC.record(_AUDIO_FILE)
     time.sleep(_AUDIO_LENGTH)
     UPDTimer.deinit()
     _MIC.stop()
     mean_sensor()
     #_MIC.aumentar_volume(2)
     

     header=False
     try:os.stat(_SENSORS_FILE)
     except:header=True
     pen = open(_SENSORS_FILE,"a+")
     if header: pen.write('timestamp,temperatura(C),umidade(%),pressao(Pa),gas(ohms),luminisidade(%),audio\n')
     print("Saving: {},{},{},{},{},{};".format(time_record,temp,hum,pres,gas,lumin,_AUDIO_FILE))
     pen.write("{},{},{},{},{},{},{}\n".format(time_record, temp, hum, pres, gas, lumin, _AUDIO_FILE))        
     pen.close()
        
     print("Done")
     machine.deepsleep(_SLEEP_TIME*1000)
else:
     LED.boot()
     machine.deepsleep(1000)
