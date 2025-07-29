import xml.etree.ElementTree as ET
from typing import Dict

def xml_to_dict(xml_string: str) -> Dict:  
    return _xml_to_dict(ET.fromstring(xml_string))

def _xml_to_dict(eml: ET.Element) -> Dict:
    """
    Convert an EML XML string to a dictionary.
    This function parses the XML and converts it to a nested dictionary structure.
    :param eml: The EML XML string to convert.
    :return: A dictionary representation of the EML XML.
    """

    element = eml
    node = {}
    if element.attrib:
        node.update(element.attrib)
    if element.text and element.text.strip():
        node['text'] = element.text.strip()
    # Add children
    for child in element:
        child_dict = _xml_to_dict(child)
        tag = child.tag.split('}', 1)[-1]  # Remove namespace if present
        if tag in node:
            # If tag already exists, convert to list
            if not isinstance(node[tag], list):
                node[tag] = [node[tag]]
            node[tag].append(child_dict)
        else:
            node[tag] = child_dict
    return node
