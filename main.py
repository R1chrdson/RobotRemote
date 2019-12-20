from kivy.utils import platform
if platform == 'android':
    from kivy.core.window import Window
    Window.softinput_mode = 'pan'
    from jnius import autoclass
    BluetoothDevice = autoclass('android.bluetooth.BluetoothDevice')
    BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
    BluetoothSocket = autoclass('android.bluetooth.BluetoothSocket')
    BufferedReader = autoclass('java.io.BufferedReader')
    InputStream = autoclass('java.io.InputStreamReader')
    UUID = autoclass('java.util.UUID')
    CharBuilder = autoclass('java.lang.Character')
else:
    Config.set('graphics', 'resizable', '0')
    Config.set('graphics', 'width', '960')
    Config.set('graphics', 'height', '510')

from kivy.uix.spinner import Spinner
from kivy.uix.dropdown import DropDown

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.slider import Slider
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.scrollview import ScrollView
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.filechooser import FileChooserListView
from kivy.logger import Logger
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.config import ConfigParser, Config
from functools import partial
import os
import time    
import socket
import layouts

class Choose(BoxLayout):
    def __init__(self, **kwargs):
        super(Choose, self).__init__(**kwargs)
        Clock.schedule_once(self.elementSetup, 0)
    
    def elementSetup(self, dt):
        app = App.get_running_app()
        if self.group == 'arms':
            if app.root.arms == 1:
                self.ids.first.state = 'down'
                self.ids.second.state = 'normal'
            else:
                self.ids.first.state = 'normal'
                self.ids.second.state = 'down'
        if self.group == 'engines':
            if app.root.engines == 1:
                self.ids.first.state = 'down'
                self.ids.second.state = 'normal'
            else:
                self.ids.first.state = 'normal'
                self.ids.second.state = 'down'
        if self.group == 'modes':
            if app.commands['ELEMENTS']['MODES'] == '1':
                self.ids.first.state = 'normal'
                self.ids.second.state = 'down'
            else:
                self.ids.first.state = 'down'
                self.ids.second.state = 'normal'
        

    def changeSettings(self, state, refer):
        if(state == 'normal'):
            refer.size_hint_y = 0
            refer.pos_hint = {'top': 2}
        else:
            refer.size_hint_y = 0.8
            refer.pos_hint = {'top': .8}
    
    def switchMode(self, state, command):
        if state == 'down':
            root = App.get_running_app().root
            if command == 'off':
                root.ids.statusLayout.ids.modes.pos_hint = {'top': 2}
                root.ids.mode.text = ''
            else:
                root.ids.statusLayout.ids.modes.pos_hint = {'top': 1}
                root.ids.mode.text = root.ids.statusLayout.getMode()

class SensorsButton(ToggleButton):
    def showSensors(self, refer, state):
        app = App.get_running_app()
        if(state == 'normal'):
            app.root.ids.mainScreen.disabled = False
            refer.pos_hint = {'top': 4}
            Clock.unschedule(app.update)
        else:
            app.root.ids.mainScreen.disabled = True 
            refer.pos_hint = {'top':.8}
            app.update = Clock.schedule_interval(self.updateSensors, float(app.commands['SENSORS']['REFRESH']))
            if app.root.ids.settings.state == 'down':
                app.root.ids.settings.state = 'normal'
                app.root.ids.settings.changeScreen()
            if app.root.ids.statusLayout.size_hint_y == .8:
                app.root.ids.status.mode()
           
    def updateSensors(self, dt): # update sensors
        if App.get_running_app().connected:
            command = App.get_running_app().commands['SENSORS']['command']
            App.get_running_app().send([int(command)])
            data = App.get_running_app().root.ids.sensorsLayout.children[0].children[0].children
            for value in data:
                byte = App.get_running_app().read()
                App.get_running_app().root.notification('Sensors', str(byte))
                if value == 'temperature':
                    value.data = str((byte[0]*256 + byte[1])*0.00268-46.85)
                elif value == 'humidity':
                    value.data = str((byte[0]*256 + byte[1])*0.00191-6)
                else:
                    value.data = str(byte[0]*256 + byte[1])

