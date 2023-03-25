from dataclasses import dataclass
import os

import xmltodict
import requests

REMOTE = os.environ.get('REMOTE', "http://192.168.1.169:8761")
APP_ID = os.environ.get('APP_NAME', "SAWTOOTH-NODE")
OUTPUT_FILE = os.environ.get('OUTPUT_FILE', "validator.toml")

@dataclass
class App(object):
    host: str
    port: str

def parse_xml_to_obj(dict):
    instances = []
    
    instancesXml = dict['application']['instance']
    for instanceXml in instancesXml:
        instances.append(App(host=instanceXml['ipAddr'], port=instanceXml['port']['#text']))
        
    return instances

def generate_toml_string(peers: list[App]):
    str = 'peers = [{}]'
    innerStr = []
    
    for peer in peers:
        innerStr.append('\"tcp://{}:{}\"'.format(peer.host, peer.port))
        
    return str.format(', '.join(innerStr))     # remove last comma

def write_file(content: str, filename: str):
    with open(filename, 'w+') as file:
        file.write(content)
    
def parse_remote_url(host: str, app_id: str):
    return "{}/eureka/v2/apps/{}".format(host, app_id)


# ----------------------------------------------------------------------------------------------------- #

res = requests.get(parse_remote_url(REMOTE, APP_ID))
if res.status_code == 404:
    exit(-1)

dict_data = xmltodict.parse(res.content)
peers = parse_xml_to_obj(dict_data)
peerStr = generate_toml_string(peers)

write_file(content=peerStr, filename=OUTPUT_FILE)

