import os, json, urllib, ssl, base64
from urllib.request import urlopen, Request
import re
from AlexaSmartHome import *

import math, colorsys
import logging

SKILL_NAME = 'Alexicz'

ENDPOINT_ADAPTERS = Registry()

_LOGGER = logging.getLogger(__name__)

class DomoticzEndpoint(AlexaEndpoint):

    _device_ = None
    def getDevice(self):
        if self._device_ is None:
            self._device_ = self.handler.getDevice(self._endpointId)
        return self._device_

    def setHandler(self, handler):
        self.handler = handler
    
    def getProperty(self, name):
        #device = self.handler.getDevice(self._endpointId)
        device = self.getDevice()
        if   name == 'powerState':
            if device['Status'] == 'On':
                return 'ON'
            else:
                return 'OFF'
        elif name == 'lockState':
            if device['Status'] == 'On':
                return 'LOCKED'
            else:
                return 'UNLOCKED'
            return 'JAMMED'
        elif name == 'brightness':
            level = device['Level']
            maxLevel = device['MaxDimLevel']
            return int((float(level) * 100) / float(maxLevel))
            #return round(self.entity.attributes['brightness'] / 255.0 * 100)
        elif name == 'percentage':
            level = device['Level']
            maxLevel = device['MaxDimLevel']
            return int((float(level) * 100) / float(maxLevel))
        elif name == 'colorTemperature':
            level = device['Level']
            maxLevel = device['MaxDimLevel']
            # Value to be returned 1000 to 10.000
            return 1000 + 9000 * (float(level) / float(maxLevel))
        elif name == 'temperature':
            if isinstance(self, ThermostatAlexaEndpoint):
                temp = device['SetPoint']
            else:
                temp = device['Temp']
            return {
                'value': float(temp),
                'scale': 'CELSIUS',
            }
        elif name == 'targetSetpoint':
            setPoint = device['SetPoint']
            return {
                'value': float(setPoint),
                'scale': 'CELSIUS',
            }
        elif name == 'thermostatMode':
            if isinstance(self, SelectorThermostatAlexaEndpoint):
                ilevel = int(device['Level']/device['LevelInt'])
                levels = device['LevelNames'].split("|")
                mode = levels[ilevel].upper()
                return mode
        elif name == 'detectionState':
            if device['Status'] == 'Closed':
                return 'NOT_DETECTED'
            else:
                return 'DETECTED'
            return 'JAMMED'
        return None

class OnOffAlexaEndpoint(DomoticzEndpoint):

    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaPowerController(self, 'Alexa.PowerController',[{'name': 'powerState'}]))

    def turnOn(self):
        self.handler.setSwitch(self._endpointId, 'On')

    def turnOff(self):
        self.handler.setSwitch(self._endpointId, 'Off')

@ENDPOINT_ADAPTERS.register('Scene')
class SceneAlexaEndpoint(DomoticzEndpoint):

    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaSceneController(self, 'Alexa.AlexaSceneController', deactivationSupported=False))

    def activate(self):
        self.handler.setSceneSwitch(self._endpointId, 'On')

    def deactivate(self):
        self.handler.setSceneSwitch(self._endpointId, 'Off')

@ENDPOINT_ADAPTERS.register('Group')
class GroupAlexaEndpoint(SceneAlexaEndpoint):

    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaSceneController(self, 'Alexa.AlexaSceneController', deactivationSupported=True))

@ENDPOINT_ADAPTERS.register('SwitchLight')
class SwitchLightAlexaEndpoint(OnOffAlexaEndpoint):

    def setPercentage(self, percentage):
        self.handler.setLevel(self._endpointId, percentage)

    def setBrightness(self, brightness):
        self.handler.setLevel(self._endpointId, brightness)

    def setColor(self, hue, saturation, brigthness):
        rgb = color_hsb_to_RGB(hue, saturation, brigthness)
        self.handler.setColor(self._endpointId, rgb, int (100*brigthness))

    def setColorTemperature(self, kelvin):
        # !! Convert 1000 to 10000 => 0..100 for dz :-) 
        dzKelvin = ((kelvin - 1000) * 100) / 10000
        self.handler.setKelvinLevel(self._endpointId, dzKelvin)

