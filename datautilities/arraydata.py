import numpy

class InputData(object):

    def __init__(self):
        
        pass
    
    def set_from_data_model(self, data):

        #print(data.network.__dir__())
        self.num_bus = len(data.network.bus)
        self.num_acl = len(data.network.ac_line)
        self.num_dcl = len(data.network.dc_line)
        self.num_xfr = len(data.network.two_winding_transformer)
        self.num_sh = len(data.network.shunt)
        self.num_sd = len(data.network.simple_dispatchable_device)
        self.num_pd = len([i for i in data.network.simple_dispatchable_device if i.device_type == 'producer'])
        self.num_cd = len([i for i in data.network.simple_dispatchable_device if i.device_type == 'consumer'])
        self.num_prz = len(data.network.active_zonal_reserve)
        self.num_qrz = len(data.network.reactive_zonal_reserve)
        self.num_t = len(data.time_series_input.general.interval_duration)
        self.num_k = len(data.reliability.contingency)

        # establish an order of elements in each type
        self.bus_uid = numpy.array([i.uid for i in data.network.bus])
        self.acl_uid = numpy.array([i.uid for i in data.network.ac_line])
        self.dcl_uid = numpy.array([i.uid for i in data.network.dc_line])
        self.xfr_uid = numpy.array([i.uid for i in data.network.two_winding_transformer])
        self.sh_uid = numpy.array([i.uid for i in data.network.shunt])
        self.sd_uid = numpy.array([i.uid for i in data.network.simple_dispatchable_device])
        self.prz_uid = numpy.array([i.uid for i in data.network.active_zonal_reserve])
        self.qrz_uid = numpy.array([i.uid for i in data.network.reactive_zonal_reserve])
        self.k_uid = numpy.array([i.uid for i in data.reliability.contingency])
        self.all_uid = numpy.concatenate((self.bus_uid,
            self.acl_uid,
            self.dcl_uid,
            self.xfr_uid,
            self.sh_uid,
            self.sd_uid,
            self.prz_uid,
            self.qrz_uid,
            self.k_uid))

        self.num_all = self.all_uid.size

        # ranges
        self.t_num = numpy.array(list(range(self.num_t)))

        self.bus_map = {self.bus_uid[i]:i for i in range(self.num_bus)}
        self.acl_map = {self.acl_uid[i]:i for i in range(self.num_acl)}
        self.dcl_map = {self.dcl_uid[i]:i for i in range(self.num_dcl)}
        self.xfr_map = {self.xfr_uid[i]:i for i in range(self.num_xfr)}
        self.sh_map = {self.sh_uid[i]:i for i in range(self.num_sh)}
        self.sd_map = {self.sd_uid[i]:i for i in range(self.num_sd)}
        self.prz_map = {self.prz_uid[i]:i for i in range(self.num_prz)}
        self.qrz_map = {self.qrz_uid[i]:i for i in range(self.num_qrz)}
        self.k_map = {self.k_uid[i]:i for i in range(self.num_k)}
        self.all_map = {self.all_uid[i]:i for i in range(self.num_all)}
        
        start = 0
        end = 0

        end += self.num_bus
        self.all_is_bus = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_bus

        end += self.num_acl
        self.all_is_acl = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_acl

        end += self.num_dcl
        self.all_is_dcl = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_dcl

        end += self.num_xfr
        self.all_is_xfr = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_xfr

        end += self.num_sh
        self.all_is_sh = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_sh

        end += self.num_sd
        self.all_is_sd = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_sd

        end += self.num_prz
        self.all_is_prz = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_prz

        end += self.num_qrz
        self.all_is_qrz = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_qrz

        end += self.num_k
        self.all_is_k = numpy.array([(start <= i and i < end) for i in range(self.num_all)])
        start += self.num_k
        
        self.t_duration = numpy.array(data.time_series_input.general.interval_duration)

        self.k_out_device_uid = numpy.array([k.components[0] for k in data.reliability.contingency])
        self.k_out_device = numpy.array([self.all_map[self.k_out_device_uid[i]] for i in range(self.num_k)])
        self.k_out_is_acl = numpy.array([self.all_is_acl[self.k_out_device[i]] for i in range(self.num_k)])
        self.k_out_is_dcl = numpy.array([self.all_is_dcl[self.k_out_device[i]] for i in range(self.num_k)])
        self.k_out_is_xfr = numpy.array([self.all_is_xfr[self.k_out_device[i]] for i in range(self.num_k)])
        self.k_out_acl = numpy.array([self.acl_map[self.k_out_device_uid[i]] if self.k_out_is_acl[i] else 0 for i in range(self.num_k)])
        self.k_out_dcl = numpy.array([self.dcl_map[self.k_out_device_uid[i]] if self.k_out_is_dcl[i] else 0 for i in range(self.num_k)])
        self.k_out_xfr = numpy.array([self.xfr_map[self.k_out_device_uid[i]] if self.k_out_is_xfr[i] else 0 for i in range(self.num_k)])

        #summary['violation costs'] = network.violation_cost
        # ts_sd = time_series_input.simple_dispatchable_device
        # ts_prz = time_series_input.active_zonal_reserve
        # ts_qrz = time_series_input.reactive_zonal_reserve

        self.set_sd_t_from_data_model(data)

    def set_sd_t_from_data_model(self, data):

        data_map = {x.uid:x for x in data.time_series_input.simple_dispatchable_device}
        self.sd_t_u_on_max = numpy.array([data_map[i].on_status_ub for i in self.sd_uid])
        self.sd_t_u_on_min = numpy.array([data_map[i].on_status_lb for i in self.sd_uid])

