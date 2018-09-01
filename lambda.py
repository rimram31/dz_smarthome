import json
import logging

import AlexaSmartHome, DomoticzHandler

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
    config = Configuration('configdz.json')
    if config.debug:
        logger.setLevel(logging.DEBUG)

    logger.debug("Lambda invocation %s", repr(request))
    dzRemote = DomoticzHandler.Domoticz(config.url, config.username, config.password)
    response =  AlexaSmartHome.handle_message(dzRemote, request)
    logger.debug("Skill response %s", response)

    return response