@ENDPOINT_ADAPTERS.register('Blind')
class BlindAlexaEndpoint(OnOffAlexaEndpoint):

    def turnOn(self):
        self.handler.setSwitch(self._endpointId, 'Off')

    def turnOff(self):
        self.handler.setSwitch(self._endpointId, 'On')

    def setPercentage(self, percentage):
        self.handler.setLevel(self._endpointId, percentage)

@ENDPOINT_ADAPTERS.register('RFY')
class RFYAlexaEndpoint(OnOffAlexaEndpoint):

    def turnOn(self):
        self.handler.setSwitch(self._endpointId, 'Off')

    def turnOff(self):
        self.handler.setSwitch(self._endpointId, 'On')

    def setPercentage(self, percentage):
        self.handler.setLevel(self._endpointId, percentage)

class LockableAlexaEndpoint(DomoticzEndpoint):
    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaLockController(self, 'Alexa.LockController',[{'name': 'lockState'}]))              

@ENDPOINT_ADAPTERS.register('Lock')
class LockAlexaEndpoint(LockableAlexaEndpoint):
    pass

@ENDPOINT_ADAPTERS.register('Contact')
class ContactAlexaEndpoint(DomoticzEndpoint):
    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaContactSensor(self, 'Alexa.ContactSensor',[{'name': 'detectionState'}]))

@ENDPOINT_ADAPTERS.register('TemperatureSensor')
class TemperatureSensorAlexaEndpoint(DomoticzEndpoint):

    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaTemperatureSensor(self, 'Alexa.TemperatureSensor',[{'name': 'temperature'}]))

    def setTargetSetPoint(self, targetSetPoint):
        pass

    def setThermostatMode(self, mode):
        pass

@ENDPOINT_ADAPTERS.register('Thermostat')
class ThermostatAlexaEndpoint(DomoticzEndpoint):

    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        super().__init__(endpointId, friendlyName, description, manufacturerName)
        self.addCapability(AlexaTemperatureSensor(self, 'Alexa.TemperatureSensor',[{'name': 'temperature'}]))
        thermostatCapability = AlexaThermostatController(self, 'Alexa.ThermostatController',[{'name': 'targetSetpoint'}, {'name': 'thermostatMode'}])
        thermostatCapability.setModesSupported(["HEAT","COOL","AUTO","ECO","OFF"])
        self.addCapability(thermostatCapability)

    def setTargetSetPoint(self, targetSetPoint):
        self.handler.setTemp(self._endpointId, targetSetPoint)

    def setThermostatMode(self, mode):
        pass

@ENDPOINT_ADAPTERS.register('SelectorThermostat')
class SelectorThermostatAlexaEndpoint(DomoticzEndpoint):

    def setTargetSetPoint(self, targetSetPoint):
        #self.handler.setTemp(self._endpointId, targetSetPoint)
        pass

    def setThermostatMode(self, mode):
        self.handler.setLevelByName(self._endpointId, mode)

