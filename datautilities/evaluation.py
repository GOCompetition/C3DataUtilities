'''

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
        self.set_temp_zero()
        #self.problem = problem
        #self.problem = arraydata.InputData()
        #self.solution = arraydata.OutputData()
        #self.

    def run(self):

        self.eval_sd_t_u_on_max()
        self.eval_sd_t_u_on_min()

    def set_problem(self, prob):

        # todo - might be more convenient to flatten the problem attributes
        self.problem = prob

    def set_solution(self, sol):

        # note these are not copies of the arrays
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

    def eval_sd_t_u_on_max(self):

        numpy.subtract(self.sd_t_u_on, self.problem.sd_t_u_on_max, out=self.sd_t_int)
        print('sd_t_u_on_max viol: {}'.format(utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])))
        # print(
        #     'sd_t_u_on. max: {}, min: {}'.format(
        #         numpy.amax(self.sd_t_u_on),
        #         numpy.amin(self.sd_t_u_on)))
        # print(
        #     'sd_t_u_on_max. max: {}, min: {}'.format(
        #         numpy.amax(self.problem.sd_t_u_on_max),
        #         numpy.amin(self.problem.sd_t_u_on_max)))
        #indices_max = numpy.argmax(self.sd_t_int)
        #val_max = self.sd_t_int[indices_max]
        #IDG1

    def eval_sd_t_u_on_min(self):

        numpy.subtract(self.problem.sd_t_u_on_min, self.sd_t_u_on, out=self.sd_t_int)
        print('sd_t_u_on_min viol: {}'.format(utils.get_max(self.sd_t_int, idx_lists=[self.problem.sd_uid, self.problem.t_num])))
        
    def eval_sd_t_u_su_sd(self):

        self.sd_t_int[:] = numpy.diff(self.sd_t_u_on, n=1, axis=1, prepend=self.problem.sd_u_on_0)
        numpy.maximum(self.sd_t_int, 0, out=self.sd_t_u_su)
        numpy.negative(self.sd_t_int, out=self.sd_t_int)
        numpy.maximum(self.sd_t_int, 0, out=self.sd_t_u_sd)
        print('sd_t_u_su: {}'.format(self.sd_t_u_su))
        print('sd_t_u_sd: {}'.format(self.sd_t_u_sd))
