'''

'''

import networkx
from pydantic.error_wrappers import ValidationError
from datamodel.input.data import InputDataFile
from datautilities import utils
from datautilities.errors import ModelError, GitError
import traceback
import pprint

def write(file_name, mode, text):

    with open(file_name, mode) as f:
        f.write(text)

def check(data_file, summary_file, data_errors_file, ignored_errors_file):

    # open files
    for fn in [summary_file, data_errors_file, ignored_errors_file]:
        with open(fn, 'w') as f:
            pass

    # data file
    with open(summary_file, 'a') as f:
        f.write('problem data file: {}'.format(data_file))

    # git info
    try:
        git_info = utils.get_git_info_all()
        with open(summary_file, 'a') as f:
            f.write('git info: {}'.format(git_info))
    except GitError:
        with open(summary_file, 'a') as f:
            f.write('git info error ignored')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())
    except Exception:
        with open(summary_file, 'a') as f:
            f.write('git info error ignored')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())

    # read data
    try:
        data_model = InputDataFile.load(data_file)
    except ValidationError as e:
        with open(summary_file, 'a') as f:
            f.write('data read error - pydantic validation')
        with open(data_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e

    # independent data model checks
    try:
        model_checks(data_model)
    except ModelError as e:
        with open(summary_file, 'a') as f:
            f.write('model error - independent checks')
        with open(data_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e

    # connectedness check
    try:
        connected(data_model)
    except ModelError as e:
        with open(summary_file, 'a') as f:
            f.write('model error - connectedness')
        with open(data_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e

    # summary
    summary = get_summary(data_model)
    with open(summary_file, 'a') as f:
        pp = pprint.PrettyPrinter()
        f.write('data summary: {}'.format(pp.pprint(summary)))

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

def model_checks(data):

    checks = [
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
    for c in checks:
        try:
            c(data)
        except ModelError as e:
            errors.append(e)
    if len(errors) > 0:
        msg = (
            'validation.model_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(e) for e in errors]))
        raise ModelError(msg)        

def ts_uids_not_repeated(data):

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

def network_and_reliability_uids_not_repeated(data):
    
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

def ctg_dvc_uids_in_domain(data):

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

def bus_prz_uids_in_domain(data):

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

def bus_qrz_uids_in_domain(data):

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

def shunt_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_shunt = len(data.network.shunt)
    shunt_idx_bus_not_in_domain = [
        i for i in range(num_shunt)
        if not (data.network.shunt[i].bus in domain)]
    shunt_bus_not_in_domain = [
        (i, data.network.shunt[i].uid, data.network.shunt[i].bus)
        for i in shunt_idx_bus_not_in_domain]
    if len(shunt_idx_bus_not_in_domain) > 0:
        msg = "fails shunt bus in buses. failing shunts (index, uid, bus uid): {}".format(
            shunt_bus_not_in_domain)
        raise ModelError(msg)

def sd_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_idx_bus_not_in_domain = [
        i for i in range(num_sd)
        if not (data.network.simple_dispatchable_device[i].bus in domain)]
    sd_bus_not_in_domain = [
        (i, data.network.simple_dispatchable_device[i].uid, data.network.simple_dispatchable_device[i].bus)
        for i in sd_idx_bus_not_in_domain]
    if len(sd_idx_bus_not_in_domain) > 0:
        msg = "fails simple dispatchable device bus in buses. failing devices (index, uid, bus uid): {}".format(
            sd_bus_not_in_domain)
        raise ModelError(msg)

def sd_type_in_domain(data):

    domain = set(['producer', 'consumer'])
    num_sd = len(data.network.simple_dispatchable_device)
    sd_idx_type_not_in_domain = [
        i for i in range(num_sd)
        if not (data.network.simple_dispatchable_device[i].device_type in domain)]
    sd_type_not_in_domain = [
        (i, data.network.simple_dispatchable_device[i].uid, data.network.simple_dispatchable_device[i].device_type)
        for i in sd_idx_type_not_in_domain]
    if len(sd_idx_type_not_in_domain) > 0:
        msg = "fails simple dispatchable device type in domain. domain: {}, failing devices (index, uid, type): {}".format(domain, sd_type_not_in_domain)
        raise ModelError(msg)

def acl_fr_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.ac_line)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.ac_line[i].fr_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.ac_line[i].uid, data.network.ac_line[i].fr_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails ac line from bus in buses. failing devices (index, uid, from bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def acl_to_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.ac_line)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.ac_line[i].to_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.ac_line[i].uid, data.network.ac_line[i].to_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails ac line to bus in buses. failing devices (index, uid, to bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def xfr_fr_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.two_winding_transformer)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.two_winding_transformer[i].fr_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.two_winding_transformer[i].uid, data.network.two_winding_transformer[i].fr_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails transformer from bus in buses. failing devices (index, uid, from bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def xfr_to_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.two_winding_transformer)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.two_winding_transformer[i].to_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.two_winding_transformer[i].uid, data.network.two_winding_transformer[i].to_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails transformer to bus in buses. failing devices (index, uid, to bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def dcl_fr_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.dc_line)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.dc_line[i].fr_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.dc_line[i].uid, data.network.dc_line[i].fr_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails dc line from bus in buses. failing devices (index, uid, from bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def dcl_to_bus_uids_in_domain(data):
    
    domain = data.network.get_bus_uids()
    domain = set(domain)
    num_dvc = len(data.network.dc_line)
    dvc_idx_bus_not_in_domain = [
        i for i in range(num_dvc)
        if not (data.network.dc_line[i].to_bus in domain)]
    dvc_bus_not_in_domain = [
        (i, data.network.dc_line[i].uid, data.network.dc_line[i].to_bus)
        for i in dvc_idx_bus_not_in_domain]
    if len(dvc_idx_bus_not_in_domain) > 0:
        msg = "fails dc line to bus in buses. failing devices (index, uid, to bus uid): {}".format(
            dvc_bus_not_in_domain)
        raise ModelError(msg)

def ts_sd_uids_in_domain(data):
    
    network_num = len(data.network.simple_dispatchable_device)
    ts_num = len(data.time_series_input.simple_dispatchable_device)
    network_uids = [data.network.simple_dispatchable_device[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.simple_dispatchable_device[i].uid for i in range(ts_num)]
    idx_in_ts_not_in_network = [i for i in range(ts_num) if ts_uids[i] not in network_uids]
    idx_uid_in_ts_not_in_network = [(i, ts_uids[i]) for i in idx_in_ts_not_in_network]
    if len(idx_in_ts_not_in_network) > 0:
        msg = "fails time_series_input simple_dispatchable_device uids in domain. failing devices (index, uid): {}".format(
            idx_uid_in_ts_not_in_network)
        raise ModelError(msg)

def ts_sd_uids_cover_domain(data):
    
    network_num = len(data.network.simple_dispatchable_device)
    ts_num = len(data.time_series_input.simple_dispatchable_device)
    network_uids = [data.network.simple_dispatchable_device[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.simple_dispatchable_device[i].uid for i in range(ts_num)]
    idx_in_network_not_in_ts = [i for i in range(network_num) if network_uids[i] not in ts_uids]
    idx_uid_in_network_not_in_ts = [(i, network_uids[i]) for i in idx_in_network_not_in_ts]
    if len(idx_in_network_not_in_ts) > 0:
        msg = "fails time_series_input simple_dispatchable_device uids cover domain. failing devices (index, uid): {}".format(
            idx_uid_in_network_not_in_ts)
        raise ModelError(msg)

def ts_prz_uids_in_domain(data):
    
    network_num = len(data.network.active_zonal_reserve)
    ts_num = len(data.time_series_input.active_zonal_reserve)
    network_uids = [data.network.active_zonal_reserve[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.active_zonal_reserve[i].uid for i in range(ts_num)]
    idx_in_ts_not_in_network = [i for i in range(ts_num) if ts_uids[i] not in network_uids]
    idx_uid_in_ts_not_in_network = [(i, ts_uids[i]) for i in idx_in_ts_not_in_network]
    if len(idx_in_ts_not_in_network) > 0:
        msg = "fails time_series_input active_zonal_reserve uids in domain. failing devices (index, uid): {}".format(
            idx_uid_in_ts_not_in_network)
        raise ModelError(msg)

def ts_prz_uids_cover_domain(data):
    
    network_num = len(data.network.active_zonal_reserve)
    ts_num = len(data.time_series_input.active_zonal_reserve)
    network_uids = [data.network.active_zonal_reserve[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.active_zonal_reserve[i].uid for i in range(ts_num)]
    idx_in_network_not_in_ts = [i for i in range(network_num) if network_uids[i] not in ts_uids]
    idx_uid_in_network_not_in_ts = [(i, network_uids[i]) for i in idx_in_network_not_in_ts]
    if len(idx_in_network_not_in_ts) > 0:
        msg = "fails time_series_input active_zonal_reserve uids cover domain. failing devices (index, uid): {}".format(
            idx_uid_in_network_not_in_ts)
        raise ModelError(msg)

def ts_qrz_uids_in_domain(data):
    
    network_num = len(data.network.reactive_zonal_reserve)
    ts_num = len(data.time_series_input.reactive_zonal_reserve)
    network_uids = [data.network.reactive_zonal_reserve[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.reactive_zonal_reserve[i].uid for i in range(ts_num)]
    idx_in_ts_not_in_network = [i for i in range(ts_num) if ts_uids[i] not in network_uids]
    idx_uid_in_ts_not_in_network = [(i, ts_uids[i]) for i in idx_in_ts_not_in_network]
    if len(idx_in_ts_not_in_network) > 0:
        msg = "fails time_series_input reactive_zonal_reserve uids in domain. failing devices (index, uid): {}".format(
            idx_uid_in_ts_not_in_network)
        raise ModelError(msg)

def ts_qrz_uids_cover_domain(data):
    
    network_num = len(data.network.reactive_zonal_reserve)
    ts_num = len(data.time_series_input.reactive_zonal_reserve)
    network_uids = [data.network.reactive_zonal_reserve[i].uid for i in range(network_num)]
    ts_uids = [data.time_series_input.reactive_zonal_reserve[i].uid for i in range(ts_num)]
    idx_in_network_not_in_ts = [i for i in range(network_num) if network_uids[i] not in ts_uids]
    idx_uid_in_network_not_in_ts = [(i, network_uids[i]) for i in idx_in_network_not_in_ts]
    if len(idx_in_network_not_in_ts) > 0:
        msg = "fails time_series_input reactive_zonal_reserve uids cover domain. failing devices (index, uid): {}".format(
            idx_uid_in_network_not_in_ts)
        raise ModelError(msg)

def ts_sd_on_status_ub_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.on_status_ub) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(on_status_ub) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(on_status_ub)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_on_status_lb_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.on_status_lb) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(on_status_lb) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(on_status_lb)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_lb_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_lb) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_lb) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_lb)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_ub_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_ub) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_ub) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_ub)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_q_lb_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.q_lb) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(q_lb) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(q_lb)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_q_ub_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.q_ub) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(q_ub) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(q_ub)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_reg_res_up_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_reg_res_up_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_reg_res_up_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_reg_res_up_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_reg_res_down_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_reg_res_down_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_reg_res_down_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_reg_res_down_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_syn_res_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_syn_res_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_syn_res_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_syn_res_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_nsyn_res_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_nsyn_res_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_nsyn_res_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_nsyn_res_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_ramp_res_up_online_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_ramp_res_up_online_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_ramp_res_up_online_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_ramp_res_up_online_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_ramp_res_down_online_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_ramp_res_down_online_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_ramp_res_down_online_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_ramp_res_down_online_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_ramp_res_down_offline_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_ramp_res_down_offline_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_ramp_res_down_offline_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_ramp_res_down_offline_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_p_ramp_res_up_offline_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.p_ramp_res_up_offline_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(p_ramp_res_up_offline_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(p_ramp_res_up_offline_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_q_res_up_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.q_res_up_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(q_res_up_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(q_res_up_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_q_res_down_cost_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.q_res_down_cost) for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [
        (i, data.time_series_input.simple_dispatchable_device[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device len(q_res_down_cost) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(q_res_down_cost)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_prz_ramping_reserve_up_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.RAMPING_RESERVE_UP) for c in data.time_series_input.active_zonal_reserve]
    idx_err = [
        (i, data.time_series_input.active_zonal_reserve[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input active_zonal_reserve len(RAMPING_RESERVE_UP) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(RAMPING_RESERVE_UP)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_prz_ramping_reserve_down_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.RAMPING_RESERVE_DOWN) for c in data.time_series_input.active_zonal_reserve]
    idx_err = [
        (i, data.time_series_input.active_zonal_reserve[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input active_zonal_reserve len(RAMPING_RESERVE_DOWN) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(RAMPING_RESERVE_DOWN)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_qrz_react_up_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.REACT_UP) for c in data.time_series_input.reactive_zonal_reserve]
    idx_err = [
        (i, data.time_series_input.reactive_zonal_reserve[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input reactive_zonal_reserve len(REACT_UP) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(REACT_UP)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_qrz_react_down_len_eq_num_t(data):
    
    num_t = len(data.time_series_input.general.interval_duration)
    component_lens = [len(c.REACT_DOWN) for c in data.time_series_input.reactive_zonal_reserve]
    idx_err = [
        (i, data.time_series_input.reactive_zonal_reserve[i].uid, component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input reactive_zonal_reserve len(REACT_DOWN) == len(intervals). len(intervals): {}. failing devices (idx, uid, len(REACT_DOWN)): {}".format(
            num_t, idx_err)
        raise ModelError(msg)

def ts_sd_on_status_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.on_status_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.on_status_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device on_status_lb <= on_status_ub. failures (device index, device uid, interval index, on_status_lb, on_status_ub): {}".format(idx_err)
        raise ModelError(msg)

def ts_sd_p_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.p_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.p_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device p_lb <= p_ub. failures (device index, device uid, interval index, p_lb, p_ub): {}".format(idx_err)
        raise ModelError(msg)

def ts_sd_q_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.q_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.q_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device q_lb <= q_ub. failures (device index, device uid, interval index, q_lb, q_ub): {}".format(idx_err)
        raise ModelError(msg)

def connected(data):

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





