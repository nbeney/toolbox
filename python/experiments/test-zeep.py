from __future__ import print_function

import traceback

import zeep

# logging.config.dictConfig({
#     'version': 1,
#     'formatters': {
#         'verbose': {
#             'format': '%(name)s: %(message)s'
#         }
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logging.StreamHandler',
#             'formatter': 'verbose',
#         },
#     },
#     'loggers': {
#         'zeep.transports': {
#             'level': 'DEBUG',
#             'propagate': True,
#             'handlers': ['console'],
#         },
#     }
# })

try:
    # client = zeep.Client('http://www.webservicex.net/ConvertSpeed.asmx?WSDL')
    # client = zeep.Client('http://www.webservicex.net/TranslateService.asmx?WSDL')
    # client = zeep.Client('http://www.webservicex.net/country.asmx?WSDL')
    client = zeep.Client('http://www.webservicex.net/geoipservice.asmx?WSDL')
    client.wsdl.dump()
    # print(client.service.GetCurrencyCode())
    # print(client.service.GetCountryByCurrencyCode('JPY'))
    resp = client.service.GetGeoIP('155.168.23.18')
    print(type(resp))
    print(resp)
except:
    traceback.print_exc()

print('===============================================================================================')

try:
    client = zeep.Client('http://www.webservicex.net/ConvertSpeed.asmx?WSDL')
    service1 = client.bind('ConvertSpeeds', 'ConvertSpeedsSoap')
    service2 = client.bind('ConvertSpeeds', 'ConvertSpeedsSoap12')
    print(service1.ConvertSpeed(100, 'kilometersPerhour', 'milesPerhour'))
    print(service2.ConvertSpeed(100, 'kilometersPerhour', 'milesPerhour'))
except:
    traceback.print_exc()

print('===============================================================================================')

try:
    client = zeep.Client('http://www.soapclient.com/xml/soapresponder.wsdl')
    resp = client.service.Method1('Zeep', 'is cool')
    print(resp)
except:
    traceback.print_exc()

print('===============================================================================================')

try:
    client = zeep.Client('http://www.soapclient.com/xml/soapresponder.wsdl')
    with client.options(raw_response=True):
        resp = client.service.Method1('Zeep', 'is cool')
        print(resp.content)
except:
    traceback.print_exc()

print('===============================================================================================')

try:
    client = zeep.Client('http://www.soapclient.com/xml/soapresponder.wsdl')
    with client.options(raw_response=True):
        resp = client.service.Method1('Zeep', 'is cool')
        print(resp.content)
except:
    traceback.print_exc()

print('===============================================================================================')

try:
    transport = zeep.Transport(timeout=10)
    client = zeep.Client('http://www.soapclient.com/xml/soapresponder.wsdl', transport=transport)
    print(client.service.Method1('Zeep', 'is cool'))
except:
    traceback.print_exc()