class SettingsButton(ToggleButton):
    def changeScreen(self):
        app = App.get_running_app()
        if self.state == 'down':
            app.root.ids.settingsLayout.ids.action.text = 'Choose action'
            Clock.unschedule(app.newData)
            if app.root.ids.statusLayout.size_hint_y == .8:
                app.root.ids.status.mode()
            if app.root.ids.sensors.state == 'down':
                app.root.ids.sensors.state = 'normal'
                app.root.ids.sensors.showSensors(app.root.ids.sensorsLayout, app.root.ids.sensors.state)
        if self.state == 'normal':
            arms = app.root.arms
            engines = app.root.engines
            newArms, newEngines = arms, engines
            if app.root.ids.settingsLayout.ids.arms.ids.first.state == 'down':
                newArms = 1
            else:
                newArms = 2
            if app.root.ids.settingsLayout.ids.engines.ids.first.state == 'down':
                newEngines = 1
            else:
                newEngines = 2
            if newArms != arms or newEngines != engines:
                app.root.arms = newArms
                app.root.engines = newEngines
                app.root.changeLayout()
            if app.updateSettings:
                for section in app.updateSettings.keys():
                   for variable in app.updateSettings[section].keys(): 
                        try:
                            globals = {'app': app, 'section': section, 'variable': variable}
                            locals = {}
                            exec('app.root.ids.mainScreen.children[0].ids.{}.{} = app.updateSettings[section][variable]'.format(section.lower(), variable), globals, locals)
                        except Exception as e:
                            app.root.notification('Settings update', e)
                app.updateSettings = {}
            

            app.newData = Clock.schedule_interval(app.sendNewData, .075)
        if self.layout.size_hint_y == 0:
            self.layout.size_hint_y = .8 
        else:
            self.layout.size_hint_y = 0

class MyFileChooser(FileChooserListView):
    def on_submit(self, *args):
        App.get_running_app().loadFromFile(*args[0])

class SettingsLayout(ScrollView):
    def bluetoothDevices(self):
        try:
            paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
            self.ids.deviceList.remove_widget(self.ids.deviceList.children[0])
            self.ids.deviceList.add_widget(BoxLayout(size_hint=(1, len(paired_devices) / 3), orientation='vertical'))
            App.get_running_app().root.notification('BluetoothDevices', str(len(paired_devices)) + ' devices were found')
            if paired_devices:
                for device in paired_devices:
                    self.ids.deviceList.children[0].add_widget(ToggleButton(text=str(device.getName()), group='device', allow_no_selection=False))
                self.ids.deviceList.children[0].children[0].state = 'down'
        except Exception as e:
            App.get_running_app().root.notification('BluetoothDevices', e)

    def commandsAction(self, text):
        if text == 'Load':
            try:
                self.ids.option.text = 'Choose option'
                self.ids.option.setOptions(MyFileChooser(path='.'))
            except Exception as e:
                App.get_running_app().root.notification('Load', e)
        if text == 'Save':
            if self.ids.option.text != 'Choose option':
                App.get_running_app().commands.write()
                App.get_running_app().root.notification('Commands', 'saved')
            else:
                self.ids.action.text = 'Choose action'
        if text == 'Default': 
            self.ids.option.text = 'Choose option'
            App.get_running_app().loadFromFile('default.ini')
            App.get_running_app().root.notification('Commands', 'defaults are loaded')

