from reading import Reader
from validation import Validator
import json

#data_file = '/pic/dtn/go/Jesse/c3/updated/PSY_RTS_GMLC_data_fixed_load_commit_v3_output.json'
#data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_fixed_load_20220414.json'
#data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_flex_load_20220414.json'
#data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_fixed_load_20220422.json'
#data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_flex_load_20220422.json'
data_file = '/pic/dtn/go/Nongchao/c3/updated/PSY_RTS_GMLC_data_flex_load_20220501.json'
#sol_file = '/pic/dtn/go/Carleton/PSY_RTS_GMLC_data_flex_load_20220414-solution.zip'
sol_file = '/pic/dtn/go/Jesse/c3/updated/solution_BASECASE.json'

reader = Reader()

data = reader.read_json_data(data_file)
print(json.dumps(data, indent=4, sort_keys=True))

sol = reader.read_json_sol(sol_file)
print(json.dumps(sol, indent=4, sort_keys=True))

validator = Validator()

validator.validate_json_data(data)

validator.validate_json_sol(sol)

# print('data keys: {}'.format(data.keys()))
# print('network keys: {}'.format(data['network'].keys()))
print('time_series_input keys: {}'.format(data['time_series_input'].keys()))
# buses = data['network']['bus']
# ac_lines = data['network']

network = data['network']
time_series = data['time_series_input']

general = network['general']
vio_cost = network['violation_cost']
p_rsv = network['active_zonal_reserve']

print('general: {}'.format(general))
print('vio_cost: {}'.format(vio_cost))
print('p_rsv: {}'.format(p_rsv))

bus = network['bus']
acl = network['ac_line']
dcl = network['dc_line']
xfr = network['two_winding_transformer']
sh = network['shunt']
sd = network['simple_dispatchable_device']

num_bus = len(bus)
num_acl = len(acl)
num_dcl = len(dcl)
num_xfr = len(xfr)
num_sh = len(sh)
num_sd = len(sd)

print('num bus: {}'.format(num_bus))
print('num acl: {}'.format(num_acl))
print('num dcl: {}'.format(num_dcl))
print('num xfr: {}'.format(num_xfr))
print('num sh: {}'.format(num_sh))
print('num sd: {}'.format(num_sd))

# for k in data.keys():
#     print('k: {}, k.keys(): {}'.format(k, data[k].keys()))
#print(data['network'])

# print('network keys: {}'.format(data['network'].keys()))
# print('time_series_input keys: {}'.format(data['network'].keys()))
# data['network']
