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
    """
    Converts a dictionary in XML format into a list of App objects.

    Args:
        dict (dict): A dictionary representing an XML file.

    Returns:
        list: A list of App objects.

    Raises:
        None
    """
    def app_from_xml_entry(xmlEntry):
        return App(host=xmlEntry['ipAddr'], port=xmlEntry['port']['#text'])

    instances_xml = xml_dict['application']['instance']

    if not isinstance(instances_xml, list):      # If there is only one, wrap as list
        instances_xml = [instances_xml]

    return [app_from_xml_entry(instance_xml) for instance_xml in instances_xml]       # Parse xml to App


def remove_own_instance(peers: list[App]):
    """
    Removes the own instance from the list of peers.

    Args:
        peers (list[App]): A list of App objects representing the instances.

    Returns:
        list[App]: A new list of App objects without the own instance.

    Raises:
        None
    """
    def is_own_instance(peer: App):
        return peer.host == OWN_HOST and peer.port == OWN_PORT

    return [peer for peer in peers if not is_own_instance(peer)]


def generate_toml_string(peers: list[App]):
    """
    Generates a TOML string representation of the peers.

    Args:
        peers (list[App]): A list of App objects representing the peers.

    Returns:
        str: A TOML string representation of the peers.

    Raises:
        None

    Examples:
        >>> app_list = [App(host='127.0.0.1', port='8080'), App(host='192.168.1.1', port='8000')]
        >>> generate_toml_string(app_list)
        'peers = ["tcp://127.0.0.1:8080", "tcp://192.168.1.1:8000"]'
    """
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