class Domoticz(object):

    def __init__(self,url,username=None,password=None):
        self.url = os.path.join(url, '')

        if url.startswith("https"):
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            httpsHandler = urllib.request.HTTPSHandler(context = context)
            opener = urllib.request.build_opener(httpsHandler)
            urllib.request.install_opener(opener)

        self.authorization = None
        if username is not None:
            credentials = '%s:%s' % (username, password)
            encoded_credentials = base64.b64encode(credentials.encode())
            self.authorization = b'Basic ' + encoded_credentials

        self.planID = -1
        self.includeScenesGroups = False
        self.prefixName = None
        self.config = None

    def configure(self, config):
        self.includeScenesGroups = config.includeScenesGroups
        self.planID = config.planID
        self.prefixName = config.prefixName
        self.config = config

    def api(self, query):
        url = self.url + "json.htm?" + query
        print("Domoticz API call %s", url)
        _LOGGER.debug("Domoticz API call %s", url)
        headers = { 'Content-Type': 'application/json' }
        if self.authorization is not None:
            headers['Authorization'] = self.authorization
        payload = urlopen(Request(url, None, headers)).read()
        return json.loads(payload.decode('utf-8'))

    def getEndpoint(self, request):
        endpointId = request['endpoint']['endpointId']
        items = endpointId.split("-")
        className = items[0]
        id = items[1]
        endpoint = ENDPOINT_ADAPTERS[className](id)
        if className == 'SwitchLight':
            endpoint.addCapability(AlexaPercentageController(endpoint, 'Alexa.PercentageController',[{'name': 'percentage'}]))
            endpoint.addCapability(AlexaBrightnessController(endpoint, 'Alexa.BrightnessController',[{'name': 'brightness'}]))
            endpoint.addCapability(AlexaColorController(endpoint, 'Alexa.ColorController'))
            endpoint.addCapability(AlexaColorTemperatureController(endpoint, 'Alexa.ColorTemperatureController'))
        elif className == 'Blind' or className == 'RFY':
            endpoint.addCapability(AlexaPercentageController(endpoint, 'Alexa.PercentageController',[{'name': 'percentage'}]))
        cookies = request['endpoint']['cookie']
        if cookies is not None:
            endpoint.addCookie(cookies)
        endpoint.setHandler(self)
        return endpoint

    def getEndpoints(self):
        endpoints = []

        # Devices
        response = self.api('type=devices&used=true')
        devices= response['result']
        for device in devices:
            endpoint = None

            if (device['PlanID'] == "0" or device['PlanID'] == ""): continue
            if (self.planID >= 0 and (not (self.planID in device['PlanIDs']))): continue

            devType = device['Type']

            friendlyName = device['Name']
            endpointId = device['idx']
            manufacturerName = device['HardwareName']
            description = devType

            matchObj = re.match( r'.*Alexa_Name:\s*([^\n]*)', device['Description'], re.M|re.I|re.DOTALL)
            if matchObj:  friendlyName = matchObj.group(1)
            matchObj = re.match( r'.*Alexa_Description:\s*([^\n]*)', device['Description'], re.M|re.I|re.DOTALL)
            if matchObj:  description = matchObj.group(1)
            extra = None
            matchObj = re.match( r'.*Alexa_extra:\s*([^\n]*)', device['Description'], re.M|re.I|re.DOTALL)
            if matchObj:  extra = matchObj.group(1)

            if self.prefixName is not None:
                friendlyName = self.prefixName + friendlyName

            if (devType.startswith('Lighting') or devType.startswith('Color Switch')):
                switchType = device['SwitchType']
                if switchType == 'On/Off':
                    # Usual switch case
                    endpoint = SwitchLightAlexaEndpoint("SwitchLight-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("SWITCH")
                    hasDimmer = device['HaveDimmer']
                    if (hasDimmer):
                        endpoint.addCapability(AlexaPercentageController(self, 'Alexa.PercentageController',[{'name': 'percentage'}]))
                        endpoint.addCapability(AlexaBrightnessController(self, 'Alexa.BrightnessController',[{'name': 'brightness'}]))
                else:
                    # Usual switch case
                    endpoint = SwitchLightAlexaEndpoint("SwitchLight-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("LIGHT")
                    hasDimmer = device['HaveDimmer']
                    if (hasDimmer):
                        endpoint.addCapability(AlexaPercentageController(self, 'Alexa.PercentageController',[{'name': 'percentage'}]))
                        endpoint.addCapability(AlexaBrightnessController(self, 'Alexa.BrightnessController',[{'name': 'brightness'}]))              
                    subType = device['SubType']
                    if (subType.startswith("RGB")):
                        endpoint.addCapability(AlexaColorController(self, 'Alexa.ColorController'))              
                        endpoint.addCapability(AlexaColorTemperatureController(self, 'Alexa.ColorTemperatureController'))

            elif (devType.startswith('Light/Switch')):
                switchType = device['SwitchType']
                # Special case to implement a "virtual thermostat"
                if switchType == 'Selector' and (extra is not None):
                    # extra must contain { "OFF": 0, CONFORT": idx, "ECONOMIE"; idx...}
                    endpoint = ThermostatAlexaEndpoint("SelectorThermostat-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("THERMOSTAT")
                elif (switchType.startswith('Door')):
                    endpoint = LockAlexaEndpoint("Lock-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("SWITCH")
                elif (switchType.startswith('Contact')):
                    endpoint = ContactAlexaEndpoint("Contact-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("CONTACT_SENSOR")
                else:
                    # Usual switch case
                    endpoint = SwitchLightAlexaEndpoint("SwitchLight-"+endpointId, friendlyName, description, manufacturerName)
                    endpoint.addDisplayCategories("SWITCH")
                    hasDimmer = device['HaveDimmer']
                    if (hasDimmer):
                        endpoint.addCapability(AlexaPercentageController(self, 'Alexa.PercentageController',[{'name': 'percentage'}]))
                        endpoint.addCapability(AlexaBrightnessController(self, 'Alexa.BrightnessController',[{'name': 'brightness'}]))              
                    subType = device['SubType']
                    if (subType.startswith("RGB")):
                        endpoint.addDisplayCategories("LIGHT")
                        endpoint.addCapability(AlexaColorController(self, 'Alexa.ColorController'))              
                        endpoint.addCapability(AlexaColorTemperatureController(self, 'Alexa.ColorTemperatureController')) 						

            elif (devType.startswith('Blind') or devType.startswith('RFY')):
                if   devType.startswith('Blind'): endpoint = BlindAlexaEndpoint("Blind-"+endpointId, friendlyName, description, manufacturerName)
                elif devType.startswith('RFY'):   endpoint = RFYAlexaEndpoint("RFY-"+endpointId, friendlyName, description, manufacturerName)
                endpoint.addDisplayCategories("SWITCH")
                hasDimmer = device['HaveDimmer']
                if (hasDimmer):
                    endpoint.addCapability(AlexaPercentageController(self, 'Alexa.PercentageController',[{'name': 'percentage'}]))

            elif (devType.startswith('Lock')):
                endpoint = LockAlexaEndpoint("Lock-"+endpointId, friendlyName, description, manufacturerName)
                endpoint.addDisplayCategories("SWITCH")

            elif (devType.startswith('Contact')):
                endpoint = ContactAlexaEndpoint("Contact-"+endpointId, friendlyName, description, manufacturerName)
                endpoint.addDisplayCategories("CONTACT_SENSOR")

            elif (devType.startswith('Temp')):
                endpoint = TemperatureSensorAlexaEndpoint("TemperatureSensor-"+endpointId, friendlyName, description, manufacturerName)
                endpoint.addDisplayCategories("TEMPERATURE_SENSOR")

            elif (devType.startswith('Therm')):
                endpoint = ThermostatAlexaEndpoint("Thermostat-"+endpointId, friendlyName, description, manufacturerName)
                endpoint.addDisplayCategories("THERMOSTAT")
                endpoint.addDisplayCategories("TEMPERATURE_SENSOR")

            if (endpoint is not None):
                if extra is not None:
                    endpoint.addCookie({ "extra": extra} )
                #print(endpoint.displayCategories())
                endpoints.append(endpoint)

        # Scenes/Groups
        if self.includeScenesGroups:
            response = self.api('type=scenes')
            scenes= response['result']
            for scene in scenes:
                endpoint = None

                sceneType = scene['Type']
                friendlyName = scene['Name']
                endpointId = scene['idx']
                manufacturerName = SKILL_NAME
                description = sceneType

                matchObj = re.match( r'.*Alexa_Name:\s*([^\n]*)', scene['Description'], re.M|re.I|re.DOTALL)
                if matchObj:  friendlyName = matchObj.group(1)
                matchObj = re.match( r'.*Alexa_Description:\s*([^\n]*)', scene['Description'], re.M|re.I|re.DOTALL)
                if matchObj:  description = matchObj.group(1)
                extra = None
                matchObj = re.match( r'.*Alexa_extra:\s*([^\n]*)', scene['Description'], re.M|re.I|re.DOTALL)
                if matchObj:  extra = matchObj.group(1)

                if self.prefixName is not None:
                    friendlyName = self.prefixName + friendlyName

                if (sceneType.startswith('Scene') or sceneType.startswith('Group')):
                    if sceneType.startswith('Scene')  : 
                        endpoint = SceneAlexaEndpoint('Scene-'+endpointId, friendlyName, description, manufacturerName)
                        endpoint.addDisplayCategories("SCENE_TRIGGER")
                    elif sceneType.startswith('Group'): 
                        endpoint = GroupAlexaEndpoint('Group-'+endpointId, friendlyName, description, manufacturerName)
                        endpoint.addDisplayCategories("SCENE_TRIGGER")

                if (endpoint is not None):
                    if extra is not None:
                        endpoint.addCookie({ "extra": extra} )
                    endpoints.append(endpoint)

        return endpoints

    #
    #  Domoticz API
    #
    def getDevice(self, idx):
        return self.api('type=devices&rid=%s'%idx)['result'][0]

    def setTemp(self, idx, value):
        # Ignore exception ???
        try:
            self.api('type=command&param=udevice&idx=%s&nvalue=0&svalue=%s'%(idx,value))
        except Exception:
            pass

    def setLevel(self, idx, level):
        self.api('type=command&param=switchlight&idx=%s&switchcmd=Set%%20Level&level=%s'%(idx,level))

    def setLevelByName(self, idx, levelName):
        device = self.getDevice(idx)
        levels = device['LevelNames'].upper().split("|")
        ilevel = levels.index(levelName.upper())
        self.setLevel(idx,ilevel*int(device['LevelInt']))

    def setColor(self, idx, rgb, brightness):
        #self.api('type=command&param=setcolbrightnessvalue&idx=%s&hex=%s&brightness=%s&iswhite=false'%(idx,hue,brightness))
        self.api('type=command&param=setcolbrightnessvalue&idx=%s&hex=%0.2X%0.2X%0.2X&brightness=%s&iswhite=false'%(idx,rgb[0],rgb[1],rgb[2],brightness))
        #self.api('type=command&param=setcolbrightnessvalue&idx=%s&color={"m":3,"r":%s,"g":%s,"b":%s}&brightness=%s'%(idx,rgb[0],rgb[1],rgb[2],brightness))

    def setKelvinLevel(self, idx, kelvin):
        self.api('type=command&param=setkelvinlevel&idx=%s&kelvin=%s'%(idx,kelvin))

    def setSwitch(self, idx, value):
        self.api('type=command&param=switchlight&idx=%s&switchcmd=%s'%(idx,value))

    def setSceneSwitch(self, idx, value):
        self.api('type=command&param=switchscene&idx=%s&switchcmd=%s'%(idx,value))

def color_hsb_to_RGB(fH: float, fS: float, fB: float) -> Tuple[int, int, int]:
    """Convert a hsb into its rgb representation."""
    if fS == 0:
        fV = int(fB * 255)
        return fV, fV, fV

    r = g = b = 0
    h = fH / 60
    f = h - float(math.floor(h))
    p = fB * (1 - fS)
    q = fB * (1 - fS * f)
    t = fB * (1 - (fS * (1 - f)))

    if int(h) == 0:
        r = int(fB * 255)
        g = int(t * 255)
        b = int(p * 255)
    elif int(h) == 1:
        r = int(q * 255)
        g = int(fB * 255)
        b = int(p * 255)
    elif int(h) == 2:
        r = int(p * 255)
        g = int(fB * 255)
        b = int(t * 255)
    elif int(h) == 3:
        r = int(p * 255)
        g = int(q * 255)
        b = int(fB * 255)
    elif int(h) == 4:
        r = int(t * 255)
        g = int(p * 255)
        b = int(fB * 255)
    elif int(h) == 5:
        r = int(fB * 255)
        g = int(p * 255)
        b = int(q * 255)

    return (r, g, b)

