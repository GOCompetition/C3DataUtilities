import numpy

class InputData(object):

    def __init__(self):
        
        pass
    
    def set_from_data_model(self, data):

        self.set_structure(data)
        self.set_scalars(data)
        self.set_bus(data)
        self.set_sh(data)
        self.set_sd(data)
        self.set_acl(data)
        self.set_dcl(data)
        self.set_xfr(data)
        self.set_prz(data)
        self.set_qrz(data)
        self.set_t(data)
        self.set_k(data)
        self.set_sd_t(data)
        self.set_sd_t_cost(data)
        self.set_prz_t(data)
        self.set_qrz_t(data)

    def set_structure(self, data):

        self.set_num(data)
        self.set_uid(data)
        self.num_all = self.all_uid.size
        self.set_range(data)
        self.set_map(data)
        self.set_type_indicator(data)

    def set_num(self, data):

        self.num_bus = len(data.network.bus)
        self.num_acl = len(data.network.ac_line)
        self.num_dcl = len(data.network.dc_line)
        self.num_xfr = len(data.network.two_winding_transformer)
        self.num_sh = len(data.network.shunt)
        self.num_sd = len(data.network.simple_dispatchable_device)
        self.num_pr = len([i for i in data.network.simple_dispatchable_device if i.device_type == 'producer'])
        self.num_cs = len([i for i in data.network.simple_dispatchable_device if i.device_type == 'consumer'])
        self.num_prz = len(data.network.active_zonal_reserve)
        self.num_qrz = len(data.network.reactive_zonal_reserve)
        self.num_t = len(data.time_series_input.general.interval_duration)
        self.num_k = len(data.reliability.contingency)

    def set_uid(self, data):

        # establish an order of elements in each type
        self.bus_uid = numpy.array([i.uid for i in data.network.bus], dtype=str)
        self.acl_uid = numpy.array([i.uid for i in data.network.ac_line], dtype=str)
        self.dcl_uid = numpy.array([i.uid for i in data.network.dc_line], dtype=str)
        self.xfr_uid = numpy.array([i.uid for i in data.network.two_winding_transformer], dtype=str)
        self.sh_uid = numpy.array([i.uid for i in data.network.shunt], dtype=str)
        self.sd_uid = numpy.array([i.uid for i in data.network.simple_dispatchable_device], dtype=str)
        self.pr_uid = numpy.array(
            [i.uid for i in data.network.simple_dispatchable_device if i.device_type == 'producer'], dtype=str)
        self.cs_uid = numpy.array(
            [i.uid for i in data.network.simple_dispatchable_device if i.device_type == 'consumer'], dtype=str)
        self.prz_uid = numpy.array([i.uid for i in data.network.active_zonal_reserve], dtype=str)
        self.qrz_uid = numpy.array([i.uid for i in data.network.reactive_zonal_reserve], dtype=str)
        self.k_uid = numpy.array([i.uid for i in data.reliability.contingency], dtype=str)
        self.all_uid = numpy.concatenate((self.bus_uid,
            self.acl_uid,
            self.dcl_uid,
            self.xfr_uid,
            self.sh_uid,
            self.sd_uid,
            self.prz_uid,
            self.qrz_uid,
            self.k_uid))

    def set_range(self, data):

        # ranges
        self.t_num = numpy.array(list(range(self.num_t)), dtype=int)

    def set_map(self, data):

        # maps
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

    def set_type_indicator(self, data):

        # boolean type indicators
        
        start = 0
        end = 0

        end += self.num_bus
        self.all_is_bus = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_bus

        end += self.num_acl
        self.all_is_acl = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_acl

        end += self.num_dcl
        self.all_is_dcl = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_dcl

        end += self.num_xfr
        self.all_is_xfr = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_xfr

        end += self.num_sh
        self.all_is_sh = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_sh

        end += self.num_sd
        self.all_is_sd = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_sd

        end += self.num_prz
        self.all_is_prz = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_prz

        end += self.num_qrz
        self.all_is_qrz = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_qrz

        end += self.num_k
        self.all_is_k = numpy.array([(start <= i and i < end) for i in range(self.num_all)], dtype=bool)
        start += self.num_k

    def set_scalars(self, data):

        self.c_p = float(data.network.violation_cost.p_bus_vio_cost)
        self.c_q = float(data.network.violation_cost.p_bus_vio_cost)
        self.c_s = float(data.network.violation_cost.s_vio_cost)
        self.c_e = 1.0e6 # 1.0e4 USD/MWh = 1.0e6 USD/pu-h # todo read this from data, validate, including preferred value in config, check value > 0, add assumptions to formulation, add symbol and algebra to formulation 

    def set_bus(self, data):

        data_map = {x.uid:x for x in data.network.bus}
        self.bus_v_max = numpy.array([data_map[i].vm_ub for i in self.bus_uid], dtype=float)
        self.bus_v_min = numpy.array([data_map[i].vm_lb for i in self.bus_uid], dtype=float)
        self.bus_v_0 = numpy.array([data_map[i].initial_status.vm for i in self.bus_uid], dtype=float)
        self.bus_theta_0 = numpy.array([data_map[i].initial_status.va for i in self.bus_uid], dtype=float)
        self.bus_num_prz = numpy.array([len(data_map[i].active_reserve_uids) for i in self.bus_uid], dtype=int)
        bus_prz_uid_list = [numpy.array(data_map[i].active_reserve_uids, dtype=str) for i in self.bus_uid]
        self.bus_prz_list = [numpy.array([self.prz_map[j] for j in i], dtype=int) for i in bus_prz_uid_list]
        self.bus_num_qrz = numpy.array([len(data_map[i].reactive_reserve_uids) for i in self.bus_uid], dtype=int)
        bus_qrz_uid_list = [numpy.array(data_map[i].reactive_reserve_uids, dtype=str) for i in self.bus_uid]
        self.bus_qrz_list = [numpy.array([self.qrz_map[j] for j in i], dtype=int) for i in bus_qrz_uid_list]

    def set_sh(self, data):

        data_map = {x.uid:x for x in data.network.shunt}
        sh_bus_uid = numpy.array([data_map[i].bus for i in self.sh_uid], dtype=str)
        self.sh_bus = numpy.array([self.bus_map[i] for i in sh_bus_uid], dtype=int)
        self.sh_g_st = numpy.array([data_map[i].gs for i in self.sh_uid], dtype=float)
        self.sh_b_st = numpy.array([data_map[i].bs for i in self.sh_uid], dtype=float)
        self.sh_u_st_max = numpy.array([data_map[i].step_ub for i in self.sh_uid], dtype=int)
        self.sh_u_st_min = numpy.array([data_map[i].step_lb for i in self.sh_uid], dtype=int)
        self.sh_u_st_0 = numpy.array([data_map[i].initial_status.step for i in self.sh_uid], dtype=int)

    def set_sd(self, data):

        data_map = {x.uid:x for x in data.network.simple_dispatchable_device}
        sd_bus_uid = numpy.array([data_map[i].bus for i in self.sd_uid], dtype=str)
        self.sd_bus = numpy.array([self.bus_map[i] for i in sd_bus_uid], dtype=int)
        self.sd_is_pr = numpy.array([1 if data_map[i].device_type == 'producer' else 0 for i in self.sd_uid], dtype=int)
        self.sd_is_cs = numpy.array([1 if data_map[i].device_type == 'consumer' else 0 for i in self.sd_uid], dtype=int)
        self.pr_sd = numpy.array(
            [i for i in range(self.num_sd) if data_map[self.sd_uid[i]].device_type == 'producer'], dtype=int)
        self.cs_sd = numpy.array(
            [i for i in range(self.num_sd) if data_map[self.sd_uid[i]].device_type == 'consumer'], dtype=int)
        self.sd_c_su = numpy.array([data_map[i].startup_cost for i in self.sd_uid], dtype=float)
        self.sd_c_sd = numpy.array([data_map[i].shutdown_cost for i in self.sd_uid], dtype=float)
        self.sd_c_on = numpy.array([data_map[i].on_cost for i in self.sd_uid], dtype=float)
        self.sd_d_up_min = numpy.array([data_map[i].in_service_time_lb for i in self.sd_uid], dtype=float)
        self.sd_d_dn_min = numpy.array([data_map[i].down_time_lb for i in self.sd_uid], dtype=float)
        self.sd_p_ramp_up_max = numpy.array([data_map[i].p_ramp_up_ub for i in self.sd_uid], dtype=float)
        self.sd_p_ramp_dn_max = numpy.array([data_map[i].p_ramp_down_ub for i in self.sd_uid], dtype=float)
        self.sd_p_startup_ramp_up_max = numpy.array([data_map[i].p_startup_ramp_ub for i in self.sd_uid], dtype=float)
        self.sd_p_shutdown_ramp_dn_max = numpy.array([data_map[i].p_shutdown_ramp_ub for i in self.sd_uid], dtype=float)

        # downtime-dependent startup cost data
        startup_states = {i:sorted(data_map[i].startup_states, key=(lambda x: x[0])) for i in self.sd_uid} # sort startup states so that cost is increasing within each sd
        self.sd_num_startup_state = numpy.array([len(startup_states[i]) for i in self.sd_uid], dtype=int)
        self.sd_startup_state_d_max_list = [numpy.array([s[1] for s in startup_states[i]], dtype=float) for i in self.sd_uid]
        self.sd_startup_state_c_list = [numpy.array([s[0] for s in startup_states[i]], dtype=float) for i in self.sd_uid]
        #self.sd_startup_state_d_max = numpy.array([s[1] for i in self.sd_uid for s in startup_states[i]])
        #self.sd_startup_state_c = numpy.array([s[0] for i in self.sd_uid for s in startup_states[i]])

        # max startups constraint data
        self.sd_num_max_startup_constr = numpy.array([len(data_map[i].startups_ub) for i in self.sd_uid], dtype=int)
        self.sd_max_startup_constr_a_start_list = [
            numpy.array([s[0] for s in data_map[i].startups_ub], dtype=float) for i in self.sd_uid]
        self.sd_max_startup_constr_a_end_list = [
            numpy.array([s[1] for s in data_map[i].startups_ub], dtype=float) for i in self.sd_uid]
        self.sd_max_startup_constr_max_startup_list = [
            numpy.array([s[2] for s in data_map[i].startups_ub], dtype=int) for i in self.sd_uid]
        # self.sd_max_startup_constr_t_start_list = [
        #     numpy.array([ for a in sd_max_startup_constr_a_start_list[i]])
        #     for i in self.sd_uid]

        # max energy constraint data
        self.sd_num_max_energy_constr = numpy.array([len(data_map[i].energy_req_ub) for i in self.sd_uid], dtype=int)
        self.sd_max_energy_constr_a_start_list = [
            numpy.array([s[0] for s in data_map[i].energy_req_ub], dtype=float) for i in self.sd_uid]
        self.sd_max_energy_constr_a_end_list = [
            numpy.array([s[1] for s in data_map[i].energy_req_ub], dtype=float) for i in self.sd_uid]
        self.sd_max_energy_constr_max_energy_list = [
            numpy.array([s[2] for s in data_map[i].energy_req_ub], dtype=float) for i in self.sd_uid]

        # min energy constraint data
        self.sd_num_min_energy_constr = numpy.array([len(data_map[i].energy_req_lb) for i in self.sd_uid], dtype=int)
        self.sd_min_energy_constr_a_start_list = [
            numpy.array([s[0] for s in data_map[i].energy_req_lb], dtype=float) for i in self.sd_uid]
        self.sd_min_energy_constr_a_end_list = [
            numpy.array([s[1] for s in data_map[i].energy_req_lb], dtype=float) for i in self.sd_uid]
        self.sd_min_energy_constr_min_energy_list = [
            numpy.array([s[2] for s in data_map[i].energy_req_lb], dtype=float) for i in self.sd_uid]

        # prior state data
        self.sd_u_on_0 = numpy.array([data_map[i].initial_status.on_status for i in self.sd_uid], dtype=int)
        self.sd_p_0 = numpy.array([data_map[i].initial_status.p for i in self.sd_uid], dtype=float)
        self.sd_q_0 = numpy.array([data_map[i].initial_status.q for i in self.sd_uid], dtype=float)
        self.sd_d_dn_0 = numpy.array([data_map[i].initial_status.accu_down_time for i in self.sd_uid], dtype=float)
        self.sd_d_up_0 = numpy.array([data_map[i].initial_status.accu_up_time for i in self.sd_uid], dtype=float)
        
        # p-q indicators:
        self.sd_is_pqe = numpy.array([data_map[i].q_linear_cap for i in self.sd_uid], dtype=int)
        self.sd_is_pqa = numpy.array([data_map[i].q_bound_cap for i in self.sd_uid], dtype=int)
        self.sd_is_pqi = numpy.array([data_map[i].q_bound_cap for i in self.sd_uid], dtype=int)
        self.sd_is_pqae = self.sd_is_pqa + self.sd_is_pqe
        self.sd_is_pqie = self.sd_is_pqi + self.sd_is_pqe
        self.num_pqe = numpy.sum(self.sd_is_pqe)
        self.num_pqa = numpy.sum(self.sd_is_pqa)
        self.num_pqi = numpy.sum(self.sd_is_pqi)
        self.num_pqae = numpy.sum(self.sd_is_pqae)
        self.num_pqie = numpy.sum(self.sd_is_pqie)

        # reserves:
        self.sd_p_rgu_max = numpy.array([data_map[i].p_reg_res_up_ub for i in self.sd_uid], dtype=float)
        self.sd_p_rgd_max = numpy.array([data_map[i].p_reg_res_down_ub for i in self.sd_uid], dtype=float)
        self.sd_p_scr_max = numpy.array([data_map[i].p_syn_res_ub for i in self.sd_uid], dtype=float)
        self.sd_p_nsc_max = numpy.array([data_map[i].p_nsyn_res_ub for i in self.sd_uid], dtype=float)
        self.sd_p_rru_on_max = numpy.array([data_map[i].p_ramp_res_up_online_ub for i in self.sd_uid], dtype=float)
        self.sd_p_rrd_on_max = numpy.array([data_map[i].p_ramp_res_down_online_ub for i in self.sd_uid], dtype=float)
        self.sd_p_rru_off_max = numpy.array([data_map[i].p_ramp_res_up_offline_ub for i in self.sd_uid], dtype=float)
        self.sd_p_rrd_off_max = numpy.array([data_map[i].p_ramp_res_down_offline_ub for i in self.sd_uid], dtype=float)
        
        # p-q optionals:
        self.sd_q_p0_pqe = numpy.array(
            [data_map[i].q_0 if data_map[i].q_linear_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_q_p0_pqa = numpy.array(
            [data_map[i].q_0_ub if data_map[i].q_bound_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_q_p0_pqi = numpy.array(
            [data_map[i].q_0_lb if data_map[i].q_bound_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_beta_pqe = numpy.array(
            [data_map[i].beta if data_map[i].q_linear_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_beta_pqa = numpy.array(
            [data_map[i].beta_ub if data_map[i].q_bound_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_beta_pqi = numpy.array(
            [data_map[i].beta_lb if data_map[i].q_bound_cap else 0.0 for i in self.sd_uid], dtype=float)
        self.sd_q_p0_pqae = self.sd_q_p0_pqe + self.sd_q_p0_pqa
        self.sd_q_p0_pqie = self.sd_q_p0_pqe + self.sd_q_p0_pqi
        self.sd_beta_pqae = self.sd_beta_pqe + self.sd_beta_pqa
        self.sd_beta_pqie = self.sd_beta_pqe + self.sd_beta_pqi
        
    def set_acl(self, data):

        data_map = {x.uid:x for x in data.network.ac_line}
        acl_fbus_uid = numpy.array([data_map[i].fr_bus for i in self.acl_uid], dtype=str)
        acl_tbus_uid = numpy.array([data_map[i].to_bus for i in self.acl_uid], dtype=str)
        self.acl_fbus = numpy.array([self.bus_map[i] for i in acl_fbus_uid], dtype=int)
        self.acl_tbus = numpy.array([self.bus_map[i] for i in acl_tbus_uid], dtype=int)
        self.acl_r_sr = numpy.array([data_map[i].r for i in self.acl_uid], dtype=float)
        self.acl_x_sr = numpy.array([data_map[i].x for i in self.acl_uid], dtype=float)
        self.acl_g_sr = self.acl_r_sr / (self.acl_r_sr**2 + self.acl_x_sr**2)
        self.acl_b_sr = - self.acl_x_sr / (self.acl_r_sr**2 + self.acl_x_sr**2)
        self.acl_b_ch = numpy.array([data_map[i].b for i in self.acl_uid], dtype=float)
        self.acl_s_max = numpy.array([data_map[i].mva_ub_nom for i in self.acl_uid], dtype=float)
        self.acl_s_max_ctg = numpy.array([data_map[i].mva_ub_em for i in self.acl_uid], dtype=float)
        self.acl_c_su = numpy.array([data_map[i].connection_cost for i in self.acl_uid], dtype=float)
        self.acl_c_sd = numpy.array([data_map[i].disconnection_cost for i in self.acl_uid], dtype=float)
        self.acl_u_on_0 = numpy.array([data_map[i].initial_status.on_status for i in self.acl_uid], dtype=int)
        self.acl_g_fr = numpy.array(
            [data_map[i].g_fr if data_map[i].additional_shunt == 1 else 0.0 for i in self.acl_uid], dtype=float)
        self.acl_b_fr = numpy.array(
            [data_map[i].b_fr if data_map[i].additional_shunt == 1 else 0.0 for i in self.acl_uid], dtype=float)
        self.acl_g_to = numpy.array(
            [data_map[i].g_to if data_map[i].additional_shunt == 1 else 0.0 for i in self.acl_uid], dtype=float)
        self.acl_b_to = numpy.array(
            [data_map[i].b_to if data_map[i].additional_shunt == 1 else 0.0 for i in self.acl_uid], dtype=float)

    def set_dcl(self, data):

        data_map = {x.uid:x for x in data.network.dc_line}
        dcl_fbus_uid = numpy.array([data_map[i].fr_bus for i in self.dcl_uid], dtype=str)
        dcl_tbus_uid = numpy.array([data_map[i].to_bus for i in self.dcl_uid], dtype=str)
        self.dcl_fbus = numpy.array([self.bus_map[i] for i in dcl_fbus_uid], dtype=int)
        self.dcl_tbus = numpy.array([self.bus_map[i] for i in dcl_tbus_uid], dtype=int)
        self.dcl_p_max = numpy.array([data_map[i].pdc_ub for i in self.dcl_uid], dtype=float)
        self.dcl_q_fr_max = numpy.array([data_map[i].qdc_fr_ub for i in self.dcl_uid], dtype=float)
        self.dcl_q_fr_min = numpy.array([data_map[i].qdc_fr_lb for i in self.dcl_uid], dtype=float)
        self.dcl_q_to_max = numpy.array([data_map[i].qdc_to_ub for i in self.dcl_uid], dtype=float)
        self.dcl_q_to_min = numpy.array([data_map[i].qdc_to_lb for i in self.dcl_uid], dtype=float)
        self.dcl_p_0 = numpy.array([data_map[i].initial_status.pdc_fr for i in self.dcl_uid], dtype=float)
        self.dcl_q_fr_0 = numpy.array([data_map[i].initial_status.qdc_fr for i in self.dcl_uid], dtype=float)
        self.dcl_q_to_0 = numpy.array([data_map[i].initial_status.qdc_to for i in self.dcl_uid], dtype=float)

    def set_xfr(self, data):

        data_map = {x.uid:x for x in data.network.two_winding_transformer}
        xfr_fbus_uid = numpy.array([data_map[i].fr_bus for i in self.xfr_uid], dtype=str)
        xfr_tbus_uid = numpy.array([data_map[i].to_bus for i in self.xfr_uid], dtype=str)
        self.xfr_fbus = numpy.array([self.bus_map[i] for i in xfr_fbus_uid], dtype=int)
        self.xfr_tbus = numpy.array([self.bus_map[i] for i in xfr_tbus_uid], dtype=int)
        self.xfr_r_sr = numpy.array([data_map[i].r for i in self.xfr_uid], dtype=float)
        self.xfr_x_sr = numpy.array([data_map[i].x for i in self.xfr_uid], dtype=float)
        self.xfr_g_sr = self.xfr_r_sr / (self.xfr_r_sr**2 + self.xfr_x_sr**2)
        self.xfr_b_sr = - self.xfr_x_sr / (self.xfr_r_sr**2 + self.xfr_x_sr**2)
        self.xfr_b_ch = numpy.array([data_map[i].b for i in self.xfr_uid], dtype=float)
        self.xfr_tau_max = numpy.array([data_map[i].tm_ub for i in self.xfr_uid], dtype=float)
        self.xfr_tau_min = numpy.array([data_map[i].tm_lb for i in self.xfr_uid], dtype=float)
        self.xfr_phi_max = numpy.array([data_map[i].ta_ub for i in self.xfr_uid], dtype=float)
        self.xfr_phi_min = numpy.array([data_map[i].ta_lb for i in self.xfr_uid], dtype=float)
        self.xfr_s_max = numpy.array([data_map[i].mva_ub_nom for i in self.xfr_uid], dtype=float)
        self.xfr_s_max_ctg = numpy.array([data_map[i].mva_ub_em for i in self.xfr_uid], dtype=float)
        self.xfr_c_su = numpy.array([data_map[i].connection_cost for i in self.xfr_uid], dtype=float)
        self.xfr_c_sd = numpy.array([data_map[i].disconnection_cost for i in self.xfr_uid], dtype=float)
        self.xfr_u_on_0 = numpy.array([data_map[i].initial_status.on_status for i in self.xfr_uid], dtype=int)
        self.xfr_tau_0 = numpy.array([data_map[i].initial_status.tm for i in self.xfr_uid], dtype=float)
        self.xfr_phi_0 = numpy.array([data_map[i].initial_status.ta for i in self.xfr_uid], dtype=float)
        self.xfr_g_fr = numpy.array(
            [data_map[i].g_fr if data_map[i].additional_shunt == 1 else 0.0 for i in self.xfr_uid], dtype=float)
        self.xfr_b_fr = numpy.array(
            [data_map[i].b_fr if data_map[i].additional_shunt == 1 else 0.0 for i in self.xfr_uid], dtype=float)
        self.xfr_g_to = numpy.array(
            [data_map[i].g_to if data_map[i].additional_shunt == 1 else 0.0 for i in self.xfr_uid], dtype=float)
        self.xfr_b_to = numpy.array(
            [data_map[i].b_to if data_map[i].additional_shunt == 1 else 0.0 for i in self.xfr_uid], dtype=float)

    def set_prz(self, data):

        data_map = {x.uid:x for x in data.network.active_zonal_reserve}
        self.prz_sigma_rgu = numpy.array([data_map[i].REG_UP for i in self.prz_uid], dtype=float)
        self.prz_sigma_rgd = numpy.array([data_map[i].REG_DOWN for i in self.prz_uid], dtype=float)
        self.prz_sigma_scr = numpy.array([data_map[i].SYN for i in self.prz_uid], dtype=float)
        self.prz_sigma_nsc = numpy.array([data_map[i].NSYN for i in self.prz_uid], dtype=float)
        self.prz_c_rgu = numpy.array([data_map[i].REG_UP_vio_cost for i in self.prz_uid], dtype=float)
        self.prz_c_rgd = numpy.array([data_map[i].REG_DOWN_vio_cost for i in self.prz_uid], dtype=float)
        self.prz_c_scr = numpy.array([data_map[i].SYN_vio_cost for i in self.prz_uid], dtype=float)
        self.prz_c_nsc = numpy.array([data_map[i].NSYN_vio_cost for i in self.prz_uid], dtype=float)
        self.prz_c_rru = numpy.array([data_map[i].RAMPING_RESERVE_UP_vio_cost for i in self.prz_uid], dtype=float)
        self.prz_c_rrd = numpy.array([data_map[i].RAMPING_RESERVE_DOWN_vio_cost for i in self.prz_uid], dtype=float)
        prz_bus_list = [[] for i in self.prz_uid]
        for i in range(self.num_bus):
            for j in self.bus_prz_list[i]:
                prz_bus_list[j].append(i)
        self.prz_num_bus = numpy.array([len(i) for i in prz_bus_list], dtype=int)
        self.prz_bus_list = [numpy.array(i, dtype=int) for i in prz_bus_list]
        prz_sd_list = [[] for i in self.prz_uid]
        for i in range(self.num_sd):
            for j in self.bus_prz_list[self.sd_bus[i]]:
                prz_sd_list[j].append(i)
        self.prz_num_sd = numpy.array([len(i) for i in prz_sd_list], dtype=int)
        self.prz_sd_list = [numpy.array(i, dtype=int) for i in prz_sd_list]

    def set_qrz(self, data):

        data_map = {x.uid:x for x in data.network.reactive_zonal_reserve}
        self.qrz_c_qru = numpy.array([data_map[i].REACT_UP_vio_cost for i in self.qrz_uid])
        self.qrz_c_qrd = numpy.array([data_map[i].REACT_DOWN_vio_cost for i in self.qrz_uid])
        qrz_bus_list = [[] for i in self.qrz_uid]
        for i in range(self.num_bus):
            for j in self.bus_qrz_list[i]:
                qrz_bus_list[j].append(i)
        self.qrz_num_bus = numpy.array([len(i) for i in qrz_bus_list], dtype=int)
        self.qrz_bus_list = [numpy.array(i, dtype=int) for i in qrz_bus_list]
        qrz_sd_list = [[] for i in self.qrz_uid]
        for i in range(self.num_sd):
            for j in self.bus_qrz_list[self.sd_bus[i]]:
                qrz_sd_list[j].append(i)
        self.qrz_num_sd = numpy.array([len(i) for i in qrz_sd_list], dtype=int)
        self.qrz_sd_list = [numpy.array(i, dtype=int) for i in qrz_sd_list]

    def set_t(self, data):

        self.t_d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
        self.t_a_end = numpy.cumsum(self.t_d)
        self.t_a_start = numpy.zeros(shape=(self.num_t, ), dtype=float)
        self.t_a_start[1:self.num_t] = self.t_a_end[0:(self.num_t - 1)]
        self.t_a_mid = 0.5 * (self.t_a_start + self.t_a_end)

    def set_k(self, data):

        k_out_device_uid = numpy.array([k.components[0] for k in data.reliability.contingency])
        self.k_out_device = numpy.array([self.all_map[k_out_device_uid[i]] for i in range(self.num_k)], dtype=int)
        self.k_out_is_acl = numpy.array([self.all_is_acl[self.k_out_device[i]] for i in range(self.num_k)], dtype=int)
        self.k_out_is_dcl = numpy.array([self.all_is_dcl[self.k_out_device[i]] for i in range(self.num_k)], dtype=int)
        self.k_out_is_xfr = numpy.array([self.all_is_xfr[self.k_out_device[i]] for i in range(self.num_k)], dtype=int)
        self.k_out_acl = numpy.array(
            [self.acl_map[k_out_device_uid[i]] if self.k_out_is_acl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_dcl = numpy.array(
            [self.dcl_map[k_out_device_uid[i]] if self.k_out_is_dcl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_xfr = numpy.array(
            [self.xfr_map[k_out_device_uid[i]] if self.k_out_is_xfr[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_fbus_is_acl = numpy.array(
            [self.acl_fbus[self.k_out_acl[i]] if self.k_out_is_acl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_tbus_is_acl = numpy.array(
            [self.acl_tbus[self.k_out_acl[i]] if self.k_out_is_acl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_fbus_is_dcl = numpy.array(
            [self.dcl_fbus[self.k_out_dcl[i]] if self.k_out_is_dcl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_tbus_is_dcl = numpy.array(
            [self.dcl_tbus[self.k_out_dcl[i]] if self.k_out_is_dcl[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_fbus_is_xfr = numpy.array(
            [self.xfr_fbus[self.k_out_xfr[i]] if self.k_out_is_xfr[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_tbus_is_xfr = numpy.array(
            [self.xfr_tbus[self.k_out_xfr[i]] if self.k_out_is_xfr[i] else 0 for i in range(self.num_k)], dtype=int)
        self.k_out_fbus = self.k_out_fbus_is_acl + self.k_out_fbus_is_dcl + self.k_out_fbus_is_xfr
        self.k_out_tbus = self.k_out_tbus_is_acl + self.k_out_tbus_is_dcl + self.k_out_tbus_is_xfr

    def set_sd_t(self, data):

        data_map = {x.uid:x for x in data.time_series_input.simple_dispatchable_device}
        self.sd_t_u_on_max = numpy.reshape(
            numpy.array([data_map[i].on_status_ub for i in self.sd_uid], dtype=int),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_u_on_min = numpy.reshape(
            numpy.array([data_map[i].on_status_lb for i in self.sd_uid], dtype=int),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_p_max = numpy.reshape(
            numpy.array([data_map[i].p_ub for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_p_min = numpy.reshape(
            numpy.array([data_map[i].p_lb for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_q_max = numpy.reshape(
            numpy.array([data_map[i].q_ub for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_q_min = numpy.reshape(
            numpy.array([data_map[i].q_lb for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rgu = numpy.reshape(
            numpy.array([data_map[i].p_reg_res_up_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rgd = numpy.reshape(
            numpy.array([data_map[i].p_reg_res_down_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_scr = numpy.reshape(
            numpy.array([data_map[i].p_syn_res_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_nsc = numpy.reshape(
            numpy.array([data_map[i].p_nsyn_res_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rru_on = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_up_online_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rrd_on = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_down_online_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rru_off = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_up_offline_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_rrd_off = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_down_offline_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_qru = numpy.reshape(
            numpy.array([data_map[i].q_res_up_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_c_qrd = numpy.reshape(
            numpy.array([data_map[i].q_res_down_cost for i in self.sd_uid], dtype=float),
            newshape=(self.num_sd, self.num_t))

    def set_sd_t_cost(self, data):
        '''
        cost blocks are processed in two ways beyond the raw data
        1. marginal cost value is negated for consumer devices, i.e. positive benefit is transformed into negative cost
        2. for each device and each time interval, the cost blocks are sorted in order of increasing marginal cost
        then to evaluate the cost of a given p value, one loops over the cost blocks in order,
        applying the cost to the remaining dispatched energy, subtracting pmax from the dispatched energy
        '''

        data_map = {x.uid:x for x in data.time_series_input.simple_dispatchable_device}
        cost_blocks = [data_map[i].cost for i in self.sd_uid]
        for i in range(self.num_sd): # negate the cost value for consumer blocks. keep producer blocks as is
            if self.sd_is_cs[i]:
                cost_blocks[i] = [[((-1.0) * t_b_c[0], t_b_c[1]) for t_b_c in t_c] for t_c in cost_blocks[i]]
        for i in range(self.num_sd): # sort blocks in order of increasing cost
            cost_blocks[i] = [sorted(t_c, key=(lambda x: x[0])) for t_c in cost_blocks[i]]
        self.sd_t_num_block = numpy.reshape(
            numpy.array([[len(t_c) for t_c in c] for c in cost_blocks], dtype=int),
            newshape=(self.num_sd, self.num_t))
        self.sd_t_block_c_list = [[numpy.array([t_b_c[0] for t_b_c in t_c], dtype=float) for t_c in c] for c in cost_blocks]
        self.sd_t_block_p_max_list = [
            [numpy.array([t_b_c[1] for t_b_c in t_c], dtype=float) for t_c in c] for c in cost_blocks]

    def set_prz_t(self, data):

        data_map = {x.uid:x for x in data.time_series_input.active_zonal_reserve}
        self.prz_t_p_rru_min = numpy.reshape(
            numpy.array([data_map[i].RAMPING_RESERVE_UP for i in self.prz_uid], dtype=float),
            newshape=(self.num_qrz, self.num_t))
        self.prz_t_p_rrd_min = numpy.reshape(
            numpy.array([data_map[i].RAMPING_RESERVE_DOWN for i in self.prz_uid], dtype=float),
            newshape=(self.num_prz, self.num_t))

    def set_qrz_t(self, data):

        data_map = {x.uid:x for x in data.time_series_input.reactive_zonal_reserve}
        self.qrz_t_q_qru_min = numpy.reshape(
            numpy.array([data_map[i].REACT_UP for i in self.qrz_uid], dtype=float),
            newshape=(self.num_qrz, self.num_t))
        self.qrz_t_q_qrd_min = numpy.reshape(
            numpy.array([data_map[i].REACT_DOWN for i in self.qrz_uid], dtype=float),
            newshape=(self.num_qrz, self.num_t))

class OutputData(object):

    def __init__(self):

        pass

    def set_from_data_model(self, input_data, output_data_model):
        
        self.set_bus_t(input_data, output_data_model)
        self.set_sh_t(input_data, output_data_model)
        self.set_sd_t(input_data, output_data_model)
        self.set_acl_t(input_data, output_data_model)
        self.set_dcl_t(input_data, output_data_model)
        self.set_xfr_t(input_data, output_data_model)

    def set_bus_t(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.bus}
        self.bus_t_v = numpy.reshape(
            numpy.array([data_map[i].vm for i in input_data.bus_uid], dtype=float),
            newshape=(input_data.num_bus, input_data.num_t))
        self.bus_t_theta = numpy.reshape(
            numpy.array([data_map[i].va for i in input_data.bus_uid], dtype=float),
            newshape=(input_data.num_bus, input_data.num_t))

    def set_sh_t(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.shunt}
        self.sh_t_u_st = numpy.reshape(
            numpy.array([data_map[i].step for i in input_data.sh_uid], dtype=int),
            newshape=(input_data.num_sh, input_data.num_t))

    def set_sd_t(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.simple_dispatchable_device}
        self.sd_t_u_on = numpy.reshape(
            numpy.array([data_map[i].on_status for i in input_data.sd_uid], dtype=int),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_on = numpy.reshape(
            numpy.array([data_map[i].p_on for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_q = numpy.reshape(
            numpy.array([data_map[i].q for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rgu = numpy.reshape(
            numpy.array([data_map[i].p_reg_res_up for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rgd = numpy.reshape(
            numpy.array([data_map[i].p_reg_res_down for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_scr = numpy.reshape(
            numpy.array([data_map[i].p_syn_res for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_nsc = numpy.reshape(
            numpy.array([data_map[i].p_nsyn_res for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rru_on = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_up_online for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rrd_on = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_down_online for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rru_off = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_up_offline for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_p_rrd_off = numpy.reshape(
            numpy.array([data_map[i].p_ramp_res_down_offline for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_q_qru = numpy.reshape(
            numpy.array([data_map[i].q_res_up for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))
        self.sd_t_q_qrd = numpy.reshape(
            numpy.array([data_map[i].q_res_down for i in input_data.sd_uid], dtype=float),
            newshape=(input_data.num_sd, input_data.num_t))

    def set_acl_t(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.ac_line}
        self.acl_t_u_on = numpy.reshape(
            numpy.array([data_map[i].on_status for i in input_data.acl_uid], dtype=int), # , dtype=numpy.int8) # could help, but not much
            newshape=(input_data.num_acl, input_data.num_t))

    def set_dcl_t(self, input_data, output_data_model):

        # todo note the reshape here to deal with empty set of DC lines
        # in general we need this technique on all arraydata fields of dim >= 2
        # maybe ndmin=2 in the array constructor would work
        # also need dtype in the array constructor
        data_map = {x.uid:x for x in output_data_model.time_series_output.dc_line}
        #self.dcl_t_p = numpy.array([data_map[i].pdc_fr for i in input_data.dcl_uid], ndmin=2)
        self.dcl_t_p = numpy.reshape(
            numpy.array([data_map[i].pdc_fr for i in input_data.dcl_uid], dtype=float),
            newshape=(input_data.num_dcl, input_data.num_t))
        self.dcl_t_q_fr = numpy.reshape(
            numpy.array([data_map[i].qdc_fr for i in input_data.dcl_uid], dtype=float),
            newshape=(input_data.num_dcl, input_data.num_t))
        self.dcl_t_q_to = numpy.reshape(
            numpy.array([data_map[i].qdc_to for i in input_data.dcl_uid], dtype=float),
            newshape=(input_data.num_dcl, input_data.num_t))

    def set_xfr_t(self, input_data, output_data_model):

        data_map = {x.uid:x for x in output_data_model.time_series_output.two_winding_transformer}
        self.xfr_t_u_on = numpy.reshape(
            numpy.array([data_map[i].on_status for i in input_data.xfr_uid], dtype=int),
            newshape=(input_data.num_xfr, input_data.num_t))
        self.xfr_t_tau = numpy.reshape(
            numpy.array([data_map[i].tm for i in input_data.xfr_uid], dtype=float),
            newshape=(input_data.num_xfr, input_data.num_t))
        self.xfr_t_phi = numpy.reshape(
            numpy.array([data_map[i].ta for i in input_data.xfr_uid], dtype=float),
            newshape=(input_data.num_xfr, input_data.num_t))

