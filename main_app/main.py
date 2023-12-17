import PySimpleGUI as sg
import serial
import logging
from pathlib import Path
import time
import threading
import requests
import datetime
import platform
import os
import cv2
import numpy as np
import pdb
import psutil
import subprocess as sp
import platform

if platform.system() != 'Windows':
    from picamera2 import Picamera2
    import RPi.GPIO as GPIO


FILE = Path(__file__).stem
logger = logging.getLogger(FILE)
logger.setLevel(logging.INFO)
logging.basicConfig(format = '%(levelname)s - %(message)s')

CIRCLE = '⚫'

def make_window(theme):
    sg.theme(theme)

    menu_def = [['Version', ['1.0.1']] , ['Help',['doc']]]
    #menu_def = [['&Application', ['E&xit']],
    #           ['&Help', ['&About']] ]
    test_ALARMS_FAN_layout = [
                [sg.Text('In this section, you can test the functionality of warning modules' , justification='center',font='Courier 10')],
                [sg.Text('Make a serial connection' , justification='left',font='Courier 8') ,sg.Button('connection' , key = '-CON-B'), sg.Text(CIRCLE , size=(10,1), font='Default 18', text_color='black', key='-OUT1-')], 
                [sg.HorizontalSeparator()],
                [sg.Text('Please set the alarm severity of the warning modules:',justification='left',font='Courier 8') , sg.Combo(values=('Low' , 'High') , default_value='Low' , readonly=True , k = '-COMBO-alarm-test-level-'),
                 sg.Button('ALARM test' , k='-do-alarm-B' , disabled=True)],
                [sg.Text(text ='...', k = '-info-text-' , font = 'Courier 10' , pad=(10,10) , text_color='orange')],
                [sg.HorizontalSeparator()],
                [sg.Text('CPU temperature is: 0' , k = '-cpu-temp-info-', justification='left',font='Courier 8')],
                [sg.Text('Please set the fan speed for test', justification='left',font='Courier 8'),sg.Combo(values=('Low' , 'High') , default_value='Low' , readonly=True , k = '-COMBO-fan-test-level-') , sg.Button('FAN test' , k='-do-fan-B' , disabled=True)]]
    
    test_IOT_layout = [[sg.Column([
                              [sg.Button('ping google', key='-ping-google-B-',size = (25, 2) , pad=(1,5))],
                              [sg.Button('open site', key='-open-site-B-',size = (25, 2), pad=(1,5))],
                              [sg.Button('send json to site', key='-send-json-B-',size = (25, 2), pad=(1,5))],
                              [sg.Button('get version from site', key='-get-version-B-',size = (25, 2), pad=(1,5))],
                              [sg.Button('send error to site', key='-send-error-B-' , size = (25, 2), pad=(1,5))]], pad=(0,0)),
                    sg.Multiline(size=(60,10), key='-info-multiline-iot-', font='Courier 8', expand_x=True, expand_y=True,
                                reroute_stdout=False, reroute_stderr=False, echo_stdout_stderr=True, autoscroll=True, auto_refresh=True)]]

    test_CAMERA_IR_layout = [[sg.Column([
                            [sg.Button('test camera' , key = '-test-camera-B-' ,size = (20,1)) ,],
                            [sg.Button('set IR', size=(20, 1), key='-IR-B-'),
                            sg.Slider((0, 255), 0, 1, orientation='v', size=(10, 3), key='-IR-level-S-')],
                            ]),
                            sg.Image(filename='',background_color= 'black', key='-IMAGE-test-camera-' , size = (500 , 400)),]
                        ]

    test_MEMORY_STARTUP_layout = [[sg.Text(f"\n\n\nthe free space that available in this system is:{psutil.disk_usage('/').free / (2**30)} GIB" , justification='left',font='Courier 14')],
                                  [sg.HorizontalSeparator()],
                                  [sg.Text(f"\n\nstartup file must be placed in this directory:\n home/nasir/reboot.bin\n open file for check it..." , justification='left',font='Courier 12') ],
                                  [sg.Button('open file' , key="-open-file-" , pad = 10),]
                                  ]
    test_MODElS_layout =  [[sg.Column([
                              [sg.Button('open camera', key='-open-camera-B-',size = (25, 2) , pad=(1,5))],
                              [sg.Button('test sunglassess', key='-test-sunglassess-B-',size = (25, 2), pad=(1,5))],
                              [sg.Button('test mask', key='-test-mask-B-',size = (25, 2), pad=(1,5))],
                              [sg.Button('test mobile', key='-test-mobile-B-',size = (25, 2), pad=(1,5))],
                              ], pad=(0,0)),
                                sg.Image(filename='',background_color= 'black', key='-IMAGE-test-models-' , size = (500 , 400)),]
                        ]
    test_GPS_layout = []

    layout = [[sg.MenubarCustom(menu_def , key = '-MENU-' , font = 'Courier 10' , tearoff=False)],
              [sg.Text("Test Platform of FMS embedded systems" , size = (60,1) ,justification='center', font=("Helvetica", 16), relief=sg.RELIEF_RIDGE, k='-TEXT HEADING-')],
              [sg.TabGroup([[
                  sg.Tab("Alarms/Fan test" , test_ALARMS_FAN_layout),
                  sg.Tab("IOT test" , test_IOT_layout),
                  sg.Tab("Camera/IR test" , test_CAMERA_IR_layout),
                  sg.Tab("Memory/Startup test" , test_MEMORY_STARTUP_layout),
                  sg.Tab("Models test" , test_MODElS_layout),
                  sg.Tab("GPS test" , test_GPS_layout),
                ]], key='-TAB GROUP-', expand_x=True, expand_y=True)]
              ]
    
    window = sg.Window("TEST GUI" , layout=layout,  grab_anywhere=True , resizable= True , margins=(0,0) , use_custom_titlebar=True , finalize=True , keep_on_top=False)
    window.set_min_size(window.size)
    return window


