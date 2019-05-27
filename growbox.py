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

def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
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

def main():
    pin = 24
    sensor = Adafruit_DHT.AM2302
    humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
    if humidity is not None and temperature is not None:
        readings = 'Temp={0:0.1f}*  Humidity={1:0.1f}%'.format(temperature, humidity)
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
        if fan == 'on':
            GPIO.setup(15, GPIO.LOW)
        else:
            GPIO.setup(15, GPIO.HIGH)
        if lights == 'on':
            GPIO.setup(18, GPIO.LOW)
        else:
            GPIO.setup(18, GPIO.HIGH)
        if humidity < 96:
            GPIO.setup(25, GPIO.LOW)
        else:
            GPIO.setup(25, GPIO.HIGH)
        print(readings + ' lights:' + lights + ' fan:' + fan)
    else:
        print('Failed to get reading. Trying again!')

schedule.every().day.at("06:00").do(run_threaded, lights_on)
schedule.every().day.at("18:00").do(run_threaded, lights_off)
schedule.every(60).minutes.do(run_threaded, takepic)
schedule.every(5).seconds.do(run_threaded, main)

while True:
    schedule.run_pending()
    time.sleep(1)
