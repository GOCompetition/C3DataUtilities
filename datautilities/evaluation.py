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
        self.eval_acl_t_u_su_sd()
        self.eval_acl_t_u_su_sd_test()

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
        
    def eval_acl_t_u_su_sd(self):

        # todo
        # self.acl_t_int[:] = numpy.diff(
        #     self.acl_t_u_on, n=1, axis=1, prepend=numpy.reshape(self.problem.acl_u_on_0, newshape=(self.problem.num_acl, 1)))
        # numpy.maximum(self.acl_t_int, 0, out=self.acl_t_int)
        # numpy.negative(self.sd_t_int, out=self.sd_t_int)
        # numpy.maximum(self.sd_t_int, 0, out=self.sd_t_u_sd)
        pass

    def eval_acl_t_u_su_sd_test(self):
        
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
        acl_t_u_su = numpy.diff(acl_t_u_on, n=1, axis=1)
        end_time = time.time()
        print('su time diff: {}'.format(end_time - start_time))
        acl_int = numpy.zeros(shape=(num_acl, ), dtype=numpy.int8)
        start_time = time.time()
        for t in range(num_t - 1):
            numpy.subtract(acl_t_u_on[:, t+1], acl_t_u_on[:, t], out=acl_int)
        end_time = time.time()
        print('su time loop: {}'.format(end_time - start_time))
