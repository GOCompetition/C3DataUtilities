'''

'''

import networkx, traceback, pprint, json, re, pandas, time
from pydantic.error_wrappers import ValidationError
from datamodel.input.data import InputDataFile
from datamodel.output.data import OutputDataFile
from datautilities import utils
from datautilities.errors import ModelError, GitError

timestamp_pattern_str = '\A[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\Z'

def write(file_name, mode, text):

    with open(file_name, mode) as f:
        f.write(text)

def read_config(config_file):

    with open(config_file, 'r') as f:
        config = json.load(f)
    return config

def check_data(problem_file, solution_file, config_file, summary_file, problem_errors_file, ignored_errors_file, solution_errors_file):

    # read config
    config = read_config(config_file)
    #print('config: {}'.format(config))

    # open files
    for fn in [summary_file, problem_errors_file, ignored_errors_file, solution_errors_file]:
        with open(fn, 'w') as f:
            pass
    # - todo solution summary file? for now just use the problem summary file. that may be the right way anyway
    solution_summary_file = summary_file

    # data file
    with open(summary_file, 'a') as f:
        f.write('problem data file: {}\n'.format(problem_file))
    with open(summary_file, 'a') as f:
        f.write('solution data file: {}\n'.format(solution_file))

    # git info
    try:
        git_info = utils.get_git_info_all()
        with open(summary_file, 'a') as f:
            f.write('git info: {}\n'.format(git_info))
    except GitError:
        with open(summary_file, 'a') as f:
            f.write('git info error ignored\n')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())
    except Exception:
        with open(summary_file, 'a') as f:
            f.write('git info error ignored\n')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())

    # read data
    start_time = time.time()
    try:
        data_model = InputDataFile.load(problem_file)
    except ValidationError as e:
        with open(summary_file, 'a') as f:
            f.write('data read error - pydantic validation\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    end_time = time.time()
    print('load time: {}'.format(end_time - start_time))

    # independent data model checks
    start_time = time.time()
    try:
        model_checks(data_model, config)
    except ModelError as e:
        with open(summary_file, 'a') as f:
            f.write('model error - independent checks\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    end_time = time.time()
    print('model_checks time: {}'.format(end_time - start_time))

    # connectedness check
    start_time = time.time()
    try:
        connected(data_model, config)
    except ModelError as e:
        with open(summary_file, 'a') as f:
            f.write('model error - connectedness\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    end_time = time.time()
    print('connected time: {}'.format(end_time - start_time))

    # summary
    summary = get_summary(data_model)
    with open(summary_file, 'a') as f:
        pp = pprint.PrettyPrinter()
        pp.pprint(summary)
        #f.write('data summary: {}'.format(pp.pprint(summary)))
        f.write('data summary:\n')
        f.write(pp.pformat(summary))
        f.write('\n')

    if solution_file is not None:

        # read solution
        start_time = time.time()
        #print('solution file: {}'.format(solution_file))
        try:
            solution_data_model = OutputDataFile.load(solution_file)
        except ValidationError as e:
            with open(summary_file, 'a') as f:
                f.write('solution read error - pydantic validation')
            with open(solution_errors_file, 'a') as f:
                f.write(traceback.format_exc())
            raise e
        end_time = time.time()
        print('solution load time: {}'.format(end_time - start_time))
        
        # solution data model checks
        start_time = time.time()
        try:
            solution_model_checks(data_model, solution_data_model, config)
        except ModelError as e:
            with open(summary_file, 'a') as f:
                f.write('solution model error - independent checks\n')
            with open(solution_errors_file, 'a') as f:
                f.write(traceback.format_exc())
            raise e
        end_time = time.time()
        print('solution model_checks time: {}'.format(end_time - start_time))

        # summary
        solution_summary = get_solution_summary(data_model, solution_data_model)
        with open(solution_summary_file, 'a') as f:
            pp = pprint.PrettyPrinter()
            pp.pprint(solution_summary)
            f.write('solution data summary:\n')
            f.write(pp.pformat(solution_summary))
            f.write('\n')

        # print('solution data')
        # for s in ['bus', 'shunt', 'simple_dispatchable_device', 'ac_line', 'dc_line', 'two_winding_transformer']:
        #     print('section: {}'.format(s))
        #     for i in solution_data_model.time_series_output.__dict__[s]:
        #         for k, v in i.__dict__.items():
        #             if k == 'uid':
        #                 print('  {}: {}'.format(k, v))
        #             else:
        #                 print('    {}: {}'.format(k, v))            

def get_summary(data):

    summary = {}

    network = data.network
    
    summary['general'] = network.general
    summary['violation costs'] = network.violation_cost
    
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
    
    summary['num buses'] = num_bus
    summary['num ac lines'] = num_acl
    summary['num dc lines'] = num_dcl
    summary['num transformers'] = num_xfr
    summary['num shunts'] = num_sh
    summary['num simple dispatchable devices'] = num_sd
    summary['num producing devices'] = num_pd
    summary['num consuming devices'] = num_cd
    summary['num real power reserve zones'] = num_prz
    summary['num reactive power reserve zones'] = num_qrz
    
    time_series_input = data.time_series_input
    
    ts_general = time_series_input.general
    
    num_t = ts_general.time_periods
    summary['num intervals'] = num_t
    
    ts_intervals = ts_general.interval_duration
    ts_sd = time_series_input.simple_dispatchable_device
    ts_prz = time_series_input.active_zonal_reserve
    ts_qrz = time_series_input.reactive_zonal_reserve

    ctgs = data.reliability.contingency
    num_k = len(ctgs)
    summary['num contingencies'] = num_k

    summary['total duration'] = sum(ts_intervals)
    summary['interval durations'] = ts_intervals
    
    return summary

def get_solution_summary(problem_data, solution_data):

    problem_summary = get_summary(problem_data)
    # todo add solution info - is there anything?
    solution_summary = {}
    return solution_summary

def model_checks(data, config):

    checks = [
        timestamp_start_required,
        timestamp_stop_required,
        timestamp_start_valid,
        timestamp_stop_valid,
        timestamp_start_ge_min,
        total_horizon_le_timestamp_max_minus_start,
        timestamp_stop_le_max,
        timestamp_stop_minus_start_eq_total_horizon,
        # interval_duratations in interval_duration_schedules - distinguish between divisions - TODO
        interval_duration_in_schedules,
        network_and_reliability_uids_not_repeated,
        ts_uids_not_repeated,
        ctg_dvc_uids_in_domain,
        bus_prz_uids_in_domain,
        bus_qrz_uids_in_domain,
        shunt_bus_uids_in_domain,
        sd_bus_uids_in_domain,
        sd_type_in_domain,
        acl_fr_bus_uids_in_domain,
        acl_to_bus_uids_in_domain,
        xfr_fr_bus_uids_in_domain,
        xfr_to_bus_uids_in_domain,
        dcl_fr_bus_uids_in_domain,
        dcl_to_bus_uids_in_domain,
        ts_sd_uids_in_domain,
        ts_sd_uids_cover_domain,
        ts_prz_uids_in_domain,
        ts_prz_uids_cover_domain,
        ts_qrz_uids_in_domain,
        ts_qrz_uids_cover_domain,
        ts_sd_on_status_ub_len_eq_num_t,
        ts_sd_on_status_lb_len_eq_num_t,
        ts_sd_p_lb_len_eq_num_t,
        ts_sd_p_ub_len_eq_num_t,
        ts_sd_q_lb_len_eq_num_t,
        ts_sd_q_ub_len_eq_num_t,
        ts_sd_cost_len_eq_num_t,
        ts_sd_p_reg_res_up_cost_len_eq_num_t,
        ts_sd_p_reg_res_down_cost_len_eq_num_t,
        ts_sd_p_syn_res_cost_len_eq_num_t,
        ts_sd_p_nsyn_res_cost_len_eq_num_t,
        ts_sd_p_ramp_res_up_online_cost_len_eq_num_t,
        ts_sd_p_ramp_res_down_online_cost_len_eq_num_t,
        ts_sd_p_ramp_res_down_offline_cost_len_eq_num_t,
        ts_sd_p_ramp_res_up_offline_cost_len_eq_num_t,
        ts_sd_q_res_up_cost_len_eq_num_t,
        ts_sd_q_res_down_cost_len_eq_num_t,
        ts_prz_ramping_reserve_up_len_eq_num_t,
        ts_prz_ramping_reserve_down_len_eq_num_t,
        ts_qrz_react_up_len_eq_num_t,
        ts_qrz_react_down_len_eq_num_t,
        ts_sd_on_status_lb_le_ub,
        ts_sd_p_lb_le_ub,
        ts_sd_q_lb_le_ub,
        ]
    errors = []
    # try:
    #     timestamp_start_ge_min(data, config)
    # except ModelError as e:
    #     errors.append(e)
    # except Exception as e:
    #     msg = (
    #         'validation.model_checks found errors\n' + 
    #         'number of errors: {}\n'.format(len(errors)) +
    #         '\n'.join([str(e) for e in errors]))
    #     if len(errors) > 0:
    #         raise ModelError(msg)
    #     else:
    #         raise e
    for c in checks:
        try:
            c(data, config)
        except ModelError as e:
            errors.append(e)
        except Exception as e:
            msg = (
                'validation.model_checks found errors\n' + 
                'number of errors: {}\n'.format(len(errors)) +
                '\n'.join([str(e) for e in errors]))
            if len(errors) > 0:
                raise ModelError(msg)
            else:
                raise e
    if len(errors) > 0:
        msg = (
            'validation.model_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(r) for r in errors]))
        raise ModelError(msg)

def solution_model_checks(data, solution_data, config):

    checks = [
        output_ts_uids_not_repeated,
        output_ts_bus_uids_in_domain,
        output_ts_bus_uids_cover_domain,
        output_ts_shunt_uids_in_domain,
        output_ts_shunt_uids_cover_domain,
        output_ts_simple_dispatchable_device_uids_in_domain,
        output_ts_simple_dispatchable_device_uids_cover_domain,
        output_ts_ac_line_uids_in_domain,
        output_ts_ac_line_uids_cover_domain,
        output_ts_dc_line_uids_in_domain,
        output_ts_dc_line_uids_cover_domain,
        output_ts_two_winding_transformer_uids_in_domain,
        output_ts_two_winding_transformer_uids_cover_domain,
        output_ts_bus_vm_len_eq_num_t,
        output_ts_bus_va_len_eq_num_t,
        output_ts_shunt_step_len_eq_num_t,
        output_ts_simple_dispatchable_device_on_status_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_on_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_reg_res_up_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_reg_res_down_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_syn_res_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_nsyn_res_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_up_online_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_down_online_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_up_offline_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_down_offline_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_res_up_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_res_down_len_eq_num_t,
        output_ts_ac_line_on_status_len_eq_num_t,
        output_ts_dc_line_p_dc_fr_len_eq_num_t,
        output_ts_dc_line_q_dc_fr_len_eq_num_t,
        output_ts_dc_line_q_dc_to_len_eq_num_t,
        output_ts_two_winding_transformer_on_status_len_eq_num_t,
        output_ts_two_winding_transformer_tm_len_eq_num_t,
        output_ts_two_winding_transformer_ta_len_eq_num_t,
    ]
    errors = []
    for c in checks:
        try:
            c(data, solution_data, config)
        except ModelError as e:
            errors.append(e)
        except Exception as e:
            msg = (
                'validation.solution_model_checks found errors\n' + 
                'number of errors: {}\n'.format(len(errors)) +
                '\n'.join([str(e) for e in errors]))
            if len(errors) > 0:
                raise ModelError(msg)
            else:
                raise e
    if len(errors) > 0:
        msg = (
            'validation.solution_model_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(r) for r in errors]))
        raise ModelError(msg)

def valid_timestamp_str(data):
    '''
    returns True if data is a valid timestamp string else False
    '''

    valid = True
    if not isinstance(data, str):
        valid = False
    elif re.search(timestamp_pattern_str, data) is None:
        valid = False
    return valid

def timestamp_start_required(data, config):

    if config['timestamp_start_required']:
        if data.network.general.timestamp_start is None:
            msg = 'data -> general -> timestamp_start required by config, not present in data'
            raise ModelError(msg)

def timestamp_stop_required(data, config):

    if config['timestamp_stop_required']:
        if data.network.general.timestamp_stop is None:
            msg = 'data -> general -> timestamp_stop required by config, not present in data'
            raise ModelError(msg)

def timestamp_start_valid(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        if not valid_timestamp_str(start):
            raise ModelError(
                'data -> general -> timestamp_start not a valid timestamp string - incorrect format. expected: "{}", got: "{}"'.format(
                    timestamp_pattern_str, start))
        try:
            timestamp = pandas.Timestamp(start)
        except:
            raise ModelError(
                'data -> general -> timestamp_start not a valid timestamp string - could not parse data: "{}"'.format(start))            

def timestamp_stop_valid(data, config):

    end = data.network.general.timestamp_stop
    if end is not None:
        if not valid_timestamp_str(end):
            raise ModelError(
                'data -> general -> timestamp_stop not a valid timestamp string - incorrect format. expected: "{}", got: "{}"'.format(
                    timestamp_pattern_str, end))
        try:
            timestamp = pandas.Timestamp(end)
        except:
            raise ModelError(
                'data -> general -> timestamp_stop not a valid timestamp string - could not parse data: "{}"'.format(end))            

def timestamp_start_ge_min(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        min_time = config['timestamp_min']
        if pandas.Timestamp(min_time) > pandas.Timestamp(start):
            msg = 'fails {} <= {}. {}: {}, {}: {}'.format(
                'config.timestamp_min', 'data.network.general.timestamp_start',
                'config.timestamp_min', min_time, 'data.network.general.timestamp_start', start)
            raise ModelError(msg)

def total_horizon_le_timestamp_max_minus_start(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        max_time = config['timestamp_max']
        timestamp_delta = (pandas.Timestamp(max_time) - pandas.Timestamp(start)).total_seconds() / 3600.0
        total_horizon = sum(data.time_series_input.general.interval_duration)
        if total_horizon > timestamp_delta:
            msg = 'fails total_horizon <= timestamp_max - timestamp_start. config.timestamp_max: {}, data.timestamp_start: {}, data.interval_duration: {}, timestamp_max - timestamp_start: {}, sum(interval_duration): {}'.format(
                max_time, start, data.time_series_input.general.interval_duration, timestamp_delta, total_horizon)
            raise ModelError(msg)

def timestamp_stop_le_max(data, config):

    stop = data.network.general.timestamp_stop
    if stop is not None:
        max_time = config['timestamp_max']
        if pandas.Timestamp(max_time) < pandas.Timestamp(stop):
            msg = 'fails {} <= {}. {}: {}, {}: {}'.format(
                'data.network.general.timestamp_stop',
                'config.timestamp_max',
                'data.network.general.timestamp_stop', stop,
                'config.timestamp_max', max_time)
            raise ModelError(msg)

def timestamp_stop_minus_start_eq_total_horizon(data, config):

    start = data.network.general.timestamp_start
    stop = data.network.general.timestamp_stop
    if (start is not None) and (stop is not None):
        timestamp_delta = (pandas.Timestamp(stop) - pandas.Timestamp(start)).total_seconds() / 3600.0
        total_horizon = sum(data.time_series_input.general.interval_duration)
        if abs(timestamp_delta - total_horizon) > config['time_eq_tol']:
            msg = 'fails timestamp_stop - timestamp_start == sum(interval_duration). timestamp_stop: {}, timestamp_start: {}, interval_duration: {}, timestamp_stop - timestamp_start: {}, sum(interval_duration): {}, config.time_eq_tol: {}'.format(
                stop, start, data.time_series_input.general.interval_duration, timestamp_delta, total_horizon, config['time_eq_tol'])
            raise ModelError(msg)

# interval_duratations in interval_duration_schedules - TODO - recognize division
def interval_duration_in_schedules(data, config):
    
    interval_durations = data.time_series_input.general.interval_duration
    num_intervals = len(interval_durations)
    schedules = config['interval_duration_schedules']
    schedules_right_len = [s for s in schedules if len(s) == num_intervals]
    schedules_match = [
        s for s in schedules_right_len
        if all([(s[i] == interval_durations[i]) for i in range(num_intervals)])]
    found = (len(schedules_match) > 0)
    if not found:
        msg = "fails data.time_series_input.general.interval_duration in config.interval_duration_schedules. data: {}, config: {}".format(
            interval_durations, schedules)
        raise ModelError(msg)

def output_ts_uids_not_repeated(data, output_data, config):

    uids = output_data.time_series_output.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in time_series_output section. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def ts_uids_not_repeated(data, config):

    uids = data.time_series_input.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in time_series_input section. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def network_and_reliability_uids_not_repeated(data, config):
    
    uids = data.network.get_uids() + data.reliability.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in network and reliability sections. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def ctg_dvc_uids_in_domain(data, config):

    # todo make this more efficient
    domain = (
        data.network.get_ac_line_uids() +
        data.network.get_two_winding_transformer_uids() +
        data.network.get_dc_line_uids())
    domain = set(domain)
    num_ctg = len(data.reliability.contingency)
    ctg_comp_not_in_domain = [
        list(set(data.reliability.contingency[i].components).difference(domain))
        for i in range(num_ctg)]
    ctg_idx_comp_not_in_domain = [
        i for i in range(num_ctg)
        if len(ctg_comp_not_in_domain[i]) > 0]
    ctg_comp_not_in_domain = [
        (i, data.reliability.contingency[i].uid, ctg_comp_not_in_domain[i])
        for i in ctg_idx_comp_not_in_domain]
    if len(ctg_idx_comp_not_in_domain) > 0:
        msg = "fails contingency outaged devices in branches. failing contingencies (index, uid, failing devices): {}".format(
            ctg_comp_not_in_domain)
        raise ModelError(msg)

def items_field_in_domain(items, field, domain, items_name, domain_name):
    # todo - use this - more efficient than set membership in a loop

    domain_set = set(domain)
    domain_size = len(domain_set)
    values = [getattr(i, field) for i in items]
    values_not_in_domain = set(values).difference(domain_set)
    all_values = list(domain_set) + list(values_not_in_domain)
    all_values_map = {all_values[i]:i for i in range(len(all_values))}
    failures = [(i, items[i].uid, values[i]) for i in range(len(items)) if all_values_map[values[i]] >= domain_size]
    if len(failures) > 0:
        msg = "fails items field in domain. items: {}, field: {}, domain: {}, failing items (index, uid, field value): {}".format(items_name, field, domain_name, failures)
        raise ModelError(msg)

def items_field_cover_domain(items, field, domain, items_name, domain_name):
    # todo - use this - more efficient than set membership in a loop

    values = [getattr(i, field) for i in items]
    values = set(values)
    failures = list(set(domain).difference(values))
    if len(failures) > 0:
        msg = "fails items field cover domain. items: {}, field: {}, domain: {}, failing domain elements: {}".format(items_name, field, domain_name, failures)
        raise ModelError(msg)

def output_ts_bus_uids_in_domain(data, solution, config):

    items = solution.time_series_output.bus
    field = 'uid'
    domain = data.network.get_bus_uids()
    items_name = 'time_series_output.bus'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_bus_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.bus
    field = 'uid'
    domain = data.network.get_bus_uids()
    items_name = 'time_series_output.bus'
    domain_name = 'network.bus.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_shunt_uids_in_domain(data, solution, config):

    items = solution.time_series_output.shunt
    field = 'uid'
    domain = data.network.get_shunt_uids()
    items_name = 'time_series_output.shunt'
    domain_name = 'network.shunt.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_shunt_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.shunt
    field = 'uid'
    domain = data.network.get_shunt_uids()
    items_name = 'time_series_output.shunt'
    domain_name = 'network.shunt.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_simple_dispatchable_device_uids_in_domain(data, solution, config):

    items = solution.time_series_output.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_output.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_simple_dispatchable_device_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_output.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_ac_line_uids_in_domain(data, solution, config):

    items = solution.time_series_output.ac_line
    field = 'uid'
    domain = data.network.get_ac_line_uids()
    items_name = 'time_series_output.ac_line'
    domain_name = 'network.ac_line.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_ac_line_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.ac_line
    field = 'uid'
    domain = data.network.get_ac_line_uids()
    items_name = 'time_series_output.ac_line'
    domain_name = 'network.ac_line.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_dc_line_uids_in_domain(data, solution, config):

    items = solution.time_series_output.dc_line
    field = 'uid'
    domain = data.network.get_dc_line_uids()
    items_name = 'time_series_output.dc_line'
    domain_name = 'network.dc_line.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_dc_line_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.dc_line
    field = 'uid'
    domain = data.network.get_dc_line_uids()
    items_name = 'time_series_output.dc_line'
    domain_name = 'network.dc_line.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_two_winding_transformer_uids_in_domain(data, solution, config):

    items = solution.time_series_output.two_winding_transformer
    field = 'uid'
    domain = data.network.get_two_winding_transformer_uids()
    items_name = 'time_series_output.two_winding_transformer'
    domain_name = 'network.two_winding_transformer.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_two_winding_transformer_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.two_winding_transformer
    field = 'uid'
    domain = data.network.get_two_winding_transformer_uids()
    items_name = 'time_series_output.two_winding_transformer'
    domain_name = 'network.two_winding_transformer.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def bus_prz_uids_in_domain(data, config):

    # todo - this might be inefficient - can we get it down to just one set difference operation? I think so,
    # look at the set of (i, j) for i in buses for j in reserve_zones[i] and
    # the set of (i, j) for i in buses for j in reserve_zones
    domain = data.network.get_active_zonal_reserve_uids()
    domain = set(domain)
    num_bus = len(data.network.bus)
    bus_prz_not_in_domain = [
        list(set(data.network.bus[i].active_reserve_uids).difference(domain))
        for i in range(num_bus)]
    bus_idx_prz_not_in_domain = [
        i for i in range(num_bus)
        if len(bus_prz_not_in_domain[i]) > 0]
    bus_prz_not_in_domain = [
        (i, data.network.bus[i].uid, bus_prz_not_in_domain[i])
        for i in bus_idx_prz_not_in_domain]
    if len(bus_idx_prz_not_in_domain) > 0:
        msg = "fails bus real power reserve zones in real power reserve zones. failing buses (index, uid, failing zones): {}".format(
            bus_prz_not_in_domain)
        raise ModelError(msg)

def bus_qrz_uids_in_domain(data, config):

    # todo see above todo item in bus_prz_uids_in_domain
    domain = data.network.get_reactive_zonal_reserve_uids()
    domain = set(domain)
    num_bus = len(data.network.bus)
    bus_qrz_not_in_domain = [
        list(set(data.network.bus[i].reactive_reserve_uids).difference(domain))
        for i in range(num_bus)]
    bus_idx_qrz_not_in_domain = [
        i for i in range(num_bus)
        if len(bus_qrz_not_in_domain[i]) > 0]
    bus_qrz_not_in_domain = [
        (i, data.network.bus[i].uid, bus_qrz_not_in_domain[i])
        for i in bus_idx_qrz_not_in_domain]
    if len(bus_idx_qrz_not_in_domain) > 0:
        msg = "fails bus reactive power reserve zones in reactive power reserve zones. failing buses (index, uid, failing zones): {}".format(
            bus_qrz_not_in_domain)
        raise ModelError(msg)

def shunt_bus_uids_in_domain(data, config):

    items = data.network.shunt
    field = 'bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.shunt'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def sd_bus_uids_in_domain(data, config):

    items = data.network.simple_dispatchable_device
    field = 'bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.simple_dispatchable_device'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def sd_type_in_domain(data, config):

    items = data.network.simple_dispatchable_device
    field = 'device_type'
    domain = ['producer', 'consumer']
    items_name = 'network.simple_dispatchable_device'
    domain_name = str(domain)
    items_field_in_domain(items, field, domain, items_name, domain_name)

def acl_fr_bus_uids_in_domain(data, config):

    #start_time = time.time()

    ### should be fast
    items = data.network.ac_line
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.ac_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

    ### might be slower
    # domain = data.network.get_bus_uids()
    # domain = set(domain)
    # num_dvc = len(data.network.ac_line)
    # dvc_idx_bus_not_in_domain = [
    #     i for i in range(num_dvc)
    #     if not (data.network.ac_line[i].fr_bus in domain)]
    # dvc_bus_not_in_domain = [
    #     (i, data.network.ac_line[i].uid, data.network.ac_line[i].fr_bus)
    #     for i in dvc_idx_bus_not_in_domain]
    # if len(dvc_idx_bus_not_in_domain) > 0:
    #     msg = "fails ac line from bus in buses. failing devices (index, uid, from bus uid): {}".format(
    #         dvc_bus_not_in_domain)
    #     raise ModelError(msg)

    #end_time = time.time()
    #print('acl_fr_bus_uids_in_domain time: {}'.format(end_time - start_time))

def acl_to_bus_uids_in_domain(data, config):

    items = data.network.ac_line
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.ac_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def xfr_fr_bus_uids_in_domain(data, config):

    items = data.network.two_winding_transformer
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.two_winding_transformer'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def xfr_to_bus_uids_in_domain(data, config):

    items = data.network.two_winding_transformer
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.two_winding_transformer'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def dcl_fr_bus_uids_in_domain(data, config):

    items = data.network.dc_line
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.dc_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def dcl_to_bus_uids_in_domain(data, config):

    items = data.network.dc_line
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.dc_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_sd_uids_in_domain(data, config):

    items = data.time_series_input.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_input.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_sd_uids_cover_domain(data, config):

    items = data.time_series_input.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_input.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_prz_uids_in_domain(data, config):

    items = data.time_series_input.active_zonal_reserve
    field = 'uid'
    domain = data.network.get_active_zonal_reserve_uids()
    items_name = 'time_series_input.active_zonal_reserve'
    domain_name = 'network.active_zonal_reserve.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_prz_uids_cover_domain(data, config):

    items = data.time_series_input.active_zonal_reserve
    field = 'uid'
    domain = data.network.get_active_zonal_reserve_uids()
    items_name = 'time_series_input.active_zonal_reserve'
    domain_name = 'network.active_zonal_reserve.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_qrz_uids_in_domain(data, config):

    items = data.time_series_input.reactive_zonal_reserve
    field = 'uid'
    domain = data.network.get_reactive_zonal_reserve_uids()
    items_name = 'time_series_input.reactive_zonal_reserve'
    domain_name = 'network.reactive_zonal_reserve.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_qrz_uids_cover_domain(data, config):
    
    items = data.time_series_input.reactive_zonal_reserve
    field = 'uid'
    domain = data.network.get_reactive_zonal_reserve_uids()
    items_name = 'time_series_input.reactive_zonal_reserve'
    domain_name = 'network.reactive_zonal_reserve.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_sd_on_status_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'on_status_ub')

def ts_sd_on_status_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'on_status_lb')

def ts_sd_p_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_lb')

def ts_sd_p_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ub')

def ts_sd_q_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_lb')

def ts_sd_q_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_ub')

def ts_sd_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'cost')

def ts_sd_p_reg_res_up_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_reg_res_up_cost')

def ts_sd_p_reg_res_down_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_reg_res_down_cost')

def ts_sd_p_syn_res_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_syn_res_cost')

def ts_sd_p_nsyn_res_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_nsyn_res_cost')

def ts_sd_p_ramp_res_up_online_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_up_online_cost')

def ts_sd_p_ramp_res_down_online_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_down_online_cost')

def ts_sd_p_ramp_res_down_offline_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_down_offline_cost')

def ts_sd_p_ramp_res_up_offline_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_up_offline_cost')

def ts_sd_q_res_up_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_res_up_cost')

def ts_sd_q_res_down_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_res_down_cost')

def ts_prz_ramping_reserve_up_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'active_zonal_reserve', 'RAMPING_RESERVE_UP')

def ts_prz_ramping_reserve_down_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'active_zonal_reserve', 'RAMPING_RESERVE_DOWN')

def ts_qrz_react_up_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'reactive_zonal_reserve', 'REACT_UP')

def ts_qrz_react_down_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'reactive_zonal_reserve', 'REACT_DOWN')

def ts_component_field_len_eq_num_t(data, component, field):

    num_t = len(data.time_series_input.general.interval_duration)
    component_uids = [c.uid for c in getattr(data.time_series_input, component)]
    component_lens = [len(getattr(c, field)) for c in getattr(data.time_series_input, component)]
    idx_err = [
        (i, component_uids[i], component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input {} len({}) == len(intervals). len(intervals): {}. failing items (idx, uid, len({})): {}".format(
            component, field, num_t, field, idx_err)
        raise ModelError(msg)

def output_ts_component_field_len_eq_num_t(data, solution, component, field):

    num_t = len(data.time_series_input.general.interval_duration)
    component_uids = [c.uid for c in getattr(solution.time_series_output, component)]
    component_lens = [len(getattr(c, field)) for c in getattr(solution.time_series_output, component)]
    idx_err = [
        (i, component_uids[i], component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_output {} len({}) == len(time_series_input.intervals). len(intervals): {}. failing items (idx, uid, len({})): {}".format(
            component, field, num_t, field, idx_err)
        raise ModelError(msg)

def output_ts_bus_vm_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'bus', 'vm')

def output_ts_bus_va_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'bus', 'va')
    
def output_ts_shunt_step_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'shunt', 'step')

def output_ts_simple_dispatchable_device_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'on_status')