class FMSSys():
    serial_connection = False
    time_to_sleep = 0
    _os = platform.platform().split('-')[0]


    def __init__(self):
        self.UUID = '685b1c0a-8cd7-4bc2-ae5a-6c62a97e8c25'
        self.URL = "https://fms.drivingsimulator.ir/"
        self.VERSION_URL = f"https://fms.drivingsimulator.ir/api/{self.UUID}/version"
        self.ERROR_HANDLER_URL = "https://fms.drivingsimulator.ir/api/device/error"

        self.headers = {
            "Authorization": "Bearer 1|kAEypoKd8oDrGpOQqJPY5yZDt6FC8scgFgRHRlkv"
        }

        self.demo_temps = [34,35,36,36,37,38]

        self.ir_value = 0

        self.window_tab = ''

    def create_serial_connection(self):
        try:
            self.ser = serial.Serial(port='/dev/ttyS0',
                                            baudrate=9600,
                                            parity=serial.PARITY_NONE,
                                            stopbits=serial.STOPBITS_ONE,
                                            bytesize=serial.EIGHTBITS,
                                            timeout=1)
            self.serial_connection = True
        except: 
            logger.info("some thing wrong in make serial connection")
            self.serial_connection = False
    ############ change some things in last realese
    def do_alarm(self , level):

        if level == 'High':
            message = b'thr \r\n'
            self.time_to_sleep = 5
        elif level == 'Low':
            message = b'one \r\n'
            self.time_to_sleep = 3
        if self.serial_connection:
            print(f"alarming... {message}")
            GPIO.output(self.pin_num, GPIO.HIGH)
            self.ser.write(message)
            return self.time_to_sleep
            #time.sleep(self.time_to_sleep)
    
    def ping_google(self , window) -> bool:
        if (lambda a: True if 0 == a.system('ping google.com -w 4 > clear') else False)(__import__('os')):
            with open('./clear' , mode = 'rt') as f:
                data = f.read()
            window['-info-multiline-iot-'](value = data + '\n reach the internet successfully...')
        else: window['-info-multiline-iot-'](value = 'cant reach the internet...')

    def open_site(self , window):
        connection = requests.get(self.URL, headers=self.headers, timeout = (3, 5))
        time.sleep(2)
        window['-info-multiline-iot-'](value = connection.text + f'\n\n\n\n{connection.status_code}')
        return 'ack'
    
    def send_json_to_site(self , json , window):
        connection = requests.post(self.URL, json=json, headers=self.headers)
        window['-info-multiline-iot-'](value = connection.text + f'\n\n\n\n{connection.status_code}')
        return 'ack'
    
    def get_version_from_site(self , window):
        connection = requests.get(self.VERSION_URL, headers=self.headers, timeout = (3, 5))
        window['-info-multiline-iot-'](value = connection.text + f'\n\n\n\n{connection.status_code}')
        return 'ack'
    
    def send_error_to_site(self , window):
        error_handler_text={
            "uuid": self.UUID,
            "message" : 'check error handler'
        }
        connection = requests.post(self.ERROR_HANDLER_URL , json = error_handler_text, headers=self.headers)
        window['-info-multiline-iot-'](value = connection.text + f'\n\n\n\n{connection.status_code}')
        return 'ack'
    
    def fan_test(self , level):
        if self._os == 'Windows':
            print(f'the fan speed is {level}')

        ####### maybe it must be chage
        elif self._os == 'Rasberian':
            # GPIO.setwarnings(False)
            # GPIO.setmode(GPIO.BOARD)
            # if level == 'Low':
            #     GPIO.output(self.pin_num, GPIO.LOW)
            # elif level == 'High':
            #     GPIO.output(self.pin_num, GPIO.HIGH)
            pass


    def check_cpu_temp(self , window):
        if self._os == 'Windows':
            temp_index = -1
            while True:
                temp_index += 1
                if temp_index >= len(self.demo_temps):
                    temp_index = 0
                time.sleep(2)
                window['-cpu-temp-info-'](value = f'CPU temperature is: {self.demo_temps[temp_index]}')
            
        elif self._os == 'Rasberian':
            while True:
                time.sleep(2)
                temp = os.popen("vcgencmd measure_temp").readline().split('=')[1].split('\'')[0]
                window['-cpu-temp-info-'](value = f'CPU temperature is: {temp}')
    
    def camera_test(self , window):
        # t1 = t2 = time.time()
        if self._os == 'Windows':
            cap = cv2.VideoCapture(0)
            while self.window_tab in ['Camera/IR test','Models test']:
                ret, self.frame = cap.read()
                frame = cv2.resize(self.frame, (500,400), interpolation = cv2.INTER_LINEAR)
                if ret:
                    imgbytes = cv2.imencode('.png', frame)[1].tobytes()
                    window['-IMAGE-test-camera-'].update(data=imgbytes)
                    window['-IMAGE-test-models-'].update(data=imgbytes)
                    # t2 = time.time()
            
            window['-test-camera-B-'](disabled = False)
            window['-open-camera-B-'](disabled = False)

            return 'ack'

        elif self._os == 'Rasberian':
            # frame_size = (640, 480)
            # cap = Picamera2()
            # cap.configure(cap.create_preview_configuration(main={"format": 'XRGB8888', "size": frame_size}))
            # cap.start()
            # self.frame= cap.capture_array()

            # while self.window_tab == 'Camera/IR test':
            #     ret = False
            #     self.frame= cap.capture_array()
            #     if self.frame is not None:
            #         ret = True

            #     if not ret:
            #         self.frame = None
                
            #     if ret:
            #         frame = cv2.resize(self.frame, (500,400), interpolation = cv2.INTER_LINEAR)
            #         imgbytes = cv2.imencode('.png', frame)[1].tobytes()
            #         window['-IMAGE-test-camera-'].update(data=imgbytes)
            #         window['-IMAGE-test-models-'].update(data=imgbytes)
            
            # window['-test-camera-B-'](disabled = False)
            # window['-open-camera-B-'](disabled = False)

            # window['-test-camera-B-'](disabled = False)
            return 'ack'
    
    def set_ir(self):
        pin_num = 33
        frequency = 1000
        # GPIO.setup(pin_num, GPIO.OUT)
        if self._os == 'Windows':
            print(self.ir_value)

        if self._os == 'Rasberian':
            # pwm = GPIO.PWM(self.pin_num, self.frequency)
            # pwm.start(0)

            # while True:
            #     pwm.ChangeDutyCycle(self.value)
            #     time.sleep(2)
            # return 'ack'
            pass
    
    def open_file_in_notepad(self, file_dir):
        if self._os == 'Windows':
            programName = "notepad.exe"
            fileName = file_dir
            sp.Popen([programName, fileName])

        elif self._os == 'Rasberian':
            pass
            