class SettingsSpinner(Spinner):
    def __init__(self, **kwargs):
        super(SettingsSpinner, self).__init__(**kwargs)
        Clock.schedule_once(self.finishInit, 0)

    def finishInit(self, dt):
        self.values = App.get_running_app().commands.sections()

    def setOptions(self, widget=None):
        content = App.get_running_app().root.ids.settingsLayout.ids.content
        content.children[0].remove_widget(content.children[0].children[0])
        content.children[0].add_widget(ScrollView())
        if widget:
            print(widget)
            content.children[0].children[0].add_widget(widget)

    def showSettings(self):
        if self.text != 'Choose option':
            App.get_running_app().root.ids.settingsLayout.ids.action.text = 'Choose action'
            values = App.get_running_app().commands.items(self.text)
            scroll = ScrollView()
            scroll.add_widget(BoxLayout(padding = [0, 0, 0, 50], orientation = 'vertical', size_hint = (1, len(values)*.33 + .05)))
            self.setOptions(scroll)
            for value in values:
                scroll.children[0].add_widget(MyInput(section=self.text, variable=value[0], default=value[1], posX = .1, posY = .5, inputHeight = .5))

class SensorsData(BoxLayout):
    name = StringProperty()
    data = StringProperty()
    posNameX = NumericProperty()
    posDataX = NumericProperty()    

class SensorsLayout(ScrollView):
    def __init__(self, **kwargs):
        super(SensorsLayout, self).__init__(**kwargs)
        Clock.schedule_once(self.finishInit, 0)

    def finishInit(self, dt):
        values = App.get_running_app().commands.items('SENSORS')
        layout = App.get_running_app().root.ids.sensorsLayout
        for value in values[2:]:
            layout.children[0].children[0].add_widget(SensorsData(name=value[0], data='None', posNameX = 0, posDataX = .3))

class MyInput(FloatLayout):
    def setVariable(self, value, variable):
        if variable == 'host':
            App.get_running_app().host = value
        elif variable == 'port':
            App.get_running_app().port = value
        else:
            App.get_running_app().commands.set(self.section, variable, value)
            if self.section in App.get_running_app().updateSettings.keys():
                App.get_running_app().updateSettings[self.section].update({variable:value})
            else:
                App.get_running_app().updateSettings.update({self.section:{variable:value}})

class MyJoystick(FloatLayout):
    def __init__(self, **kwargs):
        super(MyJoystick, self).__init__(**kwargs)
        Clock.schedule_once(self.finish_init, 0)

    def finish_init(self, dt):
        if not self.angle:
            self.remove_widget(self.ids.x)
            self.remove_widget(self.ids.xValue)
        self.ids.joypad.bind(pad=self.update)

    def update(self, joystick, pad):
        avg = (self.min + self.max) / 2
        mult = avg - self.min
        constant = self.velocitymax/self.multMax
        self.ids.xValue.text = str(round(pad[0]*mult + avg))
        self.ids.yValue.text = str(round(joystick.magnitude*constant*self.ids.multiply.ids.slider.value))

class StatusLayout(ScrollView):
    def getMode(self):
        for child in self.ids.modes.children:
            if child.state == 'down':
                return child.text

class Status(ButtonBehavior, BoxLayout):
    def mode(self):
        root = App.get_running_app().root
        if root.ids.statusLayout.size_hint_y == .8:
            root.ids.statusLayout.size_hint_y = 0
            if root.ids.statusLayout.getMode() != root.ids.mode.text and root.ids.settingsLayout.ids.modes.ids.first.state == 'normal':
                root.ids.mode.text = root.ids.statusLayout.getMode()
                if root.ids.mode.text == 'Manual':
                    App.get_running_app().send([0])
                    App.get_running_app().send([2])
        else:
            root.ids.statusLayout.size_hint_y = .8
            if root.ids.sensors.state == 'down':
                root.ids.sensors.state = 'normal'
                root.ids.sensors.showSensors(root.ids.sensorsLayout, root.ids.sensors.state)
            if root.ids.settings.state == 'down':
                root.ids.settings.state = 'normal'
                root.ids.settings.changeScreen()
       
