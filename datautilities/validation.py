'''

'''

import networkx

def all_checks(data):

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
        connected,
        ]
    errors = []
    for c in checks:
        try:
            c(data)
        except Exception as e:
            errors.append(e)
    if len(errors) > 0:
        msg = (
            'validation.all_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(e) for e in errors]))
        raise Exception(msg)        

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

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
        raise ValueError(msg)

def ts_sd_on_status_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.on_status_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.on_status_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device on_status_lb <= on_status_ub. failures (device index, device uid, interval index, on_status_lb, on_status_ub): {}".format(idx_err)
        raise ValueError(msg)

def ts_sd_p_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.p_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.p_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device p_lb <= p_ub. failures (device index, device uid, interval index, p_lb, p_ub): {}".format(idx_err)
        raise ValueError(msg)

def ts_sd_q_lb_le_ub(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.q_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.q_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device q_lb <= q_ub. failures (device index, device uid, interval index, q_lb, q_ub): {}".format(idx_err)
        raise ValueError(msg)

def connected(data):

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
        msg = "fails connectedness of graph on all buses and base case in service AC branches. num connected components: {}, expected: 1, components: {}".format(
            len(connected_components), connected_components)
        raise ValueError(msg)

    # # what branches span each pair?
    pair_branches = {i:[] for i in pairs}
    # for i in range(num_branches):
    #     j = branches_pair[i]
    #     pair_branches[j].append(i)
    # pair_num_branches = [len(i) for i in pair_branches
    #     pair_branches

    # bus_pairs = 

    # buses_id = [i.uid for i in data.network.bus]
    # ac
    # branches_id = [i.uid for i in data.network.ac_line

    # return graph




    # # check connectedness under each contingency
    # bridges = list(networkx.bridges(graph))
    # print('bridges: {}'.format(bridges))
    # # num_bridges = len(bridges)
    # # bridges = sorted(list(set(branch_edges).intersection(set(bridges))))
    # # # assert len(bridges) == num_bridges i.e. all bridges are branch edges, i.e. not extra edges. extra edges should be elements of cycles
    # # bridges = [branch_edge_branch_map[r] for r in bridges]
    # disconnecting_ctgs_uid = [] # todo
    # if len(disconnecting_ctgs_uid) > 0:
    #     msg = "fails connectedness of graph on all buses and post-contingency in service AC branches. failing contingencies uid: {}".format(
    #         disconnecting_ctgs_uid)
    #     raise ValueError(msg)

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





