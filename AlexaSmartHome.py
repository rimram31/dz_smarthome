import logging
import sys, operator

from uuid import uuid4
from datetime import datetime
from typing import Tuple

import math, colorsys
import traceback 
from typing import Callable, TypeVar

CALLABLE_T = TypeVar('CALLABLE_T', bound=Callable)  # noqa pylint: disable=invalid-name

class Registry(dict):
    """Registry of items."""
    def register(self, name: str) -> Callable[[CALLABLE_T], CALLABLE_T]:
        """Return decorator to register item with a specific name."""
        def decorator(func: CALLABLE_T) -> CALLABLE_T:
            """Register decorated function."""
            self[name] = func
            return func

        return decorator

INTERFACES = Registry()

class AlexaEndpoint(object):
    def __init__(self, endpointId, friendlyName="", description="", manufacturerName=""):
        self._endpointId = endpointId
        self._friendlyName = friendlyName
        self._description = description
        self._manufacturerName = manufacturerName
        self._capabilities = []
        self._displayCategories = []
        self._cookies = {}

    def endpointId(self):
        return self._endpointId

    def friendlyName(self):
        return self._friendlyName

    def description(self):
        return self._description

    def manufacturerName(self):
        return self._manufacturerName

    def displayCategories(self):
        return self._displayCategories

    def capabilities(self):
        return self._capabilities

    def cookies(self):
        return self._cookies

    def getProperty(self, name):
        return None

    def addDisplayCategories(self, category):
        self._displayCategories.append(category)

    def addCapability(self, interface):
        self._capabilities.append(interface)

    def addCookie(self, dict):
        for k, v in dict.items():
            self._cookies[k] = v

class AlexaInterface:

    def __init__(self, endpoint, name = 'Alexa', properties = [], proactivelyReported = True, retrievable = True, modesSupported = None, deactivationSupported = None):
        self._endpoint = endpoint
        self._name = name
        self._properties = properties
        self._proactivelyReported = proactivelyReported
        self._retrievable = retrievable
        self._modesSupported = modesSupported
        self._deactivationSupported = deactivationSupported

    def name(self):
        return self._name

    def version(self):
        return "3"

    def propertiesSupported(self):
        return self._properties

    def propertiesProactivelyReported(self):
        return self._proactivelyReported

    def propertiesRetrievable(self):
        return self._retrievable

    def supportsDeactivation(self):
        return self._deactivationSupported

    def configuration(self):
        return None

    def supportScheduling(self):
        return False

    def modesSupported(self):
        return self._modesSupported

    def setModesSupported(self, modesSupported):
        self._modesSupported = modesSupported

    def serializeDiscovery(self):
        result = {
            'type': 'AlexaInterface',
            'interface': self.name(),
            'version': self.version(),
            'properties': {
                'supported': self.propertiesSupported(),
                'proactivelyReported': self.propertiesProactivelyReported(),
                'retrievable': self.propertiesRetrievable(),
            },
        }
        if self.configuration() is not None:
            result['configuration'] = self.configuration()
        supports_deactivation = self.supportsDeactivation()
        if supports_deactivation is not None:
            result['supportsDeactivation'] = supports_deactivation
        return result

    def serializeProperties(self):
        for prop in self.propertiesSupported():
            prop_name = prop['name']
            prop_value = self._endpoint.getProperty(prop_name)
            if prop_value is not None:
                yield {
                    'name': prop_name,
                    'namespace': self.name(),
                    'value': prop_value,
                }

@INTERFACES.register('Alexa.PowerController')
class AlexaPowerController(AlexaInterface):
    def name(self):
        return 'Alexa.PowerController'

    def propertiesSupported(self):
        return [{'name': 'powerState'}]

@INTERFACES.register('Alexa.LockController')
class AlexaLockController(AlexaInterface):
    def name(self):
        return 'Alexa.LockController'

    def propertiesSupported(self):
        return [{'name': 'lockState'}]