class Container(FloatLayout):
    layout = None
    arms = 0
    engines = 0

    def __init__(self, **kwargs):
        super(Container, self).__init__(**kwargs)
        Clock.schedule_once(self.firstRun, 0)

    def firstRun(self, dt=0):
        self.arms = int(App.get_running_app().commands['ELEMENTS']['ARMSDEFAULT'])
        self.engines = int(App.get_running_app().commands['ELEMENTS']['ENGINESDEFAULT'])
        if App.get_running_app().commands['ELEMENTS']['MODES'] == '1':
            self.ids.settingsLayout.ids.modes.switchMode('down', 'on')
        else:
            self.ids.settingsLayout.ids.modes.switchMode('down', 'off')
        self.changeLayout()

    def changeLayout(self):        
        if self.layout:
            self.ids.mainScreen.remove_widget(self.layout)
        if self.arms == 1:
            if self.engines == 1:
                self.layout = layouts.Arm1Eng1()
            else:
                self.layout = layouts.Arm1Eng2()
        else:
            if self.engines == 1:
                self.layout = layouts.Arm2Eng1()
            else:
                self.layout = layouts.Arm2Eng2()
        self.ids.mainScreen.add_widget(self.layout)

    def notification(self, text, e):
        self.ids.notification.text = text + ': ' + str(e)
        Clock.schedule_once(self.clear, 5)

    def clear(self, dt):
        self.ids.notification.text = ''

