import sys, traceback
from datamodel.input.data import InputDataFile
from datautilities import utils, validation

# run this either as:
#
#   python check_data.py
#
# or as:
#
#   python check_data.py <problem_data_file_name>
#

# this file is OK
data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707.json'

# these files have multiple errors. The data reader should find and report all (maybe only some?)
# of them by raising an exception.
#data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707_read_errors.json'
#data_file = '/people/holz501/gocomp/c3/data/Jesse/14bus/14bus_20220707_model_errors.json'

# error message starts with, e.g.:
# pydantic.error_wrappers.ValidationError: 9 validation errors for InputDataFile

def summarize_problem_data(data):

    # print('data: {}'.format(list(data.dict().keys())))
    
    network = data.network
    # print('network: {}'.format(list(network.dict().keys())))
    
    general = network.general
    vio_cost = network.violation_cost
    
    print('general: {}'.format(general))
    print('violation costs: {}'.format(vio_cost))
    
    bus = network.bus
    acl = network.ac_line
    dcl = network.dc_line
    xfr = network.two_winding_transformer
    sh = network.shunt
    sd = network.simple_dispatchable_device
    pd = [i for i in network.simple_dispatchable_device if i.device_type == 'producer']
    cd = [i for i in network.simple_dispatchable_device if i.device_type == 'consumer']
    prz = network.active_zonal_reserve
    qrz = network.reactive_zonal_reserve
    
    num_bus = len(bus)
    num_acl = len(acl)
    num_dcl = len(dcl)
    num_xfr = len(xfr)
    num_sh = len(sh)
    num_sd = len(sd)
    num_pd = len(pd)
    num_cd = len(cd)
    num_prz = len(prz)
    num_qrz = len(qrz)
    
    print('num buses: {}'.format(num_bus))
    print('num ac lines: {}'.format(num_acl))
    print('num dc lines: {}'.format(num_dcl))
    print('num transformers: {}'.format(num_xfr))
    print('num shunts: {}'.format(num_sh))
    print('num simple dispatchable devices: {}'.format(num_sd))
    print('num producing devices: {}'.format(num_pd))
    print('num consuming devices: {}'.format(num_cd))
    print('num real power reserve zones: {}'.format(num_prz))
    print('num reactive power reserve zones: {}'.format(num_qrz))
    
    time_series_input = data.time_series_input
    # print('time_series_input: {}'.format(list(time_series_input.dict().keys())))
    
    ts_general = time_series_input.general
    # print('ts general: {}'.format(list(ts_general.dict().keys())))
    
    num_t = ts_general.time_periods
    print('num intervals: {}'.format(num_t))
    
    ts_intervals = ts_general.interval_duration
    ts_sd = time_series_input.simple_dispatchable_device
    ts_prz = time_series_input.active_zonal_reserve
    ts_qrz = time_series_input.reactive_zonal_reserve

    print('total duration: {}'.format(sum(ts_intervals)))
    print('interval durations: {}'.format(ts_intervals))

def check_problem_data(problem_data_file):

    problem_data_model = InputDataFile.load(problem_data_file)
    validation.all_checks(problem_data_model)
    return problem_data_model
    
if __name__ == '__main__':

    try:
        utils.print_git_info_all()
    except Exception as e:
        print('error in print_git_info_all, not raising the exception')
        traceback.print_exc()
        #print(e)
    if len(sys.argv) > 1:
        problem_data_file_name = sys.argv[1]
    else:
        problem_data_file_name = data_file
    print('problem data file: {}'.format(problem_data_file_name))
    problem_data_model = check_problem_data(problem_data_file_name)
    summarize_problem_data(problem_data_model)
