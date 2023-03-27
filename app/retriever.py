from dataclasses import dataclass
import os

import xmltodict
import requests

REMOTE = os.environ.get('REMOTE', "http://192.168.1.169:8761")
APP_ID = os.environ.get('APP_NAME', "SAWTOOTH-NODE")
OUTPUT_FILE = os.environ.get('OUTPUT_FILE', "validator.toml")
OWN_HOST = os.environ.get('OWN_HOST', "localhost")
OWN_PORT = os.environ.get('OWN_PORT', "8800")

@dataclass
class App(object):
    host: str
    port: str

def parse_xml_to_obj(dict):
    instances = []
    
    instancesXml = dict['application']['instance']
    
    if not isinstance(instancesXml, list):
        instances.append(App(host=instancesXml['ipAddr'], port=instancesXml['port']['#text']))
    
    else:
        for instanceXml in instancesXml:
            instances.append(App(host=instanceXml['ipAddr'], port=instanceXml['port']['#text']))
        
    return instances

def remove_own_instance(peers: list[App]):
    def is_own_instance(peer: App):
        return peer.host == '10.43.1.182' and peer.port == OWN_PORT
    
    return [peer for peer in peers if not is_own_instance(peer)]


def generate_toml_string(peers: list[App]):
    str = 'peers = [{}]'
    innerStr = []
    
    for peer in peers:
        innerStr.append('\"tcp://{}:{}\"'.format(peer.host, peer.port))
        
    return str.format(', '.join(innerStr))     # remove last comma

def write_file(content: str, filename: str):
    with open(filename, 'w+') as file:
        file.write(content + '\n')
    
def parse_remote_url(host: str, app_id: str):
    return "{}/eureka/v2/apps/{}".format(host, app_id)


# ----------------------------------------------------------------------------------------------------- #

res = requests.get(parse_remote_url(REMOTE, APP_ID))
if res.status_code == 404:
    exit(-1)

dict_data = xmltodict.parse(res.content)
peers = parse_xml_to_obj(dict_data)
peers = remove_own_instance(peers)
peerStr = generate_toml_string(peers)

write_file(content=peerStr, filename=OUTPUT_FILE)

