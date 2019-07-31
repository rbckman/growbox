#!/usr/bin/python

import sys
import os
import glob
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
import schedule
import threading
GPIO.setmode(GPIO.BCM)

# Try to grab a sensor reading.  Use the read_retry method which will retry up
# to 15 times to get a sensor reading (waiting 2 seconds between each retry).

humidifier = False
GPIO.setup(25, GPIO.HIGH)

pin = 24
sensor = Adafruit_DHT.DHT22

try:
    with open('/home/pi/growbox/humidifier', 'r') as f:
        hum_settings = f.read().splitlines()
except:
    hum_settings = [5, 30]

def run_threaded(job_func, *my_args):
    job_thread = threading.Thread(target=job_func, args=my_args)
    job_thread.start()

def lights_on():
    with open('/home/pi/growbox/lights', 'w') as f:
        f.write('on')

def lights_off():
    with open('/home/pi/growbox/lights', 'w') as f:
        f.write('off')

def fan_on():
    with open('/home/pi/growbox/fan', 'w') as f:
        f.write('on')

def fan_off():
    with open('/home/pi/growbox/fan', 'w') as f:
        f.write('off')

def takepic():
    print('taking picture')
    os.system('raspistill -w 1920 -h 1080 -dt -o /home/pi/camera/growbox%d.jpeg')
    list_of_files = glob.glob('/home/pi/camera/*')
    latest_file = max(list_of_files, key=os.path.getctime)
    os.system('convert ' + latest_file + ' -resize 50% /home/pi/growbox.jpeg')

def mist_on(sec):
    print('turning on humidifier')
    GPIO.setup(15, GPIO.LOW)
    time.sleep(400)
    GPIO.setup(25, GPIO.LOW)
    time.sleep(sec)
    print('turning humidifier off')
    GPIO.setup(25, GPIO.HIGH)
    GPIO.setup(15, GPIO.HIGH)


def mist_off():
    print('turning humidifier off')
    GPIO.setup(25, GPIO.HIGH)

#schedule.every().day.at("06:00").do(run_threaded, lights_on)
#schedule.every().day.at("18:00").do(run_threaded, lights_off)
schedule.every(60).minutes.do(run_threaded, takepic)
schedule.every(int(hum_settings[0])).minutes.do(run_threaded, mist_on, int(hum_settings[1])).tag('humidifier')

while True:
    schedule.run_pending()
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        if humidifier == True:
            readings = 'Temp={0:0.1f}* Humidity={1:0.1f}% Humidifier:on'.format(temperature, humidity)
        else:
            readings = 'Temp={0:0.1f}* Humidity={1:0.1f}% Humidifier:off'.format(temperature, humidity)
        with open('/home/pi/growbox/readings', 'w') as f:
            f.write(readings)
    try:
        with open('/home/pi/growbox/fan', 'r') as f: 
            fan = f.read().splitlines()[0]
    except:
        fan = 'off'
    try:
        with open('/home/pi/growbox/lights', 'r') as f:
            lights = f.read().splitlines()[0]
    except:
        lights = 'off'
    try:
        with open('/home/pi/growbox/humidifier', 'r') as f:
            hum_new_settings = f.read().splitlines()
    except:
        hum_new_settings = hum_settings
    if hum_new_settings != hum_settings:
        print('got new humidifier settings')
        schedule.clear('humidifier')
        hum_settings = hum_new_settings
        schedule.every(int(hum_settings[0])).minutes.do(run_threaded, mist_on, int(hum_settings[1])).tag('humidifier')
    #if fan == 'on':
    #    GPIO.setup(15, GPIO.LOW)
    #else:
    #    GPIO.setup(15, GPIO.HIGH)
    if lights == 'on':
        GPIO.setup(18, GPIO.LOW)
    else:
        GPIO.setup(18, GPIO.HIGH)
    if humidifier == False and humidity < 95.5:
        humidifier = True
        #GPIO.setup(25, GPIO.LOW)
        #print('turning on humidifier')
    if humidifier == True and humidity >= 99.9:
        humidifier = False
        #GPIO.setup(25, GPIO.HIGH)
        #print('turning humidifier off')
    print(readings + ' lights:' + lights + ' fan:' + fan)
    print(schedule.jobs)
    time.sleep(3)
