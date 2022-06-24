import sys
from datamodel.input.data import InputDataFile

# run this either as:
#
#   python read_problem_data_test.py
#
# or as:
#
#   python read_problem_data_test.py <problem_data_file_name>
#

# this file is OK
data_file = '/people/holz501/gocomp/c3/data/PSY_RTS_GMLC_data_fixed_load_20220510.json'

# this file has multiple errors. The data reader should find and report all (maybe only some?)
# of them by raising an exception.
#data_file = '/people/holz501/gocomp/c3/data/PSY_RTS_GMLC_data_fixed_load_20220510_multiple_errors.json'

# error message starts with, e.g.:
# pydantic.error_wrappers.ValidationError: 9 validation errors for InputDataFile

def read_validate_summarize_problem_data(problem_data_file):
    '''
    This function demonstrates how you might use the Bid-DS problem data model
    to read a problem data file into Bid-DS data structures,
    perform read-time validation,
    then get a handle on the data as represented in the data structures
    as a preliminary step to further validation/checking, scrubbing,
    conversion to numpy data structures, and finally use in solution evaluation.

    The input argument is a file/path name of a problem data file.
    The function reads that file.
    Read-time validation is performed, with an error raised if any data errors are encountered there.
    Then a Bid-DS data model object is populated from the data.
    Then the Bid-DS data model object is explored and some basic summary information is printed.
    '''

    print('Start reading problem data into Bid-DS problem data model and performing read-time validation.')
    print('Problem data file name: {}'.format(problem_data_file))
    problem_data = InputDataFile.load(problem_data_file)
    print('Done reading problem data into Bid-DS problem data model. If no error is raised, then read-time validation was successful, and no errors were found in the data.')
    
    print('problem_data: {}'.format(list(problem_data.dict().keys())))
    
    network = problem_data.network
    print('network: {}'.format(list(network.dict().keys())))
    
    general = network.general
    vio_cost = network.violation_cost
    
    print('general: {}'.format(general))
    print('vio_cost: {}'.format(vio_cost))
    
    bus = network.bus
    acl = network.ac_line
    dcl = network.dc_line
    xfr = network.two_winding_transformer
    sh = network.shunt
    sd = network.simple_dispatchable_device
    prz = network.active_zonal_reserve
    qrz = network.reactive_zonal_reserve
    
    num_bus = len(bus)
    num_acl = len(acl)
    num_dcl = len(dcl)
    num_xfr = len(xfr)
    num_sh = len(sh)
    num_sd = len(sd)
    num_prz = len(prz)
    num_qrz = len(qrz)
    
    print('num bus: {}'.format(num_bus))
    print('num acl: {}'.format(num_acl))
    print('num dcl: {}'.format(num_dcl))
    print('num xfr: {}'.format(num_xfr))
    print('num sh: {}'.format(num_sh))
    print('num sd: {}'.format(num_sd))
    print('num prz: {}'.format(num_prz))
    print('num qrz: {}'.format(num_qrz))
    
    time_series_input = problem_data.time_series_input
    print('time_series_input: {}'.format(list(time_series_input.dict().keys())))
    
    ts_general = time_series_input.general
    print('ts general: {}'.format(list(ts_general.dict().keys())))
    
    num_t = ts_general.time_periods
    print('num t: {}'.format(num_t))
    
    ts_sd = time_series_input.simple_dispatchable_device
    ts_prz = time_series_input.active_zonal_reserve
    ts_qrz = time_series_input.reactive_zonal_reserve
    num_ts_sd = len(ts_sd)
    num_ts_prz = len(ts_prz)
    num_ts_qrz = len(ts_qrz)
    print('ts num sd: {}'.format(num_ts_sd))
    print('ts num prz: {}'.format(num_ts_prz))
    print('ts num qrz: {}'.format(num_ts_qrz))

if __name__ == '__main__':
    if len(sys.argv) > 1:
        problem_data_file_name = sys.argv[1]
    else:
        problem_data_file_name = data_file
    read_validate_summarize_problem_data(problem_data_file_name)
