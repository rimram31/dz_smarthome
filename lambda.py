import json
import logging
from pathlib import Path

import AlexaSmartHome, DomoticzHandler, OktaAPI

logger = logging.getLogger()

class Configuration(object):
    def __init__(self, filename=None, optsDict=None):
        self._json = {}
        if filename is not None:
            with open(filename) as f:
                self._json = json.load(f)

        if optsDict is not None:
            self._json = optsDict

        opts = {}
        opts['url'] = self.get(['url'], default='http://localhost:8080/')
        opts['username'] = self.get(['username'], default='')
        opts['password'] = self.get(['password'], default='')
        opts['planID'] = self.get(['planID'], default=None)
        opts['debug'] = self.get(['debug'], default=False)
        self.opts = opts

    def __getattr__(self, name):
        return self.opts[name]

    def get(self, keys, default):
        for key in keys:
            if key in self._json:
                return self._json[key]
        return default

    def dump(self):
        return json.dumps(self.opts, indent=2, separators=(',', ': '))

def event_handler(request, context):

    logger.debug("Lambda invocation %s", repr(request))

    config = Configuration('configdz.json')
    if config.debug:
        logger.setLevel(logging.DEBUG)

    dzRemote = None
    oktaConfig = Path("config-otka.json")
    if oktaConfig.exists():
        with open("config-otka.json") as f:
            oktaJson = json.load(f)
        okta = OktaAPI.Okta(oktaJson['endpoint'], oktaJson['api_key'])
        if 'scope' in request['directive']['payload']:
            token = request['directive']['payload']['scope']['token']
        elif 'scope' in request['directive']['endpoint']:
            token = request['directive']['endpoint']['scope']['token']
        try: 
            profile = okta.userProfile(token)
            dzRemote = DomoticzHandler.Domoticz(profile['domoticz_url'], profile['domoticz_username'], profile['domoticz_password'])
        except: pass
    else:
        dzRemote = DomoticzHandler.Domoticz(config.url, config.username, config.password)

    if config.planID is not None:
        dzRemote.setPlanID(config.planID)

    response =  AlexaSmartHome.handle_message(dzRemote, request)

    logger.debug("Skill response %s", response)

    return response