@INTERFACES.register('Alexa.SceneController')
class AlexaSceneController(AlexaInterface):
    def name(self):
        return 'Alexa.SceneController'

    def serializeDiscovery(self):
        result = {
            'type': 'AlexaInterface',
            'interface': self.name(),
            'version': self.version(),
            'proactivelyReported': self.propertiesProactivelyReported(),
            'supportsDeactivation': self.supportsDeactivation(),
        }
        return result

@INTERFACES.register('Alexa.BrightnessController')
class AlexaBrightnessController(AlexaInterface):
    def name(self):
        return 'Alexa.BrightnessController'

    def propertiesSupported(self):
        return [{'name': 'brightness'}]

@INTERFACES.register('Alexa.ColorController')
class AlexaColorController(AlexaInterface):
    def name(self):
        return 'Alexa.ColorController'

@INTERFACES.register('Alexa.ColorTemperatureController')
class AlexaColorTemperatureController(AlexaInterface):
    def name(self):
        return 'Alexa.ColorTemperatureController'

@INTERFACES.register('Alexa.PercentageController')
class AlexaPercentageController(AlexaInterface):
    def name(self):
        return 'Alexa.PercentageController'

@INTERFACES.register('Alexa.Speaker')
class AlexaSpeaker(AlexaInterface):
    def name(self):
        return 'Alexa.Speaker'

@INTERFACES.register('Alexa.StepSpeaker')
class AlexaStepSpeaker(AlexaInterface):
    def name(self):
        return 'Alexa.StepSpeaker'

@INTERFACES.register('Alexa.PlaybackController')
class AlexaPlaybackController(AlexaInterface):
    def name(self):
        return 'Alexa.PlaybackController'

@INTERFACES.register('Alexa.InputController')
class AlexaInputController(AlexaInterface):
    def name(self):
        return 'Alexa.InputController'

@INTERFACES.register('Alexa.TemperatureSensor')
class AlexaTemperatureSensor(AlexaInterface):
    def name(self):
        return 'Alexa.TemperatureSensor'

    def propertiesSupported(self):
        return [{'name': 'temperature'}]

@INTERFACES.register('Alexa.ThermostatController')
class AlexaThermostatController(AlexaInterface):
    def name(self):
        return 'Alexa.ThermostatController'

    def propertiesSupported(self):
        return [{'name': 'targetSetpoint'}, {'name': 'thermostatMode'}]

    def configuration(self):
        configuration = None
        if self.modesSupported() is not None:
            configuration = {
              'supportsScheduling': self.supportScheduling(),
              'supportedModes': self.modesSupported()
            }
        return configuration

API_DIRECTIVE = 'directive'
API_ENDPOINT = 'endpoint'
API_EVENT = 'event'
API_CONTEXT = 'context'
API_HEADER = 'header'
API_PAYLOAD = 'payload'

_LOGGER = logging.getLogger(__name__)

def api_message(request,
                name='Response',
                namespace='Alexa',
                payload=None,
                context=None):
    """Create a API formatted response message.
    """
    payload = payload or {}

    response = {
        API_EVENT: {
            API_HEADER: {
                'namespace': namespace,
                'name': name,
                'messageId': str(uuid4()),
                'payloadVersion': '3',
            },
            API_PAYLOAD: payload,
        }
    }

    # If a correlation token exists, add it to header / Need by Async requests
    token = request[API_HEADER].get('correlationToken')
    if token:
        response[API_EVENT][API_HEADER]['correlationToken'] = token

    # Extend event with endpoint object / Need by Async requests
    if API_ENDPOINT in request:
        response[API_EVENT][API_ENDPOINT] = request[API_ENDPOINT].copy()

    if context is not None:
        response[API_CONTEXT] = context

    return response

def api_error(request,
              namespace='Alexa',
              error_type='INTERNAL_ERROR',
              error_message="",
              payload=None):
    """Create a API formatted error response.

    Async friendly.
    """
    payload = payload or {}
    payload['type'] = error_type
    payload['message'] = error_message

    _LOGGER.info("Request %s/%s error %s: %s",
                 request[API_HEADER]['namespace'],
                 request[API_HEADER]['name'],
                 error_type, error_message)

    return api_message(
        request, name='ErrorResponse', namespace=namespace, payload=payload)

