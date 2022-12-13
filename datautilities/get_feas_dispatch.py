import gurobipy
import numpy

def get_feas_dispatch(data):

    output = {}
    m = Model()
    m.set_env()
    m.set_data(data)
    m.params['min_infeasibility'] = True
    m.params['min_distance'] = False
    m.make_opt_model()
    m.opt_model.optimize()
    output['model_status'] = m.opt_model.status
    if m.opt_model.status == gurobipy.GRB.OPTIMAL:
        output['success'] = True
        m.get_sol()
        m.get_viols()
        output['j_t_p_on'] = m.sol_j_t_p_on
        output['j_t_q'] = m.sol_j_t_q
        output['viols'] = m.viols
        if m.num_viols == 0:
            m.params['min_infeasibility'] = False
            m.params['min_distance'] = True
            m.make_opt_model()
            m.opt_model.optimize()
            output['model_status'] = m.opt_model.status
            if m.opt_model.status == gurobipy.GRB.OPTIMAL:
                m.get_sol()
                m.get_viols()
                output['j_t_p_on'] = m.sol_j_t_p_on
                output['j_t_q'] = m.sol_j_t_q
                output['viols'] = m.viols
            else:
                output['success'] = False
    else:
        output['success'] = False
    return(output)

class Model(object):

    def __init__(self):

        self.params = {
            'min_infeasibility': True,
            'min_distance': False}

    def set_env(self, env=None):

        if env is None:
            self.env = env
        else:
            self.env = gurobipy.Env()

    def set_data(self, data):
        '''
        data includes
        time_eq_tol
        t_d
        j_uid (for diagnosis of errors)
        j_u_on_init
        j_p_init
        j_q_init
        j_p_ru_max
        j_p_rd_max
        j_p_su_ru_max
        j_p_sd_rd_max
        j_t_u_on
        j_t_p_on_max
        j_t_p_on_min
        j_t_q_max
        j_t_q_min
        j_t_supc
        j_t_sdpc
        j_p_q_ineq
        j_p_q_eq
        j_b
        j_bmax
        j_bmin
        j_q0
        j_qmax0
        j_qmin0
        '''

        self.time_eq_tol = data['time_eq_tol']
        self.t_d = numpy.array(data['t_d'], dtype=float)
        self.num_t = self.t_d.size
        self.j_uid = numpy.array(data['j_uid'], dtype=str)
        self.num_j = self.j_uid.size
        self.j_u_on_init = numpy.array(data['j_u_on_init'], dtype=int)
        self.j_p_init = numpy.array(data['j_p_init'], dtype=float)
        self.j_q_init = numpy.array(data['j_q_init'], dtype=float)
        self.j_p_ru_max = numpy.array(data['j_p_ru_max'], dtype=float)
        self.j_p_rd_max = numpy.array(data['j_p_rd_max'], dtype=float)
        self.j_p_su_ru_max = numpy.array(data['j_p_su_ru_max'], dtype=float)
        self.j_p_sd_rd_max = numpy.array(data['j_p_sd_rd_max'], dtype=float)
        self.j_t_u_on = numpy.array(data['j_t_u_on'], dtype=int).reshape((self.num_j, self.num_t))
        self.j_t_p_on_max = numpy.array(data['j_t_p_on_max'], dtype=float).reshape((self.num_j, self.num_t))
        self.j_t_p_on_min = numpy.array(data['j_t_p_on_min'], dtype=float).reshape((self.num_j, self.num_t))
        self.j_t_q_max = numpy.array(data['j_t_q_max'], dtype=float).reshape((self.num_j, self.num_t))
        self.j_t_q_min = numpy.array(data['j_t_q_min'], dtype=float).reshape((self.num_j, self.num_t))
        self.j_t_supc = data['j_t_supc']
        self.j_t_sdpc = data['j_t_sdpc']
        self.j_p_q_ineq = data['j_p_q_ineq']
        self.j_p_q_eq = data['j_p_q_eq']
        self.j_b = data['j_b']
        self.j_bmax = data['j_bmax']
        self.j_bmin = data['j_bmin']
        self.j_q0 = data['j_q0']
        self.j_qmax0 = data['j_qmax0']
        self.j_qmin0 = data['j_qmin0']

        self.t_end_time = numpy.cumsum(self.t_d)
        self.t_start_time = numpy.zeros(shape=(self.num_t, ), dtype=float)
        self.t_start_time[1:self.num_t] = self.t_end_time[0:(self.num_t - 1)]
        self.t_mid_time = 0.5 * self.t_start_time + 0.5 * self.t_end_time

        # todo - try xrange instead of range if there is an issue with model construction time
        
        # set default values for other things we might need

        # compute u_su/u_sd
        self.j_t_u_diff = numpy.diff(
            self.j_t_u_on, axis=1, prepend=numpy.reshape(self.j_u_on_init, newshape=(self.num_j, 1)))
        self.j_t_u_su = numpy.maximum(self.j_t_u_diff, 0)
        self.j_t_u_sd = numpy.minimum(self.j_t_u_diff, 0)
        self.j_t_u_sd = numpy.negative(self.j_t_u_sd)
        
        # modify pmax/pmin given u_on
        self.j_t_p_on_max = numpy.multiply(self.j_t_u_on, self.j_t_p_on_max)
        self.j_t_p_on_min = numpy.multiply(self.j_t_u_on, self.j_t_p_on_min)

        # determine supc and sdpc p values
        self.j_t_p_su = numpy.zeros(shape=(self.num_j, self.num_t), dtype=float)
        self.j_t_p_sd = numpy.zeros(shape=(self.num_j, self.num_t), dtype=float)
        nz = numpy.nonzero(self.j_t_u_su)
        for i in range(nz[0].size):
            j = nz[0][i]
            t = nz[1][i]
            for k in self.j_t_supc[j][t]:
                self.j_t_p_su[j][k[0]] = k[1]
        nz = numpy.nonzero(self.j_t_u_sd)
        for i in range(nz[0].size):
            j = nz[0][i]
            t = nz[1][i]
            for k in self.j_t_sdpc[j][t]:
                self.j_t_p_sd[j][k[0]] = k[1]

        # determine u_onsusdpc
        self.j_t_u_onsusdpc = numpy.array(self.j_t_u_on, dtype=int)
        self.j_t_u_onsusdpc[self.j_t_p_su > 0.0] = 1
        self.j_t_u_onsusdpc[self.j_t_p_sd > 0.0] = 1

        # modify qmax/qmin given u_onsusdpc
        self.j_t_q_max = numpy.multiply(self.j_t_u_onsusdpc, self.j_t_q_max)
        self.j_t_q_min = numpy.multiply(self.j_t_u_onsusdpc, self.j_t_q_min)

        # todo - p-q linking constraints

    def make_opt_model(self):
        '''
        make a model in the Gurobi API
        future - use other APIs
        '''

        self.opt_model = gurobipy.Model()
        self.add_vars()
        self.add_constrs()
        self.add_obj()

    def add_vars(self):

        self.add_j_t_p_on()
        # self.add_j_t_p()
        self.add_j_t_q()
        if self.params['min_infeasibility']:
            self.add_j_t_p_ru_viol()
            self.add_j_t_p_rd_viol()
            self.add_j_t_q_over_viol()
            self.add_j_t_q_under_viol()
    
    def add_constrs(self):
        '''
        '''

        # self.add_j_t_p_def()
        self.add_j_t_p_ru_constr()
        self.add_j_t_p_rd_constr()
        self.add_j_t_q_leq_constr()
        self.add_j_t_q_geq_constr()
        self.add_j_t_q_eq_constr()
        
    def add_obj(self):

        if self.params['min_infeasibility']:
            self.add_infeas_obj()
        if self.params['min_distance']:
            self.add_distance_obj()

    def get_sol(self):
        
        self.get_sol_j_t_p_on()
        self.get_sol_j_t_q()

    def add_j_t_p_on(self):

        self.j_t_p_on = [
            [self.opt_model.addVar(
                lb=self.j_t_p_on_min[j,t], ub=self.j_t_p_on_max[j,t],
                name='j_t_p_on[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    # def add_j_t_p(self):
    #     self.j_t_p = [
    #         [self.opt_model.addVar(
    #             lb=-gurobipy.GRB.INFINITY, ub=gurobipy.GRB.INFINITY,
    #             name='j_t_p[{},{}]'.format(j,t))
    #          for t in range(self.num_t)]
    #         for j in range(self.num_j)]

    def add_j_t_p_ru_viol(self):

        self.j_t_p_ru_viol = [
            [self.opt_model.addVar(
                name='j_t_p_ru_viol[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_p_rd_viol(self):

        self.j_t_p_rd_viol = [
            [self.opt_model.addVar(
                name='j_t_p_rd_viol[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_q_over_viol(self):
        '''
        '''

        self.j_t_q_over_viol = {
            j: [self.opt_model.addVar(
                name='j_t_q_over_viol[{},{}]'.format(j,t))
                for t in range(self.num_t)]
            for j in range(self.num_j)
            if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)}
        
    def add_j_t_q_under_viol(self):
        '''
        '''

        self.j_t_q_under_viol = {
            j: [self.opt_model.addVar(
                name='j_t_q_under_viol[{},{}]'.format(j,t))
                for t in range(self.num_t)]
            for j in range(self.num_j)
            if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)}
                
    def add_j_t_q(self):

        self.j_t_q = [
            [self.opt_model.addVar(
                lb=self.j_t_q_min[j,t], ub=self.j_t_q_max[j,t],
                name='j_t_q[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    # def add_j_t_p_def(self):
    #     self.j_t_p_def = [
    #         [self.opt_model.addConstr(
    #             lhs=self.j_t_p[j][t],
    #             sense=gurobipy.GRB.EQUAL,
    #             rhs=(self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]),
    #             name='j_t_p_def[{},{}]'.format(j,t))
    #          for t in range(self.num_t)]
    #         for j in range(self.num_j)]

    def add_j_t_p_ru_constr(self):

        self.j_t_p_ru_constr = [
            [self.opt_model.addConstr(
                lhs=(
                    (self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]) -
                    ((self.j_t_p_on[j][t-1] + self.j_t_p_su[j,t-1] + self.j_t_p_sd[j,t-1])
                     if (t > 0) else (self.j_p_init[j]))),
                sense=gurobipy.GRB.LESS_EQUAL,
                rhs=(
                    self.t_d[t] * (
                        self.j_p_ru_max[j] if (self.j_t_u_on[j,t] == 1 and self.j_t_u_su[j,t] == 0)
                        else self.j_p_su_ru_max[j]) +
                    (self.j_t_p_ru_viol[j][t] if self.params['min_infeasibility'] else 0.0)),
                name='j_t_p_ru_constr[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_p_rd_constr(self):

        self.j_t_p_rd_constr = [
            [self.opt_model.addConstr(
                lhs=(
                    (self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]) -
                    ((self.j_t_p_on[j][t-1] + self.j_t_p_su[j,t-1] + self.j_t_p_sd[j,t-1])
                     if (t > 0) else (self.j_p_init[j]))),
                sense=gurobipy.GRB.GREATER_EQUAL,
                rhs=(
                    -self.t_d[t] * (
                        self.j_p_rd_max[j] if (self.j_t_u_on[j,t] == 1)
                        else self.j_p_sd_rd_max[j]) -
                    (self.j_t_p_rd_viol[j][t] if self.params['min_infeasibility'] else 0.0)),
                name='j_t_p_rd_constr[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_q_leq_constr(self):
        '''
        '''

        self.j_t_q_leq_constr = {
            j: [self.opt_model.addConstr(
                lhs=self.j_t_q[j][t],
                sense=gurobipy.GRB.LESS_EQUAL,
                rhs=(
                    (self.j_qmax0[j] if self.j_t_u_onsusdpc[j][t] == 1 else 0.0) +
                    self.j_bmax[j] * (self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]) +
                    (self.j_t_q_over_viol[j][t] if self.params['min_infeasibility'] else 0.0)),
                name='j_t_q_leq_constr[{},{}]'.format(j,t))
                for t in range(self.num_t)]
            for j in range(self.num_j)
            if self.j_p_q_ineq[j] == 1}

    def add_j_t_q_geq_constr(self):
        '''
        '''

        self.j_t_q_geq_constr = {
            j: [self.opt_model.addConstr(
                lhs=self.j_t_q[j][t],
                sense=gurobipy.GRB.GREATER_EQUAL,
                rhs=(
                    (self.j_qmin0[j] if self.j_t_u_onsusdpc[j][t] == 1 else 0.0) +
                    self.j_bmin[j] * (self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]) -
                    (self.j_t_q_under_viol[j][t] if self.params['min_infeasibility'] else 0.0)),
                name='j_t_q_geq_constr[{},{}]'.format(j,t))
                for t in range(self.num_t)]
            for j in range(self.num_j)
            if self.j_p_q_ineq[j] == 1}

    def add_j_t_q_eq_constr(self):
        '''
        '''

        self.j_t_q_eq_constr = {
            j: [self.opt_model.addConstr(
                lhs=self.j_t_q[j][t],
                sense=gurobipy.GRB.EQUAL,
                rhs=(
                    (self.j_q0[j] if self.j_t_u_onsusdpc[j][t] == 1 else 0.0) +
                    self.j_b[j] * (self.j_t_p_on[j][t] + self.j_t_p_su[j,t] + self.j_t_p_sd[j,t]) +
                    (self.j_t_q_over_viol[j][t] if self.params['min_infeasibility'] else 0.0) -
                    (self.j_t_q_under_viol[j][t] if self.params['min_infeasibility'] else 0.0)),
                name='j_t_q_eq_constr[{},{}]'.format(j,t))
                for t in range(self.num_t)]
            for j in range(self.num_j)
            if self.j_p_q_eq[j] == 1}

    def add_infeas_obj(self):
        '''
        '''

        obj = gurobipy.LinExpr()
        obj += gurobipy.LinExpr(
            [self.t_d[t] for j in range(self.num_j) for t in range(self.num_t)],
            [self.j_t_p_ru_viol[j][t] for j in range(self.num_j) for t in range(self.num_t)])
        obj += gurobipy.LinExpr(
            [self.t_d[t] for j in range(self.num_j) for t in range(self.num_t)],
            [self.j_t_p_rd_viol[j][t] for j in range(self.num_j) for t in range(self.num_t)])
        obj += gurobipy.LinExpr(
            [self.t_d[t]
             for j in range(self.num_j) if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)
             for t in range(self.num_t)],
            [self.j_t_q_over_viol[j][t]
             for j in range(self.num_j) if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)
             for t in range(self.num_t)])
        obj += gurobipy.LinExpr(
            [self.t_d[t]
             for j in range(self.num_j) if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)
             for t in range(self.num_t)],
            [self.j_t_q_under_viol[j][t]
             for j in range(self.num_j) if (self.j_p_q_ineq[j] == 1 or self.j_p_q_eq[j] == 1)
             for t in range(self.num_t)])
        self.opt_model.setObjective(obj)

    def add_distance_obj(self):
        '''
        '''

        obj = sum(self.t_d[t] * (self.j_t_p_on[j][t] - self.j_p_init[j]) * (self.j_t_p_on[j][t] - self.j_p_init[j]) for j in range(self.num_j) for t in range(self.num_t)) + sum(self.t_d[t] * (self.j_t_q[j][t] - self.j_q_init[j]) * (self.j_t_q[j][t] - self.j_q_init[j]) for j in range(self.num_j) for t in range(self.num_t))
        # obj += gurobipy.QuadExpr(
        #     [self.t_d[t] for j in range(self.num_j) for t in range(self.num_t)],
        #     [self.
        self.opt_model.setObjective(obj)
        
    def get_sol_j_t_p_on(self):

        self.sol_j_t_p_on = [[self.j_t_p_on[j][t].x for t in range(self.num_t)] for j in range(self.num_j)]

    def get_sol_j_t_q(self):

        self.sol_j_t_q = [[self.j_t_q[j][t].x for t in range(self.num_t)] for j in range(self.num_j)]

    def get_viols(self):

        viol_nonzero = {}
        self.viols = viol_nonzero
        self.num_viols = sum(len(v) for k,v in self.viols.items())