class RemoteApp(App):
    method = None
    tcpSocket = socket.socket()
    bluetoothSocket = None
    host = '192.168.43.254'
    port = '7778'
    device = None
    update = None
    updateSettings = {}
    connected = False
    commands = ConfigParser()
    commands.read('settings.ini')
    previousState = {'GRIPPER1': int(commands['GRIPPER1']['VAL']), 
                     'ELBOW1': int(commands['ELBOW1']['VAL']), 
                     'SHOULDER1': int(commands['SHOULDER1']['VAL']), 
                     'GRIPPER2': int(commands['GRIPPER2']['VAL']), 
                     'ELBOW2': int(commands['ELBOW2']['VAL']), 
                     'SHOULDER2': int(commands['SHOULDER2']['VAL']), 
                     'ENGINE1':0,
                     'ENGINE2':0,
                     'DIRECTION1':0,
                     'DIRECTION2':0, 
                     'ANGLE': int((int(commands['ANGLE']['MAX']) + int(commands['ANGLE']['MIN']))/2)}

    def build(self):
        self.root = Container()
        self.newData = Clock.schedule_interval(self.sendNewData, .075)

    def loadFromFile(self, file):
        if file[-3:] != 'ini':
            self.root.notification('Load', 'wrong file extension')
            return
        commands = ConfigParser()
        commands.read(file)
        try:
            for section in commands.sections():
                for values in commands.items(section):
                    self.commands.set(section, values[0], values[1])
                    if section in self.updateSettings.keys():
                        self.updateSettings[section].update({values[0]:values[1]})
                    else:
                        self.updateSettings.update({section:{values[0]:values[1]}})
            self.root.notification('Load', 'load successful')
            App.get_running_app().root.ids.settingsLayout.ids.option.setOptions()
        except:
            self.root.notification('Load', 'wrong file')

    def sendNewData(self, dt):
        current = {'GRIPPER1':int(self.root.layout.ids.gripper1.value),
                   'GRIPPER2':int(self.root.layout.ids.gripper2.value) if self.root.arms == 2 else int(self.commands['GRIPPER2']['VAL']),
                   'ELBOW1':int(self.root.layout.ids.elbow1.value),
                   'ELBOW2':int(self.root.layout.ids.elbow2.value) if self.root.arms == 2 else int(self.commands['ELBOW2']['VAL']),
                   'SHOULDER1':int(self.root.layout.ids.shoulder1.value),
                   'SHOULDER2':int(self.root.layout.ids.shoulder2.value) if self.root.arms == 2 else int(self.commands['SHOULDER2']['VAL']),
                   'DIRECTION1':self.root.layout.ids.engine1.ids.joypad.pad_y,
                   'DIRECTION2':self.root.layout.ids.engine2.ids.joypad.pad_y if self.root.engines == 2 else 0,
                   'ENGINE1':int(self.root.layout.ids.engine1.ids.yValue.text),
                   'ENGINE2':int(self.root.layout.ids.engine2.ids.yValue.text) if self.root.engines == 2 else 0,
                   'ANGLE':int(self.root.layout.ids.engine1.xValue) if self.root.engines == 1 else 90}
        package = []
        for element in current.keys():
            if current[element] != self.previousState[element]:
                if element[:-1] == 'DIRECTION':
                    if current[element] > 0 and self.previousState[element] < 0:
                        package.append(int(self.commands['ENGINE'+element[-1]][element[:-1]]))
                        package.append(int(self.commands['ENGINE'+element[-1]][element[:-1] + 'F']))
                    elif current[element] < 0 and self.previousState[element] > 0:
                        package.append(int(self.commands['ENGINE'+element[-1]][element[:-1]]))
                        package.append(int(self.commands['ENGINE'+element[-1]][element[:-1] + 'B'])) 
                else:
                    package.append(int(self.commands[element]['COMMAND']))
                    package.append(current[element])
        
        self.previousState = current
        if len(package):
            self.send(package)

    def disconnect(self):
        try: 
            self.send([0])
        except Exception as e:
            self.root.notification('Send:', e)
        try:
            if self.method == 'TCP':
                self.tcpSocket.close()
            else: 
                self.bluetoothSocket.disconnect()
        except Exception as e:
            self.root.notification('Disconnect', e)
        self.method = None
        self.connected = False
        self.root.ids.statusLayout.ids.button.text = 'Connect'
        self.root.ids.statusLabel.text = 'Disconnected'

    def connect(self):
        method = 'TCP' if self.root.ids.settingsLayout.ids.method.ids.first.state == 'down' else 'Bluetooth'
        if method == self.method:
            self.disconnect()
        try:
            if method == 'TCP':
                self.tcpSocket = socket.socket()
                self.tcpSocket.settimeout(3)
                self.tcpSocket.connect((self.host, int(self.port)))
                self.tcpSocket.send([100])
            else:
                for device in self.root.ids.settingsLayout.ids.deviceList.children[0].children:
                    if device.state == 'down':
                        objectDevice = device
                paired_devices = BluetoothAdapter.getDefaultAdapter().getBondedDevices().toArray()
                for device in paired_devices:
                    if device.getName() == objectDevice.text:
                        self.bluetoothSocket = device.createRfcommSocketToServiceRecord(UUID.fromString("00001101-0000-1000-8000-00805F9B34FB"))
                        reader = InputStream(self.bluetoothSocket.getInputStream(), 'UTF-8')
                        self.bluetooth_recv = BufferedReader(reader, 1)
                        self.bluetooth_send = self.bluetoothSocket.getOutputStream()
                        break
                self.bluetoothSocket.connect()
            self.connected = True
            self.root.ids.statusLayout.ids.button.text = 'Disconnect'
            self.root.ids.statusLabel.text = 'Connected'
            self.method = method
        except Exception as e:
            self.root.notification('Connect', e)
        else:
            self.root.ids.statusLabel.text = 'Connected'
        
    def read(self):
        try:
            if self.method == 'TCP':
                return (self.tcpSocket.recv(1),self.tcpSocket.recv(1))
            else:
                return (self.bluetooth_recv.read(), self.bluetooth_recv.read())
        except Exception as e:
            self.root.notification('Read', e)

    def send(self, cmd):
        try:
            if self.method == 'TCP':
                self.tcpSocket.send(bytearray(cmd))
            else:
                self.bluetooth_send.write(bytearray(cmd))
                self.bluetooth_send.flush()
        except Exception as e:
            self.root.notification('Send', e)
            self.disconnect()
            
if __name__ == '__main__':
    RemoteApp().run()