def handle_message(handler, message):
    """Handle incoming API messages."""
    #assert message[API_DIRECTIVE][API_HEADER]['payloadVersion'] == '3'

    # Read head data
    message = message[API_DIRECTIVE]
    namespace = message[API_HEADER]['namespace']
    name = message[API_HEADER]['name']

    #entity_id = request[API_ENDPOINT]['endpointId'].replace('#', '.')

    return invoke(namespace, name, handler, message)

class AlexaSmartHomeCall(object):
    def __init__(self, namespace, name, handler):
        self.namespace = namespace
        self.name = name
        self.handler = handler

    def invoke(self, name, request):
        try:
            return operator.attrgetter(name)(self)(request)
        except Exception:
            traceback.print_exc(file=sys.stdout)
            return api_error(request)

class Alexa(object):

    class Discovery(AlexaSmartHomeCall):

        def Discover(self, request):
            discovery_endpoints = []
            endpoints = self.handler.getEndpoints()
            for endpoint in endpoints:
                discovery_endpoint = {
                    'endpointId': endpoint.endpointId(),
                    'friendlyName': endpoint.friendlyName(),
                    'description': endpoint.description(),
                    'manufacturerName': endpoint.manufacturerName(),
                    'displayCategories': endpoint.displayCategories(),
                    'additionalApplianceDetails': {},
                }
                discovery_endpoint['capabilities'] = [
                    i.serializeDiscovery() for i in endpoint.capabilities()]
                if not discovery_endpoint['capabilities']:
                    _LOGGER.debug("Not exposing %s because it has no capabilities", endpoint.endpointId())
                    continue
                discovery_endpoints.append(discovery_endpoint)

            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])

            return api_message(
                request, name='Discover.Response', namespace='Alexa.Discovery',
                payload={'endpoints': discovery_endpoints})

    class PowerController(AlexaSmartHomeCall):

        def TurnOn(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            endpoint = self.handler.getEndpoint(request)
            endpoint.turnOn()
            return api_message(request)

        def TurnOff(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            endpoint = self.handler.getEndpoint(request)
            endpoint.turnOff()
            return api_message(request)

    class BrightnessController(AlexaSmartHomeCall):

        def setbrightness(self, request, endpoint, brightness):
            endpoint.setBrightness(brightness)
            properties = [{
                'name': 'brightness',
                'namespace': 'Alexa.BrightnessController',
                "value": brightness
            }]
            return api_message(request, context={'properties': properties})

        def SetBrightness(self, request):
            brightness = int(request[API_PAYLOAD]['brightness'])
            _LOGGER.debug("Request %s/%s brightness %d", 
                   request[API_HEADER]['namespace'], request[API_HEADER]['name'],
                   brightness)
            endpoint = self.handler.getEndpoint(request)
            return self.setbrightness(request, endpoint, brightness)

        def AdjustBrightness(self, request):
            brightness_delta = int(request[API_PAYLOAD]['brightnessDelta'])
            _LOGGER.debug("Request %s/%s brightness_delta %d", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'],
                        brightness_delta)
            endpoint = self.handler.getEndpoint(request)
            brightness = endpoint.getProperty('brightness') + brightness_delta
            return self.setbrightness(request, endpoint, brightness)

    class ColorController(AlexaSmartHomeCall):

        def SetColor(self, request):
            h = float(request[API_PAYLOAD]['color']['hue'])
            s = float(request[API_PAYLOAD]['color']['saturation'])
            b = float(request[API_PAYLOAD]['color']['brightness'])
            _LOGGER.debug("Request %s/%s", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            endpoint = self.handler.getEndpoint(request)
            endpoint.setColor(h,s,b)
            return api_message(request)

    class ColorTemperatureController(AlexaSmartHomeCall):

        def SetColorTemperature(self, request):
            kelvin = int(request[API_PAYLOAD]['colorTemperatureInKelvin'])
            _LOGGER.debug("Request %s/%s kelvin %d", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'],
                        kelvin)
            endpoint = self.handler.getEndpoint(request)
            endpoint.setColorTemperature(kelvin)
            return api_message(request)

        def DecreaseColorTemperature(self, request):
            ##current = int(entity.attributes.get(light.ATTR_COLOR_TEMP))
            ##max_mireds = int(entity.attributes.get(light.ATTR_MAX_MIREDS))
            ##value = min(max_mireds, current + 50)
            _LOGGER.debug("Request %s/%s", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def IncreaseColorTemperature(self, request):
            ##current = int(entity.attributes.get(light.ATTR_COLOR_TEMP))
            ##max_mireds = int(entity.attributes.get(light.ATTR_MAX_MIREDS))
            ##value = min(max_mireds, current - 50)
            _LOGGER.debug("Request %s/%s", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

    class SceneController(AlexaSmartHomeCall):

        def Activate(self, request):
            payload = {
                'cause': {'type': 'VOICE_INTERACTION'},
                'timestamp': '%sZ' % (datetime.utcnow().isoformat(),)
            }
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            endpoint = self.handler.getEndpoint(request)
            endpoint.activate()
            return api_message(request,
                name='ActivationStarted', namespace='Alexa.SceneController',
                payload=payload)

        def Deactivate(self, request):
            payload = {
                'cause': {'type': 'VOICE_INTERACTION'},
                'timestamp': '%sZ' % (datetime.utcnow().isoformat(),)
            }
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            endpoint = self.handler.getEndpoint(request)
            endpoint.deactivate()
            return api_message(request,
                name='DeactivationStarted', namespace='Alexa.SceneController',
                payload=payload)

    class PercentageController(AlexaSmartHomeCall):

        def SetPercentage(self, request):
            percentage = int(request[API_PAYLOAD]['percentage'])
            ##if entity.domain == fan.DOMAIN:
            ##    service = fan.SERVICE_SET_SPEED
            ##    speed = "off"
            ##    if percentage <= 33:
            ##        speed = "low"
            ## ...
            _LOGGER.debug("Request %s/%s percentage %d", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'],
                        percentage)
            endpoint = self.handler.getEndpoint(request)
            if   (percentage < 0):   percentage = 0
            elif (percentage > 100): percentage = 100
            endpoint.setPercentage(percentage)
            return api_message(request)

        def AdjustPercentage(self, request):
            percentage_delta = int(request[API_PAYLOAD]['percentageDelta'])
            _LOGGER.debug("Request %s/%s percentage_delta %d", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'],
                        percentage_delta)
            endpoint = self.handler.getEndpoint(request)
            percentage = endpoint.getProperty(percentage)
            target_percentage = int(percentage) + percentage_delta
            if   (target_percentage < 0):   target_percentage = 0
            elif (target_percentage > 100): target_percentage = 100
            endpoint.setPercentage(percentage)
            return api_message(request)

    class LockController(AlexaSmartHomeCall):

        def Lock(self, request):
            # Alexa expects a lockState in the response
            properties = [{
                'name': 'lockState',
                'namespace': 'Alexa.LockController',
                'value': 'LOCKED'
            }]
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request, context={'properties': properties})

        # Not supported by Alexa ...
        def Unlock(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

    class InputController(AlexaSmartHomeCall):

        def SelectInput(self, request):
            media_input = request[API_PAYLOAD]['input']
            _LOGGER.debug("Request %s/%s media_input %s", request[API_HEADER]['namespace'], request[API_HEADER]['name',media_input])
            return api_message(request)

    class Speaker(AlexaSmartHomeCall):

        def SetVolume(self, request):
            volume = round(float(request[API_PAYLOAD]['volume'] / 100), 2)
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def AdjustVolume(self, request):
            volume_delta = int(request[API_PAYLOAD]['volume'])
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

    class StepSpeaker(AlexaSmartHomeCall):

        def AdjustVolume(self, request):
            volume_step = request[API_PAYLOAD]['volumeSteps']
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def SetMute(self, request):
            mute = bool(request[API_PAYLOAD]['mute'])
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

    class PlaybackController(AlexaSmartHomeCall):

        def Play(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def Pause(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def Stop(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def Next(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

        def Previous(self, request):
            _LOGGER.debug("Request %s/%s", request[API_HEADER]['namespace'], request[API_HEADER]['name'])
            return api_message(request)

    class ThermostatController(AlexaSmartHomeCall):

        def SetTargetTemperature(self, request):
            temp = 20.0
            tempScale = "CELSIUS"
            #unit = entity.attributes[CONF_UNIT_OF_MEASUREMENT]
            payload = request[API_PAYLOAD]
            if 'targetSetpoint' in payload:
                temp = temperature_from_object(payload['targetSetpoint'])
                _LOGGER.debug("Request %s/%s targetSetpoint %.2f",
                            request[API_HEADER]['namespace'], request[API_HEADER]['name'], temp)
                endpoint = self.handler.getEndpoint(request)
                endpoint.setTargetSetPoint(temp)

            properties = [{
                'name': 'targetSetpoint',
                'namespace': 'Alexa.ThermostatController',
                "value": {
                    "value": temp,
                    "scale": tempScale
                }
            }]
            return api_message(request, context={'properties': properties})

        def AdjustTargetTemperature(self, request):
            temp = 20.0
            tempScale = "CELSIUS"
            ##unit = entity.attributes[CONF_UNIT_OF_MEASUREMENT]
            temp_delta = temperature_from_object(request[API_PAYLOAD]['targetSetpointDelta'])

            _LOGGER.debug("Request %s/%s targetSetpoint temp_delta %.2f", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'], temp_delta)

            endpoint = self.handler.getEndpoint(request)
            temp = endpoint.getProperty('targetSetpoint')['value']
            target_temp = temp + temp_delta
            endpoint.setTargetSetPoint(target_temp)

            properties = [{
                'name': 'targetSetpoint',
                'namespace': 'Alexa.ThermostatController',
                "value": {
                    "value": target_temp,
                    "scale": tempScale
                }
            }]
            return api_message(request, context={'properties': properties})

        def SetThermostatMode(self, request):
            mode = request[API_PAYLOAD]['thermostatMode']
            mode = mode if isinstance(mode, str) else mode['value']

            _LOGGER.debug("Request %s/%s targetSetpoint mode %s", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'], str(mode))

            endpoint = self.handler.getEndpoint(request)
            endpoint.setThermostatMode(mode)
            properties = [{
                'name': 'targetSetthermostatModepoint',
                'namespace': 'Alexa.ThermostatController',
                "value": mode
            }]
            return api_message(request, context={'properties': properties})

    class ReportState(AlexaSmartHomeCall):

        def ReportState(self, request):
            properties = []
            endpoint = self.handler.getEndpoint(request)
            for interface in endpoint.capabilities():
                properties.extend(interface.serializeProperties())

            _LOGGER.debug("Request %s/%s properties %s", 
                        request[API_HEADER]['namespace'], request[API_HEADER]['name'], str(properties))
            return api_message(request,
                name='StateReport',
                context={'properties': properties})

def invoke(namespace, name, handler, request):
    try:
        # Special case report
        if namespace == "Alexa" and name == "ReportState":
            namespace = "Alexa.ReportState"
        class allowed(object):
            Alexa = Alexa
        make_class = operator.attrgetter(namespace)
        obj = make_class(allowed)(namespace, name, handler)
        return obj.invoke(name, request)

    except Exception:
        _LOGGER.error("Can't process %s/%s", namespace, name)
        return api_error(request, error_type='INTERNAL_ERROR')

def fahrenheit_to_celsius(fahrenheit: float, interval: bool = False) -> float:
    if interval:
        return fahrenheit / 1.8
    return (fahrenheit - 32.0) / 1.8

def celsius_to_fahrenheit(celsius: float, interval: bool = False) -> float:
    if interval:
        return celsius * 1.8
    return celsius * 1.8 + 32.0

def temperature_from_object(temp_obj):
    """Get temperature from Temperature object in requested unit."""
    temp = float(temp_obj['value'])
    if temp_obj['scale'] == 'FAHRENHEIT':
        temp = fahrenheit_to_celsius(temp)
    elif temp_obj['scale'] == 'KELVIN':
        if not interval:
            temp -= 273.15
    return temp
