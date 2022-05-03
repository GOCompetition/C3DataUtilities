import json
from zipfile import ZipFile

def read_json_data(file_name):

    return read_json(file_name)

def read_json_sol(file_name):

    return read_json(file_name)

def read_json(file_name):

    with open(file_name, 'r') as f:
        data = json.load(f)
        return data

def read_file(file_name):

    if file_name.endswith('.json'):
        data = read_json(file_name)
    if file_name.endswith('.zip'):
        with ZipFile(file_name, 'r') as z:
            z.printdir()
            for info in z.infolist():
                print(info.filename)
            return None
