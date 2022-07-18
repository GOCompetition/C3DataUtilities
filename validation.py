'''

'''

def all_checks(data):

    checks = [
        uids_not_repeated,
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

def uids_not_repeated(data):
    
    uids = data.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness. repeated uids (uid, number of occurrences): {}".format(
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