def output_ts_simple_dispatchable_device_p_on_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_on')

def output_ts_simple_dispatchable_device_q_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q')

def output_ts_simple_dispatchable_device_p_reg_res_up_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_reg_res_up')

def output_ts_simple_dispatchable_device_p_reg_res_down_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_reg_res_down')

def output_ts_simple_dispatchable_device_p_syn_res_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_syn_res')

def output_ts_simple_dispatchable_device_p_nsyn_res_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_nsyn_res')

def output_ts_simple_dispatchable_device_p_ramp_res_up_online_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_up_online')

def output_ts_simple_dispatchable_device_p_ramp_res_down_online_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_down_online')

def output_ts_simple_dispatchable_device_p_ramp_res_up_offline_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_up_offline')

def output_ts_simple_dispatchable_device_p_ramp_res_down_offline_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_down_offline')

def output_ts_simple_dispatchable_device_q_res_up_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q_res_up')

def output_ts_simple_dispatchable_device_q_res_down_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q_res_down')

def output_ts_ac_line_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'ac_line', 'on_status')

def output_ts_dc_line_p_dc_fr_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'p_dc_fr')

def output_ts_dc_line_q_dc_fr_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'q_dc_fr')

def output_ts_dc_line_q_dc_to_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'q_dc_to')

