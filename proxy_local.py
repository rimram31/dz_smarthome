#!/usr/bin/python3

#
# This source is provided for tests purpose
# You can run a local web server answering tests Alexa queries (Postman for example)
# Requests are forwarded to AlexaSmartHome handler, the same used by the final lambda
#
# Require python 3 and flask to be installed
# sudo apt-get install python3 pip3
# pip3 install flask
# ... and perhaps some missings ...

from flask import Flask, request
from flask_restful import Resource, Api
import json

from pathlib import Path

import AlexaSmartHome, DomoticzHandler

app = Flask(__name__)
api = Api(app)

dz = DomoticzHandler.Domoticz("http://127.0.0.1:8080")
#dz.includeScenesGroups = True
#dz.planID = 12

class SmartHome(Resource):

    def get(self):
        return {}

    def post(self):
        message = json.loads(request.data.decode('utf-8'))
        response = AlexaSmartHome.handle_message(dz, message)
        return response

api.add_resource(SmartHome, '/smarthome')

if __name__ == '__main__':
     app.run(host='0.0.0.0', port='5002')