class OutputData(object):

    def __init__(self):

        pass

    def set_from_data_model(self, input_data, output_data_model):
        
        self.set_bus_t_from_data_model(input_data, output_data_model)
        self.set_sh_t_from_data_model(input_data, output_data_model)
        self.set_sd_t_from_data_model(input_data, output_data_model)
        self.set_acl_t_from_data_model(input_data, output_data_model)
        self.set_dcl_t_from_data_model(input_data, output_data_model)
        self.set_xfr_t_from_data_model(input_data, output_data_model)

    def set_bus_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.bus}
        self.bus_t_v = numpy.array([data_map[i].vm for i in input_data.bus_uid])
        self.bus_t_theta = numpy.array([data_map[i].va for i in input_data.bus_uid])

    def set_sh_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.shunt}
        self.sh_t_u_st = numpy.array([data_map[i].step for i in input_data.sh_uid])

    def set_sd_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.simple_dispatchable_device}
        self.sd_t_u_on = numpy.array([data_map[i].on_status for i in input_data.sd_uid])
        self.sd_t_p_on = numpy.array([data_map[i].p_on for i in input_data.sd_uid])
        self.sd_t_q = numpy.array([data_map[i].q for i in input_data.sd_uid])
        self.sd_t_p_rgu = numpy.array([data_map[i].p_reg_res_up for i in input_data.sd_uid])
        self.sd_t_p_rgd = numpy.array([data_map[i].p_reg_res_down for i in input_data.sd_uid])
        self.sd_t_p_scr = numpy.array([data_map[i].p_syn_res for i in input_data.sd_uid])
        self.sd_t_p_nsc = numpy.array([data_map[i].p_nsyn_res for i in input_data.sd_uid])
        self.sd_t_p_rru_on = numpy.array([data_map[i].p_ramp_res_up_online for i in input_data.sd_uid])
        self.sd_t_p_rrd_on = numpy.array([data_map[i].p_ramp_res_down_online for i in input_data.sd_uid])
        self.sd_t_p_rru_off = numpy.array([data_map[i].p_ramp_res_up_offline for i in input_data.sd_uid])
        self.sd_t_p_rrd_off = numpy.array([data_map[i].p_ramp_res_down_offline for i in input_data.sd_uid])
        self.sd_t_q_qru = numpy.array([data_map[i].q_res_up for i in input_data.sd_uid])
        self.sd_t_q_qrd = numpy.array([data_map[i].q_res_down for i in input_data.sd_uid])

    def set_acl_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.ac_line}
        self.acl_t_u_on = numpy.array([data_map[i].on_status for i in input_data.acl_uid])

    def set_dcl_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.dc_line}
        self.dcl_t_p = numpy.array([data_map[i].pdc_fr for i in input_data.dcl_uid])
        self.dcl_t_q_fr = numpy.array([data_map[i].qdc_fr for i in input_data.dcl_uid])
        self.dcl_t_q_to = numpy.array([data_map[i].qdc_to for i in input_data.dcl_uid])

    def set_xfr_t_from_data_model(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.two_winding_transformer}
        self.xfr_t_u_on = numpy.array([data_map[i].on_status for i in input_data.xfr_uid])
        self.xfr_t_tau = numpy.array([data_map[i].tm for i in input_data.xfr_uid])
        self.xfr_t_phi = numpy.array([data_map[i].ta for i in input_data.xfr_uid])

