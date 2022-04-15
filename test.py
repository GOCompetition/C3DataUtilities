import json
from zipfile import ZipFile

#data_file = '/pic/dtn/go/Jesse/c3/updated/PSY_RTS_GMLC_data_fixed_load_commit_v3_output.json'
#data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_fixed_load_20220414.json'
data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_flex_load_20220414.json'
#sol_file = '/pic/dtn/go/Carleton/PSY_RTS_GMLC_data_flex_load_20220414-solution.zip'
sol_file = '/pic/dtn/go/Jesse/c3/updated/solution_BASECASE.json'

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

data = read_json(data_file)
print(json.dumps(data, indent=4, sort_keys=True))

sol = read_json(sol_file)
print(json.dumps(sol, indent=4, sort_keys=True))