def output_ts_two_winding_transformer_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'on_status')

def output_ts_two_winding_transformer_tm_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'tm')

def output_ts_two_winding_transformer_ta_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'ta')

def ts_sd_on_status_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.on_status_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.on_status_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device on_status_lb <= on_status_ub. failures (device index, device uid, interval index, on_status_lb, on_status_ub): {}".format(idx_err)
        raise ModelError(msg)

def ts_sd_p_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.p_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.p_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device p_lb <= p_ub. failures (device index, device uid, interval index, p_lb, p_ub): {}".format(idx_err)
        raise ModelError(msg)

def ts_sd_q_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.q_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.q_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device q_lb <= q_ub. failures (device index, device uid, interval index, q_lb, q_ub): {}".format(idx_err)
        raise ModelError(msg)

def connected(data, config):

    msg = ""

    # get buses, branches, and contingencies that are relavant to this check
    # i.e. all buses, AC in service branches, contingencies outaging AC in service branches
    buses, branches, ctgs = get_buses_branches_ctgs_on_in_service_ac_network(data)
    num_buses = len(buses)
    num_branches = len(branches)
    num_ctgs = len(ctgs)

    # get uids in natural order (ordinal index -> uid)
    buses_uid = [i.uid for i in buses]
    branches_uid = [i.uid for i in branches]
    branches_fbus_uid = [i.fr_bus for i in branches]
    branches_tbus_uid = [i.to_bus for i in branches]
    ctgs_uid = [i.uid for i in ctgs]
    ctgs_branch_uid = [i.components[0] for i in ctgs] # exactly one branch outaged in each contingency

    # map uids to indices
    bus_uid_map = {buses_uid[i]: i for i in range(num_buses)}
    branch_uid_map = {branches_uid[i]: i for i in range(num_branches)}
    ctg_uid_map = {ctgs_uid[i]: i for i in range(num_ctgs)}

    # get branch outaged by each contingency
    ctgs_branch = [branch_uid_map[i] for i in ctgs_branch_uid]

    # get uids on from and to buses of branch outaged in each contingency
    ctgs_branch_fbus_uid = [branches_fbus_uid[branch_uid_map[i]] for i in ctgs_branch_uid]
    ctgs_branch_tbus_uid = [branches_tbus_uid[branch_uid_map[i]] for i in ctgs_branch_uid]

    # get from and to bus indices on each branch and the branch outaged by each contingency
    branches_fbus = [bus_uid_map[i] for i in branches_fbus_uid]
    branches_tbus = [bus_uid_map[i] for i in branches_tbus_uid]
    ctgs_branch_fbus = [bus_uid_map[i] for i in ctgs_branch_fbus_uid]
    ctgs_branch_tbus = [bus_uid_map[i] for i in ctgs_branch_tbus_uid]

    # get the bus pair (i.e. from and to, listed in natural order) of each branch
    branches_pair = [
        (branches_fbus[i], branches_tbus[i]) # ordered pair (f,t) if f < t
        if (branches_fbus[i] < branches_tbus[i])
        else (branches_tbus[i], branches_fbus[i]) # ordered pair (t,f) if t < t
        for i in range(num_branches)] # note f = t is not possible
    branches_pair_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in branches_pair]
    pairs = list(set(branches_pair))
    num_pairs = len(pairs)
    pairs_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in pairs]

    # get the bus pair of each contingency
    ctgs_pair = [branches_pair[i] for i in ctgs_branch]
    ctgs_pair_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in ctgs_pair]
    
    # form graph
    # use only one edge for each bus pair,
    # even if there are multiple branches spanning that pair
    # this will not affect connectedness
    # and as for bridges, just remove the bridges that correspond to pairs spanned by more than one branch
    graph = networkx.Graph()
    graph.add_nodes_from(buses_uid)
    graph.add_edges_from(pairs_uid)

    # check connectedness under the base case
    connected_components = list(networkx.connected_components(graph))
    if len(connected_components) != 1:
        msg += "fails connectedness of graph on all buses and base case in service AC branches. num connected components: {}, expected: 1, components: {}".format(
            len(connected_components), connected_components)

    # what branches span each pair?
    pair_branches = {i:[] for i in pairs}
    for i in range(num_branches):
        j = branches_pair[i]
        pair_branches[j].append(i)
    pair_num_branches = {i:len(pair_branches[i]) for i in pairs}
    #print('pair_num_branches: {}'.format(pair_num_branches))

    # what contingencies outage a branch spanning each pair?
    pair_ctgs = {i:[] for i in pairs}
    for i in range(num_ctgs):
        j = ctgs_pair[i]
        pair_ctgs[j].append(i)

    # check connectedness under each contingency
    bridges_uid = list(networkx.bridges(graph))
    bridges = [(bus_uid_map[i[0]], bus_uid_map[i[1]]) for i in bridges_uid]
    #print('bridges: {}'.format(bridges))
    num_bridges = len(bridges)
    bridges_one_branch = [i for i in bridges if pair_num_branches[i] == 1]
    #print('bridges spanned by one branch: {}'.format(bridges_one_branch))
    num_bridges_one_branch = len(bridges_one_branch)
    #bridges_one_branch_ctgs = [pair_ctgs[i] for i in bridges_one_branch]
    #bridges_one_branch_at_least_one_ctg = [i for i in bridges_one_branch if len(bridges_one_branch_ctgs[i]) > 0]
    disconnecting_ctgs = [j for i in bridges_one_branch for j in pair_ctgs[i]]
    disconnecting_ctgs_uid = [ctgs_uid[i] for i in disconnecting_ctgs]
    if len(disconnecting_ctgs_uid) > 0:
        msg += "fails connectedness of graph on all buses and post-contingency in service AC branches. failing contingencies are those outaging a branch that is a bridge in the graph. num failing contingencies: {}, expected: 0, failing contingencies uid: {}".format(
            len(disconnecting_ctgs_uid), disconnecting_ctgs_uid)

    # report the errors
    if len(msg) > 0:
        raise ModelError(msg)

