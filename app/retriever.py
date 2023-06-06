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


def parse_xml_to_obj(xml_dict):
    def app_from_xml_entry(xmlEntry):
        return App(host=xmlEntry['ipAddr'], port=xmlEntry['port']['#text'])

    instances_xml = xml_dict['application']['instance']

    if not isinstance(instances_xml, list):      # If there is only one, wrap as list
        instances_xml = [instances_xml]

    return [app_from_xml_entry(instance_xml) for instance_xml in instances_xml]       # Parse xml to App


def remove_own_instance(peers: list[App]):
    def is_own_instance(peer: App):
        return peer.host == OWN_HOST and peer.port == OWN_PORT

    return [peer for peer in peers if not is_own_instance(peer)]


def generate_toml_string(peers: list[App]):
    def parse_peer_to_str(peer: App):
        return f'\"tcp://{peer.host}:{peer.port}\"'

    innerStr = ', '.join([parse_peer_to_str(peer) for peer in peers])

    return f'peers = [{innerStr}]'


def write_file(content: str, filename: str):
    with open(filename, 'w+') as file:
        file.write(content + '\n')


def parse_remote_url(host: str, app_id: str):
    return f'{host}/eureka/v2/apps/{app_id}'

# ----------------------------------------------------------------------------------------------------- #


res = requests.get(parse_remote_url(REMOTE, APP_ID))
if res.status_code == 404:
    exit(-1)

dict_data = xmltodict.parse(res.content)
peers = parse_xml_to_obj(dict_data)
peers = remove_own_instance(peers)
peerStr = generate_toml_string(peers)

write_file(content=peerStr, filename=OUTPUT_FILE)

