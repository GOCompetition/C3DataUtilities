'''
Evaluation of solutions to the GO Competition Challenge 3 problem.
'''

import time
import numpy
from datautilities import arraydata
from datautilities import utils

class SolutionEvaluator(object):

    def __init__(self, problem, solution, config={}):
        
        self.config = config
        self.set_problem(problem)
        self.set_solution(solution)
        self.set_solution_zero()
        self.set_work_zero()

    def run(self):

        self.eval_sd_t_u_on_max()
        self.eval_sd_t_u_on_min()
        self.eval_sd_t_d_up_dn()
        self.eval_sd_t_u_su_sd()
        self.eval_sd_t_d_up_min()
        self.eval_sd_t_d_dn_min()
        self.eval_sd_t_z_on()
        self.eval_sd_t_z_su()
        self.eval_sd_t_z_sd()

        self.eval_bus_t_v_max()
        self.eval_bus_t_v_min()
        self.proj_bus_t_v_max()
        self.proj_bus_t_v_min()

        # no proj needed because integer
        self.eval_sh_t_u_st_max()
        self.eval_sh_t_u_st_min()
        self.eval_sh_t_p_q()

        self.eval_dcl_t_p_max()
        self.eval_dcl_t_p_min()
        self.proj_dcl_t_p_max()
        self.proj_dcl_t_p_min()
        self.eval_dcl_t_q_fr_max()
        self.eval_dcl_t_q_fr_min()
        self.proj_dcl_t_q_fr_max()
        self.proj_dcl_t_q_fr_min()
        self.eval_dcl_t_q_to_max()
        self.eval_dcl_t_q_to_min()
        self.proj_dcl_t_q_to_max()
        self.proj_dcl_t_q_to_min()

        self.eval_xfr_t_tau_max()
        self.eval_xfr_t_tau_min()
        self.proj_xfr_t_tau_max()
        self.proj_xfr_t_tau_min()
        self.eval_xfr_t_phi_max()
        self.eval_xfr_t_phi_min()
        self.proj_xfr_t_phi_max()
        self.proj_xfr_t_phi_min()

        self.eval_acl_t_u_su()
        self.eval_acl_t_u_sd()
        self.eval_xfr_t_u_su()
        self.eval_xfr_t_u_sd()

        self.eval_acl_t_p_q_fr_to()
        self.eval_xfr_t_p_q_fr_to()

        self.eval_acl_t_s_max_fr_to()
        self.eval_xfr_t_s_max_fr_to()

        #self.eval_acl_t_u_su_sd_test()

    def set_problem(self, prob):

        # todo - might be more convenient to flatten the problem attributes into SolutionEvaluator
        self.problem = prob

    def set_solution(self, sol):

        # note these are views not copies of the solution arrays
        self.bus_t_v = sol.bus_t_v
        self.bus_t_theta = sol.bus_t_theta
        self.sh_t_u_st = sol.sh_t_u_st
        self.sd_t_u_on = sol.sd_t_u_on
        self.sd_t_p_on = sol.sd_t_p_on
        self.sd_t_q = sol.sd_t_q
        self.sd_t_p_rgu = sol.sd_t_p_rgu
        self.sd_t_p_rgd = sol.sd_t_p_rgd
        self.sd_t_p_scr = sol.sd_t_p_scr
        self.sd_t_p_nsc = sol.sd_t_p_nsc
        self.sd_t_p_rru_on = sol.sd_t_p_rru_on
        self.sd_t_p_rrd_on = sol.sd_t_p_rrd_on
        self.sd_t_p_rru_off = sol.sd_t_p_rru_off
        self.sd_t_p_rrd_off = sol.sd_t_p_rrd_off
        self.sd_t_q_qru = sol.sd_t_q_qru
        self.sd_t_q_qrd = sol.sd_t_q_qrd
        self.acl_t_u_on = sol.acl_t_u_on
        self.dcl_t_p = sol.dcl_t_p
        self.dcl_t_q_fr = sol.dcl_t_q_fr
        self.dcl_t_q_to = sol.dcl_t_q_to
        self.xfr_t_u_on = sol.xfr_t_u_on
        self.xfr_t_tau = sol.xfr_t_tau
        self.xfr_t_phi = sol.xfr_t_phi

    def set_solution_zero(self):
        '''
        set solution arrays
        '''

        self.sd_t_u_su = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=int)
        self.sd_t_u_sd = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=int)
        self.sd_t_z = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=float)
        self.sd_t_d_up_start = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=float)
        self.sd_t_d_dn_start = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=float)

        self.sh_t_p = numpy.zeros(shape=(self.problem.num_sh, self.problem.num_t), dtype=float)
        self.sh_t_q = numpy.zeros(shape=(self.problem.num_sh, self.problem.num_t), dtype=float)

        self.acl_t_p_fr = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)
        self.acl_t_p_to = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)
        self.acl_t_q_fr = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)
        self.acl_t_q_to = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)

        self.xfr_t_p_fr = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)
        self.xfr_t_p_to = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)
        self.xfr_t_q_fr = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)
        self.xfr_t_q_to = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)

    def set_work_zero(self):
        '''
        set working arrays
        '''
        
        self.bus_float = numpy.zeros(shape=(self.problem.num_bus, ), dtype=float)
        self.sh_float = numpy.zeros(shape=(self.problem.num_sh, ), dtype=float)
        self.sd_float = numpy.zeros(shape=(self.problem.num_sd, ), dtype=float)
        self.acl_float = numpy.zeros(shape=(self.problem.num_acl, ), dtype=float)
        self.dcl_float = numpy.zeros(shape=(self.problem.num_dcl, ), dtype=float)
        self.xfr_float = numpy.zeros(shape=(self.problem.num_xfr, ), dtype=float)
        
        self.acl_int = numpy.zeros(shape=(self.problem.num_acl, ), dtype=int)
        self.xfr_int = numpy.zeros(shape=(self.problem.num_xfr, ), dtype=int)

        self.sd_t_int = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=int)
        self.sd_t_float = numpy.zeros(shape=(self.problem.num_sd, self.problem.num_t), dtype=float)

        self.bus_t_float = numpy.zeros(shape=(self.problem.num_bus, self.problem.num_t), dtype=float)

        self.sh_t_int = numpy.zeros(shape=(self.problem.num_sh, self.problem.num_t), dtype=int)
        self.sh_t_float = numpy.zeros(shape=(self.problem.num_sh, self.problem.num_t), dtype=float)

        self.dcl_t_float = numpy.zeros(shape=(self.problem.num_dcl, self.problem.num_t), dtype=float)

        self.acl_t_int = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=int)
        self.acl_t_float = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)
        self.acl_t_float_1 = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)
        self.acl_t_float_2 = numpy.zeros(shape=(self.problem.num_acl, self.problem.num_t), dtype=float)

        self.xfr_t_int = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=int)
        self.xfr_t_float = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)
        self.xfr_t_float_1 = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)
        self.xfr_t_float_2 = numpy.zeros(shape=(self.problem.num_xfr, self.problem.num_t), dtype=float)

    def get_summary(self):

        keys = [
            'viol_sd_t_u_on_max',
            'viol_sd_t_u_on_min',
            'sum_sd_t_su',
            'sum_sd_t_sd',
            'viol_sd_t_d_up_min',
            'viol_sd_t_d_dn_min',
            'sum_sd_t_z_on',
            'sum_sd_t_z_su',
            'sum_sd_t_z_sd',
            'viol_bus_t_v_max',
            'viol_bus_t_v_min',
            'viol_sh_t_u_st_max',
            'viol_sh_t_u_st_min',
            'viol_dcl_t_p_max',
            'viol_dcl_t_p_min',
            'viol_dcl_t_q_fr_max',
            'viol_dcl_t_q_fr_min',
            'viol_dcl_t_q_to_max',
            'viol_dcl_t_q_to_min',
            'viol_xfr_t_tau_max',
            'viol_xfr_t_tau_min',
            'viol_xfr_t_phi_max',
            'viol_xfr_t_phi_min',
            'viol_acl_t_u_su_max',
            'viol_acl_t_u_sd_max',
            'viol_xfr_t_u_su_max',
            'viol_xfr_t_u_sd_max',
            'sum_acl_t_u_su',
            'sum_acl_t_u_sd',
            'sum_xfr_t_u_su',
            'sum_xfr_t_u_sd',
            'sum_acl_t_z_su',
            'sum_acl_t_z_sd',
            'sum_xfr_t_z_su',
            'sum_xfr_t_z_sd',
            ]
        summary = {k: getattr(self, k, None) for k in keys}
        return summary

    def eval_sd_t_u_on_max(self):

        numpy.subtract(self.sd_t_u_on, self.problem.sd_t_u_on_max, out=self.sd_t_int)
        self.viol_sd_t_u_on_max = utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])

    def eval_sd_t_u_on_min(self):

        numpy.subtract(self.problem.sd_t_u_on_min, self.sd_t_u_on, out=self.sd_t_int)
        self.viol_sd_t_u_on_min = utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])

    def eval_sd_t_d_up_dn(self):
        '''
        evaluate uptime and downtime at the start of each interval
        use this to evaluate min up/down time constraints and downtime-dependent startup costs
        '''
        
        sd_d_up_start = numpy.zeros(shape=(self.problem.num_sd, ), dtype=float)
        sd_d_dn_start = numpy.zeros(shape=(self.problem.num_sd, ), dtype=float)
        sd_d_up_end = numpy.zeros(shape=(self.problem.num_sd, ), dtype=float)
        sd_d_dn_end = numpy.zeros(shape=(self.problem.num_sd, ), dtype=float)

        sd_d_up_end[:] = self.problem.sd_d_up_0
        sd_d_dn_end[:] = self.problem.sd_d_dn_0
        
        for t in range(self.problem.num_t):
            sd_d_up_start[:] = sd_d_up_end
            sd_d_dn_start[:] = sd_d_dn_end
            numpy.add(
                sd_d_up_start, self.problem.t_d[t],
                out=sd_d_up_end, where=(self.sd_t_u_on[:,t] == 1))
            numpy.add(
                sd_d_dn_start, self.problem.t_d[t],
                out=sd_d_dn_end, where=(self.sd_t_u_on[:,t] == 0))
            sd_d_up_end[self.sd_t_u_on[:,t] == 0] = 0.0
            sd_d_dn_end[self.sd_t_u_on[:,t] == 1] = 0.0
            self.sd_t_d_up_start[:,t] = sd_d_up_start
            self.sd_t_d_dn_start[:,t] = sd_d_dn_start
        # print('up_start:')
        # print(self.sd_t_d_up_start)
        # print('dn_start:')
        # print(self.sd_t_d_dn_start)
        
    def eval_sd_t_u_su_sd(self):

        self.sd_t_int[:] = numpy.diff(
            self.sd_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.sd_u_on_0, newshape=(self.problem.num_sd, 1)))
        numpy.maximum(self.sd_t_int, 0, out=self.sd_t_u_su)
        numpy.negative(self.sd_t_int, out=self.sd_t_int)
        numpy.maximum(self.sd_t_int, 0, out=self.sd_t_u_sd)
        self.sum_sd_t_su = numpy.sum(self.sd_t_u_su)
        self.sum_sd_t_sd = numpy.sum(self.sd_t_u_sd)

    def eval_sd_t_d_up_min(self):
        '''
        evaluate min uptime constraints on sd_t_u_sd
        if d_up_start < d_up_min - time_zero_tol then u_sd <= 0
        '''

        numpy.subtract(
            numpy.reshape(self.problem.sd_d_up_min, newshape=(self.problem.num_sd, 1)),
            self.sd_t_d_up_start, out=self.sd_t_float)
        numpy.subtract(self.sd_t_float, self.config['time_eq_tol'], out=self.sd_t_float)
        numpy.greater(self.sd_t_float, 0.0, out=self.sd_t_int)
        numpy.minimum(self.sd_t_int, self.sd_t_u_sd, out=self.sd_t_int)
        self.viol_sd_t_d_up_min = utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])

    def eval_sd_t_d_dn_min(self):
        '''
        evaluate min downtime constraints on sd_t_u_su
        if d_dn_start < d_dn_min - time_zero_tol then u_su <= 0
        '''

        numpy.subtract(
            numpy.reshape(self.problem.sd_d_dn_min, newshape=(self.problem.num_sd, 1)),
            self.sd_t_d_dn_start, out=self.sd_t_float)
        numpy.subtract(self.sd_t_float, self.config['time_eq_tol'], out=self.sd_t_float)
        numpy.greater(self.sd_t_float, 0.0, out=self.sd_t_int) # note sd_t_in should still be dtype=int, with vals in 0, 1, not bool
        numpy.minimum(self.sd_t_int, self.sd_t_u_su, out=self.sd_t_int)
        self.viol_sd_t_d_dn_min = utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])

    def eval_sd_t_z_on(self):

        numpy.multiply(
            numpy.reshape(self.problem.sd_c_on, newshape=(self.problem.num_sd, 1)), self.sd_t_u_on, out=self.sd_t_float)
        numpy.multiply(
            numpy.reshape(self.problem.t_d, newshape=(1, self.problem.num_t)), self.sd_t_float, out=self.sd_t_float)
        numpy.add(self.sd_t_z, self.sd_t_float, out=self.sd_t_z)
        self.sum_sd_t_z_on = numpy.sum(self.sd_t_float)

    def eval_sd_t_z_su(self):

        numpy.multiply(
            numpy.reshape(self.problem.sd_c_su, newshape=(self.problem.num_sd, 1)), self.sd_t_u_su, out=self.sd_t_float)
        numpy.add(self.sd_t_z, self.sd_t_float, out=self.sd_t_z)
        self.sum_sd_t_z_su = numpy.sum(self.sd_t_float)

    def eval_sd_t_z_sd(self):

        numpy.multiply(
            numpy.reshape(self.problem.sd_c_sd, newshape=(self.problem.num_sd, 1)), self.sd_t_u_sd, out=self.sd_t_float)
        numpy.add(self.sd_t_z, self.sd_t_float, out=self.sd_t_z)
        self.sum_sd_t_z_sd = numpy.sum(self.sd_t_float)

    def eval_bus_t_v_max(self):
        '''
        check violation of bus v max
        '''

        numpy.subtract(
            self.bus_t_v, numpy.reshape(self.problem.bus_v_max, newshape=(self.problem.num_bus, 1)), out=self.bus_t_float)
        self.viol_bus_t_v_max = utils.get_max(self.bus_t_float, idx_lists=[self.problem.bus_uid, self.problem.t_num])

    def eval_bus_t_v_min(self):
        '''
        check violation of bus v min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.bus_v_min, newshape=(self.problem.num_bus, 1)), self.bus_t_v, out=self.bus_t_float)
        self.viol_bus_t_v_min = utils.get_max(self.bus_t_float, idx_lists=[self.problem.bus_uid, self.problem.t_num])

    def proj_bus_t_v_max(self):
        '''
        project bus v onto vmax
        '''

        numpy.minimum(
            self.bus_t_v, numpy.reshape(self.problem.bus_v_max, newshape=(self.problem.num_bus, 1)), out=self.bus_t_v)

    def proj_bus_t_v_min(self):
        '''
        project bus v onto vmin
        '''

        numpy.maximum(
            self.bus_t_v, numpy.reshape(self.problem.bus_v_min, newshape=(self.problem.num_bus, 1)), out=self.bus_t_v)

    def eval_sh_t_u_st_max(self):
        '''
        check violation of shunt u_st max
        '''

        numpy.subtract(
            self.sh_t_u_st, numpy.reshape(self.problem.sh_u_st_max, newshape=(self.problem.num_sh, 1)), out=self.sh_t_int)
        self.viol_sh_t_u_st_max = utils.get_max(self.sh_t_int, idx_lists=[self.problem.sh_uid, self.problem.t_num])        

    def eval_sh_t_u_st_min(self):
        '''
        check violation of shunt u_st min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.sh_u_st_min, newshape=(self.problem.num_sh, 1)), self.sh_t_u_st, out=self.sh_t_int)
        self.viol_sh_t_u_st_min = utils.get_max(self.sh_t_int, idx_lists=[self.problem.sh_uid, self.problem.t_num])        
        
    def eval_sh_t_p_q(self):
        '''
        evaluate shunt p/q
        '''

        self.sh_t_float[:] = self.bus_t_v[self.problem.sh_bus, :]
        numpy.power(self.sh_t_float, 2, out=self.sh_t_float)
        numpy.multiply(
            numpy.reshape(self.problem.sh_g_st, newshape=(self.problem.num_sh, 1)), self.sh_t_u_st, out=self.sh_t_p)
        numpy.multiply(self.sh_t_p, self.sh_t_float, out=self.sh_t_p)
        numpy.multiply(
            numpy.reshape(self.problem.sh_b_st, newshape=(self.problem.num_sh, 1)), self.sh_t_u_st, out=self.sh_t_q)
        numpy.multiply(self.sh_t_q, self.sh_t_float, out=self.sh_t_q)
        numpy.negative(self.sh_t_q, out=self.sh_t_q)

    def eval_dcl_t_p_max(self):
        '''
        evaluate violation of dcl p (from bus to to bus) max
        '''

        numpy.subtract(
            self.dcl_t_p, numpy.reshape(self.problem.dcl_p_max, newshape=(self.problem.num_dcl, 1)), out=self.dcl_t_float)
        self.viol_dcl_t_p_max = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def eval_dcl_t_p_min(self):
        '''
        evaluate violation of dcl p (from bus to to bus) min (= -max, max >= 0)
        '''

        numpy.negative(self.problem.dcl_p_max, out=self.dcl_float)
        numpy.subtract(
            numpy.reshape(self.dcl_float, newshape=(self.problem.num_dcl, 1)), self.dcl_t_p, out=self.dcl_t_float)
        self.viol_dcl_t_p_min = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def proj_dcl_t_p_max(self):
        '''
        project dcl p to max (>= 0)
        '''

        numpy.minimum(
            self.dcl_t_p, numpy.reshape(self.problem.dcl_p_max, newshape=(self.problem.num_dcl, 1)), out=self.dcl_t_p)

    def proj_dcl_t_p_min(self):
        '''
        project dcl p to min (= -max, max >= 0)
        '''

        numpy.negative(self.problem.dcl_p_max, out=self.dcl_float)
        numpy.maximum(
            self.dcl_t_p, numpy.reshape(self.dcl_float, newshape=(self.problem.num_dcl, 1)), out=self.dcl_t_p)






    def eval_dcl_t_q_fr_max(self):
        '''
        evaluate violation of dcl q_fr max
        '''

        numpy.subtract(
            self.dcl_t_q_fr, numpy.reshape(self.problem.dcl_q_fr_max, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_float)
        self.viol_dcl_t_q_fr_max = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def eval_dcl_t_q_fr_min(self):
        '''
        evaluate violation of dcl q_fr min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.dcl_q_fr_min, newshape=(self.problem.num_dcl, 1)), self.dcl_t_q_fr,
            out=self.dcl_t_float)
        self.viol_dcl_t_q_fr_min = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def proj_dcl_t_q_fr_max(self):
        '''
        project dcl q_fr to max
        '''

        numpy.minimum(
            self.dcl_t_q_fr, numpy.reshape(self.problem.dcl_q_fr_max, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_q_fr)

    def proj_dcl_t_q_fr_min(self):
        '''
        project dcl q_fr to min
        '''

        numpy.maximum(
            self.dcl_t_q_fr, numpy.reshape(self.problem.dcl_q_fr_min, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_q_fr)






    def eval_dcl_t_q_to_max(self):
        '''
        evaluate violation of dcl q_to max
        '''

        numpy.subtract(
            self.dcl_t_q_to, numpy.reshape(self.problem.dcl_q_to_max, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_float)
        self.viol_dcl_t_q_to_max = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def eval_dcl_t_q_to_min(self):
        '''
        evaluate violation of dcl q_to min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.dcl_q_to_min, newshape=(self.problem.num_dcl, 1)), self.dcl_t_q_to,
            out=self.dcl_t_float)
        self.viol_dcl_t_q_to_min = utils.get_max(self.dcl_t_float, idx_lists=[self.problem.dcl_uid, self.problem.t_num])

    def proj_dcl_t_q_to_max(self):
        '''
        project dcl q_to to max
        '''

        numpy.minimum(
            self.dcl_t_q_to, numpy.reshape(self.problem.dcl_q_to_max, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_q_to)

    def proj_dcl_t_q_to_min(self):
        '''
        project dcl q_to to min
        '''

        numpy.maximum(
            self.dcl_t_q_to, numpy.reshape(self.problem.dcl_q_to_min, newshape=(self.problem.num_dcl, 1)),
            out=self.dcl_t_q_to)





    def eval_dcl_t_s_fr_max(self):
        '''
        evaluate violation of dcl s_fr max
        compute penalty
        '''
        # todo - missing from data

    def eval_dcl_t_s_to_max(self):
        '''
        evaluate violation of dcl s_to max
        compute penalty
        '''
        # todo - missing from data





    def eval_xfr_t_tau_max(self):
        '''
        evaluate violation of xfr tau max
        '''

        numpy.subtract(
            self.xfr_t_tau, numpy.reshape(self.problem.xfr_tau_max, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_float)
        self.viol_xfr_t_tau_max = utils.get_max(self.xfr_t_float, idx_lists=[self.problem.xfr_uid, self.problem.t_num])

    def eval_xfr_t_tau_min(self):
        '''
        evaluate violation of xfr tau min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.xfr_tau_min, newshape=(self.problem.num_xfr, 1)), self.xfr_t_tau, out=self.xfr_t_float)
        self.viol_xfr_t_tau_min = utils.get_max(self.xfr_t_float, idx_lists=[self.problem.xfr_uid, self.problem.t_num])

    def proj_xfr_t_tau_max(self):
        '''
        project xfr tau to max
        '''

        numpy.minimum(
            self.xfr_t_tau, numpy.reshape(self.problem.xfr_tau_max, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_tau)

    def proj_xfr_t_tau_min(self):
        '''
        project xfr tau to min
        '''

        numpy.maximum(
            self.xfr_t_tau, numpy.reshape(self.problem.xfr_tau_min, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_tau)

    def eval_xfr_t_phi_max(self):
        '''
        evaluate violation of xfr phi max
        '''

        numpy.subtract(
            self.xfr_t_phi, numpy.reshape(self.problem.xfr_phi_max, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_float)
        self.viol_xfr_t_phi_max = utils.get_max(self.xfr_t_float, idx_lists=[self.problem.xfr_uid, self.problem.t_num])

    def eval_xfr_t_phi_min(self):
        '''
        evaluate violation of xfr phi min
        '''

        numpy.subtract(
            numpy.reshape(self.problem.xfr_phi_min, newshape=(self.problem.num_xfr, 1)), self.xfr_t_phi, out=self.xfr_t_float)
        self.viol_xfr_t_phi_min = utils.get_max(self.xfr_t_float, idx_lists=[self.problem.xfr_uid, self.problem.t_num])

    def proj_xfr_t_phi_max(self):
        '''
        project xfr phi to max
        '''

        numpy.minimum(
            self.xfr_t_phi, numpy.reshape(self.problem.xfr_phi_max, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_phi)

    def proj_xfr_t_phi_min(self):
        '''
        project xfr phi to min
        '''

        numpy.maximum(
            self.xfr_t_phi, numpy.reshape(self.problem.xfr_phi_min, newshape=(self.problem.num_xfr, 1)), out=self.xfr_t_phi)

    def eval_acl_t_u_su(self):
        '''
        evaluate acl su, checking if allowed, and costs
        '''

        if self.config['acl_switch_up_allowed']:
            self.acl_t_int[:] = 0
            self.viol_acl_t_u_su_max = utils.get_max(self.acl_t_int, idx_lists=[self.problem.acl_uid, self.problem.t_num])
        self.acl_t_int[:] = numpy.diff(
            self.acl_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.acl_u_on_0, newshape=(self.problem.num_acl, 1)))
        numpy.maximum(self.acl_t_int, 0, out=self.acl_t_int)
        if not self.config['acl_switch_up_allowed']:
            self.viol_acl_t_u_su_max = utils.get_max(self.acl_t_int, idx_lists=[self.problem.acl_uid, self.problem.t_num])
        self.sum_acl_t_u_su = numpy.sum(self.acl_t_int)
        numpy.multiply(
            numpy.reshape(self.problem.acl_c_su, newshape=(self.problem.num_acl, 1)), self.acl_t_int, out=self.acl_t_float)
        self.sum_acl_t_z_su = numpy.sum(self.acl_t_float)

    def eval_acl_t_u_sd(self):
        '''
        evaluate acl sd, checking if allowed, and costs
        '''

        if self.config['acl_switch_dn_allowed']:
            self.acl_t_int[:] = 0
            self.viol_acl_t_u_sd_max = utils.get_max(self.acl_t_int, idx_lists=[self.problem.acl_uid, self.problem.t_num])
        self.acl_t_int[:] = numpy.diff(
            self.acl_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.acl_u_on_0, newshape=(self.problem.num_acl, 1)))
        numpy.negative(self.acl_t_int, out=self.acl_t_int)
        numpy.maximum(self.acl_t_int, 0, out=self.acl_t_int)
        if not self.config['acl_switch_dn_allowed']:
            self.viol_acl_t_u_sd_max = utils.get_max(self.acl_t_int, idx_lists=[self.problem.acl_uid, self.problem.t_num])
        self.sum_acl_t_u_sd = numpy.sum(self.acl_t_int)
        numpy.multiply(
            numpy.reshape(self.problem.acl_c_sd, newshape=(self.problem.num_acl, 1)), self.acl_t_int, out=self.acl_t_float)
        self.sum_acl_t_z_sd = numpy.sum(self.acl_t_float)

    def eval_xfr_t_u_su(self):
        '''
        evaluate xfr su, checking if allowed, and costs
        '''

        if self.config['xfr_switch_up_allowed']:
            self.xfr_t_int[:] = 0
            self.viol_xfr_t_u_su_max = utils.get_max(self.xfr_t_int, idx_lists=[self.problem.xfr_uid, self.problem.t_num])
        self.xfr_t_int[:] = numpy.diff(
            self.xfr_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.xfr_u_on_0, newshape=(self.problem.num_xfr, 1)))
        numpy.maximum(self.xfr_t_int, 0, out=self.xfr_t_int)
        if not self.config['xfr_switch_up_allowed']:
            self.viol_xfr_t_u_su_max = utils.get_max(self.xfr_t_int, idx_lists=[self.problem.xfr_uid, self.problem.t_num])
        self.sum_xfr_t_u_su = numpy.sum(self.xfr_t_int)
        numpy.multiply(
            numpy.reshape(self.problem.xfr_c_su, newshape=(self.problem.num_xfr, 1)), self.xfr_t_int, out=self.xfr_t_float)
        self.sum_xfr_t_z_su = numpy.sum(self.xfr_t_float)

    def eval_xfr_t_u_sd(self):
        '''
        evaluate xfr sd, checking if allowed, and costs
        '''

        if self.config['xfr_switch_dn_allowed']:
            self.xfr_t_int[:] = 0
            self.viol_xfr_t_u_sd_max = utils.get_max(self.xfr_t_int, idx_lists=[self.problem.xfr_uid, self.problem.t_num])
        self.xfr_t_int[:] = numpy.diff(
            self.xfr_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.xfr_u_on_0, newshape=(self.problem.num_xfr, 1)))
        numpy.negative(self.xfr_t_int, out=self.xfr_t_int)
        numpy.maximum(self.xfr_t_int, 0, out=self.xfr_t_int)
        if not self.config['xfr_switch_dn_allowed']:
            self.viol_xfr_t_u_sd_max = utils.get_max(self.xfr_t_int, idx_lists=[self.problem.xfr_uid, self.problem.t_num])
        self.sum_xfr_t_u_sd = numpy.sum(self.xfr_t_int)
        numpy.multiply(
            numpy.reshape(self.problem.xfr_c_sd, newshape=(self.problem.num_xfr, 1)), self.xfr_t_int, out=self.xfr_t_float)
        self.sum_xfr_t_z_sd = numpy.sum(self.xfr_t_float)


    def eval_acl_t_p_q_fr_to(self):
        '''
        evaluate acl p/q fr/to
        '''

        # v^2 terms
        numpy.power(self.bus_t_v[self.problem.acl_fbus, :], 2, out=self.acl_t_float_1)
        numpy.power(self.bus_t_v[self.problem.acl_tbus, :], 2, out=self.acl_t_float_2)

        # v^2 terms into p/q fr/to
        # p_fr
        numpy.add(self.problem.acl_g_sr, self.problem.acl_g_fr, out=self.acl_float)
        numpy.multiply(numpy.reshape(self.acl_float, newshape=(self.problem.num_acl, 1)), self.acl_t_float_1, out=self.acl_t_p_fr)
        # q_fr
        numpy.multiply(self.problem.acl_b_ch, 0.5, out=self.acl_float)
        numpy.add(self.problem.acl_b_fr, self.acl_float, out=self.acl_float)
        numpy.add(self.problem.acl_b_sr, self.acl_float, out=self.acl_float)
        numpy.negative(self.acl_float, out=self.acl_float)
        numpy.multiply(numpy.reshape(self.acl_float, newshape=(self.problem.num_acl, 1)), self.acl_t_float_1, out=self.acl_t_q_fr)
        # p_to
        numpy.add(self.problem.acl_g_sr, self.problem.acl_g_to, out=self.acl_float)
        numpy.multiply(numpy.reshape(self.acl_float, newshape=(self.problem.num_acl, 1)), self.acl_t_float_2, out=self.acl_t_p_to)
        # q_to
        numpy.multiply(self.problem.acl_b_ch, 0.5, out=self.acl_float)
        numpy.add(self.problem.acl_b_to, self.acl_float, out=self.acl_float)
        numpy.add(self.problem.acl_b_sr, self.acl_float, out=self.acl_float)
        numpy.negative(self.acl_float, out=self.acl_float)
        numpy.multiply(numpy.reshape(self.acl_float, newshape=(self.problem.num_acl, 1)), self.acl_t_float_1, out=self.acl_t_q_to)

        # v cross terms
        numpy.subtract(self.bus_t_theta[self.problem.acl_fbus, :], self.bus_t_theta[self.problem.acl_tbus, :], out=self.acl_t_float) # angle diff theta-theta'
        numpy.cos(self.acl_t_float, out=self.acl_t_float_1) # cos
        numpy.sin(self.acl_t_float, out=self.acl_t_float_2) # sin
        numpy.multiply(self.bus_t_v[self.problem.acl_fbus, :], self.bus_t_v[self.problem.acl_tbus, :], out=self.acl_t_float) # v*v'
        numpy.multiply(self.acl_t_float_1, self.acl_t_float, out=self.acl_t_float_1) # cos*v*v'
        numpy.multiply(self.acl_t_float_2, self.acl_t_float, out=self.acl_t_float_2) # sin*v*v'

        # v cross terms into p/q fr/to
        # -g*cos in p fr/to
        numpy.multiply(numpy.reshape(self.problem.acl_g_sr, newshape=(self.problem.num_acl, 1)), self.acl_t_float_1, out=self.acl_t_float)
        numpy.subtract(self.acl_t_p_fr, self.acl_t_float, out=self.acl_t_p_fr)
        numpy.subtract(self.acl_t_p_to, self.acl_t_float, out=self.acl_t_p_to)
        # b*cos in q fr/to
        numpy.multiply(numpy.reshape(self.problem.acl_b_sr, newshape=(self.problem.num_acl, 1)), self.acl_t_float_1, out=self.acl_t_float)
        numpy.add(self.acl_t_q_fr, self.acl_t_float, out=self.acl_t_q_fr)
        numpy.add(self.acl_t_q_to, self.acl_t_float, out=self.acl_t_q_to)
        # -/+ b*sin in p fr/to
        numpy.multiply(numpy.reshape(self.problem.acl_b_sr, newshape=(self.problem.num_acl, 1)), self.acl_t_float_2, out=self.acl_t_float)
        numpy.subtract(self.acl_t_p_fr, self.acl_t_float, out=self.acl_t_p_fr)
        numpy.add(self.acl_t_p_to, self.acl_t_float, out=self.acl_t_p_to)
        # -/+ g*sin in q fr/to
        numpy.multiply(numpy.reshape(self.problem.acl_g_sr, newshape=(self.problem.num_acl, 1)), self.acl_t_float_2, out=self.acl_t_float)
        numpy.subtract(self.acl_t_q_fr, self.acl_t_float, out=self.acl_t_q_fr)
        numpy.add(self.acl_t_q_to, self.acl_t_float, out=self.acl_t_q_to)

        # multiply u_on
        numpy.multiply(self.acl_t_u_on, self.acl_t_p_fr, out=self.acl_t_p_fr)
        numpy.multiply(self.acl_t_u_on, self.acl_t_q_fr, out=self.acl_t_q_fr)
        numpy.multiply(self.acl_t_u_on, self.acl_t_p_to, out=self.acl_t_p_to)
        numpy.multiply(self.acl_t_u_on, self.acl_t_q_to, out=self.acl_t_q_to)

    def eval_xfr_t_p_q_fr_to(self):
        '''
        evaluate xfr p/q fr/to
        '''

        # v^2 terms
        numpy.power(self.bus_t_v[self.problem.xfr_fbus, :], 2, out=self.xfr_t_float_1)
        numpy.power(self.bus_t_v[self.problem.xfr_tbus, :], 2, out=self.xfr_t_float_2)
        numpy.power(self.xfr_t_tau, 2, out=self.xfr_t_float)
        numpy.divide(self.xfr_t_float_1, self.xfr_t_float, out=self.xfr_t_float_1)

        # v^2 terms into p/q fr/to
        # p_fr
        numpy.add(self.problem.xfr_g_sr, self.problem.xfr_g_fr, out=self.xfr_float)
        numpy.multiply(numpy.reshape(self.xfr_float, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_1, out=self.xfr_t_p_fr)
        # q_fr
        numpy.multiply(self.problem.xfr_b_ch, 0.5, out=self.xfr_float)
        numpy.add(self.problem.xfr_b_fr, self.xfr_float, out=self.xfr_float)
        numpy.add(self.problem.xfr_b_sr, self.xfr_float, out=self.xfr_float)
        numpy.negative(self.xfr_float, out=self.xfr_float)
        numpy.multiply(numpy.reshape(self.xfr_float, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_1, out=self.xfr_t_q_fr)
        # p_to
        numpy.add(self.problem.xfr_g_sr, self.problem.xfr_g_to, out=self.xfr_float)
        numpy.multiply(numpy.reshape(self.xfr_float, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_2, out=self.xfr_t_p_to)
        # q_to
        numpy.multiply(self.problem.xfr_b_ch, 0.5, out=self.xfr_float)
        numpy.add(self.problem.xfr_b_to, self.xfr_float, out=self.xfr_float)
        numpy.add(self.problem.xfr_b_sr, self.xfr_float, out=self.xfr_float)
        numpy.negative(self.xfr_float, out=self.xfr_float)
        numpy.multiply(numpy.reshape(self.xfr_float, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_1, out=self.xfr_t_q_to)

        # v cross terms
        numpy.subtract(self.bus_t_theta[self.problem.xfr_fbus, :], self.bus_t_theta[self.problem.xfr_tbus, :], out=self.xfr_t_float)
        numpy.subtract(self.xfr_t_float, self.xfr_t_phi, out=self.xfr_t_float) # angle diff theta-theta'-phi
        numpy.cos(self.xfr_t_float, out=self.xfr_t_float_1) # cos
        numpy.sin(self.xfr_t_float, out=self.xfr_t_float_2) # sin
        numpy.multiply(self.bus_t_v[self.problem.xfr_fbus, :], self.bus_t_v[self.problem.xfr_tbus, :], out=self.xfr_t_float)
        numpy.divide(self.xfr_t_float, self.xfr_t_tau, out=self.xfr_t_float) # v*v'/tau
        numpy.multiply(self.xfr_t_float_1, self.xfr_t_float, out=self.xfr_t_float_1) # cos*v*v'/tau
        numpy.multiply(self.xfr_t_float_2, self.xfr_t_float, out=self.xfr_t_float_2) # sin*v*v'/tau

        # v cross terms into p/q fr/to
        # -g*cos in p fr/to
        numpy.multiply(numpy.reshape(self.problem.xfr_g_sr, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_1, out=self.xfr_t_float)
        numpy.subtract(self.xfr_t_p_fr, self.xfr_t_float, out=self.xfr_t_p_fr)
        numpy.subtract(self.xfr_t_p_to, self.xfr_t_float, out=self.xfr_t_p_to)
        # b*cos in q fr/to
        numpy.multiply(numpy.reshape(self.problem.xfr_b_sr, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_1, out=self.xfr_t_float)
        numpy.add(self.xfr_t_q_fr, self.xfr_t_float, out=self.xfr_t_q_fr)
        numpy.add(self.xfr_t_q_to, self.xfr_t_float, out=self.xfr_t_q_to)
        # -/+ b*sin in p fr/to
        numpy.multiply(numpy.reshape(self.problem.xfr_b_sr, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_2, out=self.xfr_t_float)
        numpy.subtract(self.xfr_t_p_fr, self.xfr_t_float, out=self.xfr_t_p_fr)
        numpy.add(self.xfr_t_p_to, self.xfr_t_float, out=self.xfr_t_p_to)
        # -/+ g*sin in q fr/to
        numpy.multiply(numpy.reshape(self.problem.xfr_g_sr, newshape=(self.problem.num_xfr, 1)), self.xfr_t_float_2, out=self.xfr_t_float)
        numpy.subtract(self.xfr_t_q_fr, self.xfr_t_float, out=self.xfr_t_q_fr)
        numpy.add(self.xfr_t_q_to, self.xfr_t_float, out=self.xfr_t_q_to)

        # multiply u_on
        numpy.multiply(self.xfr_t_u_on, self.xfr_t_p_fr, out=self.xfr_t_p_fr)
        numpy.multiply(self.xfr_t_u_on, self.xfr_t_q_fr, out=self.xfr_t_q_fr)
        numpy.multiply(self.xfr_t_u_on, self.xfr_t_p_to, out=self.xfr_t_p_to)
        numpy.multiply(self.xfr_t_u_on, self.xfr_t_q_to, out=self.xfr_t_q_to)

    def eval_acl_t_s_max_fr_to(self):
        '''
        evaluate acl s max viol/penalty at fr/to
        '''

        # todo
        pass

    def eval_xfr_t_s_max_fr_to(self):
        '''
        evaluate xfr s max viol/penalty at fr/to
        '''

        # todo
        pass

    def eval_acl_t_u_su_sd_test(self):
        
        # 336 intervals
        # 2 weeks, 1 hour per interval
        # 1 week, 0.5 hour per interval
        # 3.5 days, 0.25 hour per interval
        # 100K branches, 336 intervals -> 268 MB, 0.03 sec
        print('performance test')
        num_acl = 100000
        num_t = 336
        start_time = time.time()
        acl_t_u_on = numpy.ones(shape=(num_acl, num_t), dtype=numpy.int8)
        end_time = time.time()
        print('acl_t_u_on numpy array memory info. shape: {}, size: {}, itemsize: {}, size*itemsize: {}, nbytes: {}'.format(
            acl_t_u_on.shape,
            acl_t_u_on.size,
            acl_t_u_on.itemsize,
            acl_t_u_on.size *
            acl_t_u_on.itemsize,
            acl_t_u_on.nbytes))
        print('time: {}'.format(end_time - start_time))
        start_time = time.time()
        acl_t_p = numpy.ones(shape=(num_acl, num_t), dtype=numpy.float)
        end_time = time.time()
        print('acl_t_p numpy array memory info. shape: {}, size: {}, itemsize: {}, size*itemsize: {}, nbytes: {}'.format(
            acl_t_p.shape,
            acl_t_p.size,
            acl_t_p.itemsize,
            acl_t_p.size *
            acl_t_p.itemsize,
            acl_t_p.nbytes))
        print('time: {}'.format(end_time - start_time))
        start_time = time.time()
        acl_t_u_su = numpy.diff(acl_t_u_on, n=1, axis=1)
        end_time = time.time()
        print('su time diff: {}'.format(end_time - start_time))
        acl_int = numpy.zeros(shape=(num_acl, ), dtype=numpy.int8)
        start_time = time.time()
        for t in range(num_t - 1):
            numpy.subtract(acl_t_u_on[:, t+1], acl_t_u_on[:, t], out=acl_int)
        end_time = time.time()
        print('su time loop: {}'.format(end_time - start_time))