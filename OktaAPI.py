import os, json, urllib, ssl, base64
from urllib.request import urlopen, Request

import logging

_LOGGER = logging.getLogger(__name__)

class Okta(object):

    def __init__(self,url,api_key):

        self.url = os.path.join(url, '')
        if url.startswith("https"):
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            httpsHandler = urllib.request.HTTPSHandler(context = context)
            opener = urllib.request.build_opener(httpsHandler)
            urllib.request.install_opener(opener)

        self.authorization = 'SSWS %s'%api_key

    def oidc(self, query, token):
        url = self.url + query
        _LOGGER.debug("Okta oidc call %s", url)
        headers = { 'Content-Type': 'application/json' }
        headers['Authorization'] = 'Bearer %s' % token
        payload = urlopen(Request(url, None, headers)).read()
        return json.loads(payload.decode('utf-8'))

    def api(self, query):
        url = self.url + query
        _LOGGER.debug("Okta API call %s", url)
        headers = { 'Content-Type': 'application/json' }
        if self.authorization is not None:
            headers['Authorization'] = self.authorization
        payload = urlopen(Request(url, None, headers)).read()
        return json.loads(payload.decode('utf-8'))

    # Utility user profile
    def userProfile(self, token):
        profile = None
        try:
            userinfo = self.oidc('oauth2/default/v1/userinfo', token)
            user_data = self.api("api/v1/users/%s"%userinfo['sub'])
            profile = user_data['profile']
        except: pass
        return profile