def do_sleep_for_app(window , time_to_sleep):
    for t in range(time_to_sleep + 1):
        window['-info-text-'](value = f'{time_to_sleep - t} second to finish testing ')
        time.sleep(.9)
    window['-info-text-'](value = 'finish testing')


def fill_json_frame_window() -> dict:
    layout = [[sg.Text('Device uuid:')],
            [sg.Input(key='-device-uuid-win2', size=(35,1) , default_text =  '685b1c0a-8cd7-4bc2-ae5a-6c62a97e8c25' , disabled=True)],
            [sg.Text('awareness level:')],
            [sg.Input(key='-awareness-level-win2-',default_text = '2.5' ,size=(35,1) , disabled= True)],
            [sg.Text('time stamp:')],
            [sg.Input(key='-time-stamp-win2-', size=(35,1) , default_text = str(datetime.datetime.now()) , disabled= True)],
            [sg.Text('Error:')],
            [sg.Input(key='-error-win2-', size=(35,1) , default_text = 'None' , disabled= True)],
            [sg.Text('driver id:')],
            [sg.Input(key='-driver-id-win2-', size=(35,1) , default_text = '2' ,disabled= True)],
            [sg.Text('driver visible:')],
            [sg.Input(key='-driver-visible-win2-', size=(35,1) , default_text = 'True' , disabled= True)],
            [sg.Text('latitude:')],
            [sg.Input(key='-lat-win2-', size=(35,1) , default_text = '1.234' , disabled= True)],
            [sg.Text('longitude:')],
            [sg.Input(key='-long-win2-', size=(35,1) , default_text = '4.321' , disabled= True)],
            [sg.Button("Done" , key = '-done-'),]
            ]

    window2 = sg.Window("Json file" , layout=layout,  grab_anywhere=True , resizable= True , margins=(0,0) , use_custom_titlebar=True , finalize=True , keep_on_top=True )
    window2.set_min_size(window2.size)
    while True:
        event2 , values2 = window2.read(timeout = 100)

        if event2 in ('-done-'):
            window2.close()
            return values2
        if event2 == None:
            window2.close()


          
