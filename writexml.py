import argparse
import xml.etree.ElementTree as ET

def indent(elem, level=0):
    """Функция структурирования данных в XML файле"""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def create_xml(email_access_id, find_id_HF, find_name, find_role, find_role_id, chat_id):
    """Функция записи данных в XML файл"""
    root = ET.Element('data')

    access = ET.Element('access', email=str(email_access_id))
    root.append(access)

    header_footer = ET.Element('header_footer', id=str(find_id_HF))
    root.append(header_footer)

    name = ET.Element('name')
    name.text = str(find_name)
    header_footer.append(name)

    role = ET.Element('role', id=str(find_role_id))
    role.text = str(find_role)
    header_footer.append(role)

    chat = ET.Element('chat_id')
    chat.text = str(chat_id)
    root.append(chat)

    indent(root)
    xml_str = ET.tostring(root, encoding="utf-8", method="xml")
    print(xml_str.decode(encoding="utf-8"))

    etree = ET.ElementTree(root)
    myfile = open("data.xml" , "wb")
    etree.write(myfile, encoding='utf-8', xml_declaration=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Create XML file with arguments')
    parser.add_argument('--email_access_id', help='Email access ID', type=int)
    parser.add_argument('--find_id_HF', help='ID of header and footer', type=int)
    parser.add_argument('--find_name', help='Name of header and footer')
    parser.add_argument('--find_role', help='Name of role')
    parser.add_argument('--find_role_id', help='ID of role', type=int)
    parser.add_argument('--chat_id', help='ID of chat', type=int)
    args = parser.parse_args()

    create_xml(args.email_access_id, args.find_id_HF, args.find_name, args.find_role, args.find_role_id, args.chat_id)