def get_buses_branches_ctgs_on_in_service_ac_network(data):
    '''
    returns (bu,br,ct) where
    bu is the set of all buses
    br is the set of in service AC branches
    ct is the set of contingencies outaging an in service AC branch
    '''

    buses = data.network.bus
    ac_lines = data.network.ac_line
    in_service_ac_lines = [i for i in ac_lines if i.initial_status.on_status > 0]
    other_ac_lines = [i for i in ac_lines if not (i.initial_status.on_status > 0)]
    transformers = data.network.two_winding_transformer
    in_service_transformers = [i for i in transformers if i.initial_status.on_status > 0]
    other_transformers = [i for i in transformers if not (i.initial_status.on_status > 0)]
    in_service_ac_branches = in_service_ac_lines + in_service_transformers
    num_in_service_ac_branches = len(in_service_ac_branches)
    dc_lines = data.network.dc_line
    other_branches = other_ac_lines + other_transformers + dc_lines
    ctgs = data.reliability.contingency
    ordered_branches = in_service_ac_branches + other_branches
    num_branches = len(ordered_branches)
    ordered_branches_uid = [i.uid for i in ordered_branches]
    ordered_branches_uid_map = {ordered_branches_uid[i]: i for i in range(num_branches)}
    in_service_ac_ctgs = [i for i in ctgs if ordered_branches_uid_map[i.components[0]] < num_in_service_ac_branches]
    return buses, in_service_ac_branches, in_service_ac_ctgs