def dict_to_valid_json(values):
    json={
            "device_uuid": values['-device-uuid-win2'],
            "level": int(float(values['-awareness-level-win2-'])),
            "timestamp": values['-time-stamp-win2-'],
            "error": values['-error-win2-'],
            "driver_id": values['-driver-id-win2-'],
            "driver_visible": bool(values['-driver-visible-win2-']),
            "lat": float(values['-lat-win2-']),
            "long": float(values['-long-win2-'])
        }
    return json


def main():
    window = make_window(sg.theme('Dark2'))
    FMSsys = FMSSys()
    temp_flag = True           

    while True:

        event , values = window.read(timeout=100)
        # print(values['-TAB GROUP-'])

        # print(event,  values)
        FMSsys.window_tab = values['-TAB GROUP-']
        # print(FMSsys.window_tab)

        if temp_flag:
            threading.Thread(target=FMSsys.check_cpu_temp, args=(window,), daemon=True).start()
            temp_flag = False

        if event in (None , "Exit"):
            print("exit button has been clicked...")
            break

        if event == "version":
            sg.popup("version of the this app : 1.0.1")
        
        ######## change some thing in this part for last realeas
        if event == "-CON-B":
            FMSsys.create_serial_connection()
            if FMSsys.serial_connection and window['-info-text-'] in ['finish testing', '...']:
                window['-OUT1-'](text_color = 'green')
                window['-do-alarm-B'](disabled=False)
            else:
                window['-OUT1-'](text_color = 'orange')
                if window['-info-text-'].__dict__['DisplayText'] in ['finish testing', '...']:
                    window['-do-alarm-B'](disabled = False)
                    window['-do-fan-B'](disabled = False)
                # print(window['-info-text-'].__dict__)
                # window['-do-alarm-B'](disabled=True)
        ########

        if event == '-do-alarm-B':
            time_to_sleep = FMSsys.do_alarm(values['-COMBO-alarm-test-level-'])
            threading.Thread(target=do_sleep_for_app, args=(window,time_to_sleep), daemon=True).start()
        
        if (window['-info-text-'].__dict__['DisplayText'] in ['finish testing', '...']) and FMSsys.serial_connection:
            window['-do-alarm-B'](disabled = False)
            window['-do-fan-B'](disabled = False)
        else: 
            window['-do-alarm-B'](disabled = True)
            window['-do-fan-B'](disabled = True)

        if event == '-ping-google-B-':
            threading.Thread(target=FMSsys.ping_google, args=(window,), daemon=True).start()
        
        if event == '-open-site-B-':
            threading.Thread(target=FMSsys.open_site, args=(window,), daemon=True).start()

        if event == '-send-json-B-':
            json = dict_to_valid_json(fill_json_frame_window())
            threading.Thread(target=FMSsys.send_json_to_site, args=(json, window,), daemon=True).start()
           
        if event == '-get-version-B-':
            threading.Thread(target=FMSsys.get_version_from_site, args=(window,), daemon=True).start()
            
        
        if event == '-send-error-B-':
            threading.Thread(target=FMSsys.send_error_to_site, args=(window,), daemon=True).start()


        if event == '-do-fan-B':
            FMSsys.fan_test(values['-COMBO-fan-test-level-'])

        if event == '-open-camera-B-':
            event = '-test-camera-B-'

        if event == '-test-camera-B-':
            window['-test-camera-B-'](disabled = True)
            window['-open-camera-B-'](disabled = True)
            threading.Thread(target =FMSsys.camera_test , args = (window,) , daemon= True).start()

        if event == '-IR-B-':
            FMSsys.ir_value = values['-IR-level-S-']
            threading.Thread(target = FMSsys.set_ir , daemon= True).start()

        if event == '-open-file-':
            file = sg.popup_get_file('Choose your start up file', keep_on_top=True)
            FMSsys.open_file_in_notepad(file)


        




if __name__ == '__main__':
    # sg.theme('black')
    # sg.theme('dark red')
    # sg.theme('dark green 7')
    # sg.theme('DefaultNoMoreNagging')
    main()

