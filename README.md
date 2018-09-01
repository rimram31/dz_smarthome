# Alexa Domoticz Smart Home skill

## Presentation

Very first version of this skill.

This skill is inspired from madgeni skill [madgeni alexa domo skill](https://github.com/madgeni/alexa_domo) and also keep some code skeleton from [Home Assistant Alexa code](https://github.com/home-assistant/home-assistant)

Only devices in plan will be declared to Alexa, you can set a frendly Alexa name using Alexa_name = ... in the device description field.

## Installing the skill

You must have or create an Amazon Developer Account and an Amazon Web Service account to host the Alexa lambda

Create a Smart Home skill in Amazon Devleoper Account with an associated Lambda in your Amazon Web Service account

```sh
git clone git@github.com:rimram31/dz_smarthome.git
cd dz_smartome
```

Fill your ```configdz.json``` file
```sh
cp configdz-template.json configdz.json
nano configdz.json
```

Build the lambda zip file
```sh
./build_lambda
```
This will create the zip code file to be uploaded for the lambda (require a Python 3.6 engine, handler name is ```lambda.event_handler```)

To help to make some tests, it would be good to put the device in a 'well reconized' (voice) group.