# def check_connectedness(self):
    
#     buses_id = [r.i for r in self.raw.get_buses()]
#     buses_id = sorted(buses_id)
#     num_buses = len(buses_id)
#     lines_id = [(r.i, r.j, r.ckt) for r in self.raw.get_nontransformer_branches() if r.st == 1] # todo check status
#     num_lines = len(lines_id)
#     xfmrs_id = [(r.i, r.j, r.ckt) for r in self.raw.get_transformers() if r.stat == 1] # todo check status
#     num_xfmrs = len(xfmrs_id)
#     branches_id = lines_id + xfmrs_id
#     num_branches = len(branches_id)
#     branches_id = [(r if r[0] < r[1] else (r[1], r[0], r[2])) for r in branches_id]
#     branches_id = sorted(list(set(branches_id)))
#     ctg_branches_id = [(e.i, e.j, e.ckt) for r in self.con.get_contingencies() for e in r.branch_out_events]
#     ctg_branches_id = [(r if r[0] < r[1] else (r[1], r[0], r[2])) for r in ctg_branches_id]
#     ctg_branches_id = sorted(list(set(ctg_branches_id)))
#     ctg_branches_id_ctg_label_map = {
#         k:[]
#         for k in ctg_branches_id}
#     for r in self.con.get_contingencies():
#         for e in r.branch_out_events:
#             if e.i < e.j:
#                 k = (e.i, e.j, e.ckt)
#             else:
#                 k = (e.j, e.i, e.ckt)
#             ctg_branches_id_ctg_label_map[k].append(r.label)
#     branch_bus_pairs = sorted(list(set([(r[0], r[1]) for r in branches_id])))
#     bus_pair_branches_map = {
#         r:[]
#         for r in branch_bus_pairs}
#     for r in branches_id:
#         bus_pair_branches_map[(r[0], r[1])].append(r)
#     bus_pair_num_branches_map = {
#         k:len(v)
#         for k, v in bus_pair_branches_map.items()}
#     bus_nodes_id = [
#         'node_bus_{}'.format(r) for r in buses_id]
#     extra_nodes_id = [
#         'node_extra_{}_{}_{}'.format(r[0], r[1], r[2])
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     branch_edges = [
#         ('node_bus_{}'.format(r[0]), 'node_bus_{}'.format(r[1]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] == 1
#         for r in bus_pair_branches_map[k]]
#     branch_edge_branch_map = {
#         ('node_bus_{}'.format(r[0]), 'node_bus_{}'.format(r[1])):r
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] == 1
#         for r in bus_pair_branches_map[k]}            
#     extra_edges_1 = [
#         ('node_bus_{}'.format(r[0]), 'node_extra_{}_{}_{}'.format(r[0], r[1], r[2]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     extra_edges_2 = [
#         ('node_bus_{}'.format(r[1]), 'node_extra_{}_{}_{}'.format(r[0], r[1], r[2]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     nodes = bus_nodes_id + extra_nodes_id
#     edges = branch_edges + extra_edges_1 + extra_edges_2
#     graph = nx.Graph()
#     graph.add_nodes_from(nodes)
#     graph.add_edges_from(edges)
#     connected_components = list(nx.connected_components(graph))
#     #connected_components = [set(k) for k in connected_components] # todo get only the bus nodes and take only their id number
#     num_connected_components = len(connected_components)

#     # print alert

#     bridges = list(nx.bridges(graph))
#     num_bridges = len(bridges)
#     bridges = sorted(list(set(branch_edges).intersection(set(bridges))))
#     # assert len(bridges) == num_bridges i.e. all bridges are branch edges, i.e. not extra edges. extra edges should be elements of cycles
#     bridges = [branch_edge_branch_map[r] for r in bridges]
#     ctg_bridges = sorted(list(set(bridges).intersection(set(ctg_branches_id))))
#     num_ctg_bridges = len(ctg_bridges)

#     # print alert












        # on_status_ub
        # on_status_lb
        # p_lb
        # p_ub
        # q_lb
        # q_ub
        # cost
        # p_reg_res_up_cost
        # p_reg_res_down_cost
        # p_syn_res_cost
        # p_nsyn_res_cost
        # p_ramp_res_up_online_cost
        # p_ramp_res_down_online_cost
        # p_ramp_res_down_offline_cost
        # p_ramp_res_up_offline_cost
        # q_res_up_cost
        # q_res_down_cost





