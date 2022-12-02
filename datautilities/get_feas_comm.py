import gurobipy
import numpy

def get_feas_comm(data):

    output = {}
    m = Model()
    m.set_env()
    m.set_data(data)
    m.make_opt_model()
    m.opt_model.optimize()
    output['model_status'] = m.opt_model.status
    if m.opt_model.status == gurobipy.GRB.OPTIMAL:
        output['success'] = True
        m.get_sol()
        m.get_viols()
        output['j_t_u_on'] = m.sol_j_t_u_on
        output['viols'] = m.viols
    else:
        output['success'] = False
    return(output)

class Model(object):

    def __init__(self):

        pass

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
        j_up_time_min
        j_down_time_min
        j_up_time_init
        j_down_time_init
        j_t_u_on_max
        j_t_u_on_min
        j_w_startups_max
        j_w_start_time
        j_w_end_time
        '''

        self.time_eq_tol = data['time_eq_tol']
        self.t_d = numpy.array(data['t_d'], dtype=float)
        self.num_t = self.t_d.size
        self.j_uid = numpy.array(data['j_uid'], dtype=str)
        self.num_j = self.j_uid.size
        self.j_u_on_init = numpy.array(data['j_u_on_init'], dtype=int)
        self.j_up_time_min = numpy.array(data['j_up_time_min'], dtype=float)
        self.j_down_time_min = numpy.array(data['j_down_time_min'], dtype=float)
        self.j_up_time_init = numpy.array(data['j_up_time_init'], dtype=float)
        self.j_down_time_init = numpy.array(data['j_down_time_init'], dtype=float)
        self.j_t_u_on_max = numpy.array(data['j_t_u_on_max'], dtype=int).reshape((self.num_j, self.num_t))
        self.j_t_u_on_min = numpy.array(data['j_t_u_on_min'], dtype=int).reshape((self.num_j, self.num_t))
        self.j_w_startups_max = [numpy.array(i, dtype=int) for i in data['j_w_startups_max']]
        self.j_num_w = numpy.array([i.size for i in self.j_w_startups_max], dtype=int)
        self.j_w_start_time = [numpy.array(i, dtype=float) for i in data['j_w_start_time']]
        self.j_w_end_time = [numpy.array(i, dtype=float) for i in data['j_w_end_time']]

        self.t_end_time = numpy.cumsum(self.t_d)
        self.t_start_time = numpy.zeros(shape=(self.num_t, ), dtype=float)
        self.t_start_time[1:self.num_t] = self.t_end_time[0:(self.num_t - 1)]
        self.t_mid_time = 0.5 * self.t_start_time + 0.5 * self.t_end_time

        # todo - try xrange instead of range if there is an issue with model construction time
        
        # set default values for start and end time indices
        # todo maybe many of these (and other) numpy arrays should just be lists
        self.j_mr_end_t = [0 for j in range(self.num_j)]
        self.j_out_end_t = [0 for j in range(self.num_j)]
        self.j_t_up_time_min_start_t = [[t for t in range(self.num_t)] for j in range(self.num_j)]
        self.j_t_down_time_min_start_t = [[t for t in range(self.num_t)] for j in range(self.num_j)]
        self.j_w_start_t = [[self.num_t for w in range(self.j_num_w[j])] for j in range(self.num_j)]
        self.j_w_end_t = [[self.num_t for w in range(self.j_num_w[j])] for j in range(self.num_j)]

        # update start and end time indices
        self.update_j_mr_out_end_t() # todo uncomment
        self.update_j_t_up_time_min_start_t()
        self.update_j_t_down_time_min_start_t()
        self.update_j_w_start_end_t()

    def update_j_mr_out_end_t(self):

        t_float = numpy.zeros(shape=(self.num_t, ), dtype=float)
        t_int = numpy.zeros(shape=(self.num_t, ), dtype=int)
        for j in range(self.num_j):
            if self.j_up_time_init[j] > 0.0:
                numpy.subtract(
                    self.j_up_time_min[j] - self.j_up_time_init[j] - self.time_eq_tol,
                    self.t_start_time, out=t_float)
                numpy.greater(t_float, 0.0, out=t_int)
                t_set = numpy.nonzero(t_int)[0]
                num_t = t_set.size
                if num_t > 0:
                    self.j_mr_end_t[j] = numpy.amax(t_set) + 1
            if self.j_down_time_init[j] > 0.0:
                numpy.subtract(
                    self.j_down_time_min[j] - self.j_down_time_init[j] - self.time_eq_tol,
                    self.t_start_time, out=t_float)
                numpy.greater(t_float, 0.0, out=t_int)
                t_set = numpy.nonzero(t_int)[0]
                num_t = t_set.size
                if num_t > 0:
                    self.j_out_end_t[j] = numpy.amax(t_set) + 1
            # if self.j_mr_end_t[j] > 0 and self.j_out_end_t[j] > 0:
            #     print('j_mr_out_end_t both > 0. j: {}, mr: {}, out: {}'.format(j, self.j_mr_out_end_t[j], self.j_out_end_t[j]))

    def update_j_t_up_time_min_start_t(self):

        #print('t_start_time: {}'.format(self.t_start_time))
        t_start_time_minus_min_up_time = numpy.zeros(shape=(self.num_t, ), dtype=float)
        j_up_time_min_with_tol = self.j_up_time_min - self.time_eq_tol
        for j in range(self.num_j):
            if self.j_up_time_min[j] <= 0.0:
                # should just be [t,t)
                for t in range(self.num_t):
                    self.j_t_up_time_min_start_t[j][t] = t
                continue
            numpy.subtract(self.t_start_time, j_up_time_min_with_tol[j], out=t_start_time_minus_min_up_time)
            t1 = 0
            t = 0
            self.j_t_up_time_min_start_t[j][t] = t1
            increasing_t = True
            # if j == 0:
            #     print('t_start_time: {}'.format(self.t_start_time))
            #     print('t_start_time_minus_min_up_time: {}'.format(t_start_time_minus_min_up_time))
            while True:
                # if j == 0:
                #     print('t1: {}, t: {}, increasing_t: {}, '.format(t1, t, increasing_t))
                if increasing_t:
                    t += 1
                    if t >= self.num_t:
                        break
                    if self.t_start_time[t1] > t_start_time_minus_min_up_time[t]:
                        self.j_t_up_time_min_start_t[j][t] = t1
                    else:
                        increasing_t = False
                else:
                    t1 += 1
                    if self.t_start_time[t1] > t_start_time_minus_min_up_time[t]: # note this should catch t1 == t
                        self.j_t_up_time_min_start_t[j][t] = t1
                        increasing_t = True
        # print('j_t_up_time_min_start_t[0]: {}'.format(self.j_t_up_time_min_start_t[0]))

    def update_j_t_down_time_min_start_t(self):

        t_start_time_minus_min_down_time = numpy.zeros(shape=(self.num_t, ), dtype=float)
        j_down_time_min_with_tol = self.j_down_time_min - self.time_eq_tol
        for j in range(self.num_j):
            if self.j_down_time_min[j] <= 0.0:
                # should just be [t,t)
                for t in range(self.num_t):
                    self.j_t_down_time_min_start_t[j][t] = t
                continue
            numpy.subtract(self.t_start_time, j_down_time_min_with_tol[j], out=t_start_time_minus_min_down_time)
            t1 = 0
            t = 0
            self.j_t_down_time_min_start_t[j][t] = t1
            increasing_t = True
            while True:
                if increasing_t:
                    t += 1
                    if t >= self.num_t:
                        break
                    if self.t_start_time[t1] > t_start_time_minus_min_down_time[t]:
                        self.j_t_down_time_min_start_t[j][t] = t1
                    else:
                        increasing_t = False
                else:
                    t1 += 1
                    if self.t_start_time[t1] > t_start_time_minus_min_down_time[t]: # note this should catch t1 == t
                        self.j_t_down_time_min_start_t[j][t] = t1
                        increasing_t = True

    def update_j_w_start_end_t(self):

        t_int_1 = numpy.zeros(shape=(self.num_t, ), dtype=int)
        t_int_2 = numpy.zeros(shape=(self.num_t, ), dtype=int)
        for j in range(self.num_j):
            for w in range(self.j_num_w[j]):
                a_start = self.j_w_start_time[j][w]
                a_end = self.j_w_end_time[j][w]
                numpy.less_equal(a_start - self.time_eq_tol, self.t_start_time, out=t_int_1)
                numpy.less(self.t_start_time, a_end - self.time_eq_tol, out=t_int_2)
                numpy.multiply(t_int_1, t_int_2, out=t_int_1)
                t_set = numpy.nonzero(t_int_1)[0]
                num_t = t_set.size
                if num_t > 0:
                    self.j_w_start_t[j][w] = numpy.amin(t_set)
                    self.j_w_end_t[j][w] = numpy.amax(t_set) + 1

    def make_opt_model(self):
        '''
        make a model in the Gurobi API
        future - use other APIs
        '''

        self.opt_model = gurobipy.Model()
        self.add_vars()
        self.add_constrs()

    def add_vars(self):

        self.add_j_t_u_on()
        self.add_j_t_u_su()
        self.add_j_t_u_sd()
        self.add_j_t_up_time_min_viol()
        self.add_j_t_down_time_min_viol()
        self.add_j_w_startups_max_viol()
    
    def add_constrs(self):
        '''
        '''

        self.add_j_t_su_sd_def()
        self.add_j_t_su_sd_le_1()
        self.add_j_t_up_time_min_constr()
        self.add_j_t_down_time_min_constr()
        self.add_j_w_startups_max_constr()

    def get_sol(self):
        
        self.get_sol_j_t_u_on()
        self.get_sol_j_t_up_time_min_viol()
        self.get_sol_j_t_down_time_min_viol()
        self.get_sol_j_w_startups_max_viol()

    def add_j_t_u_on(self):

        self.j_t_u_on = [
            [self.opt_model.addVar(
                lb=self.j_t_u_on_min[j,t], ub=self.j_t_u_on_max[j,t],
                vtype=gurobipy.GRB.BINARY, name='j_t_u_on[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]
        for j in range(self.num_j):
            if self.j_mr_end_t[j] > 0 and self.j_out_end_t[j] > 0:
                print('j: {}, uid: {}, mr_end_t: {}, out_end_t: {}'.format(j, self.j_uid[j], self.j_mr_end_t[j], self.j_out_end_t[j]))
            for t in range(self.j_mr_end_t[j]):
                self.j_t_u_on[j][t].lb = 1
                if self.j_t_u_on_max[j,t] < 1:
                    print('j: {}, uid: {}, t: {}, u_on_max: {}, mr_end_t: {}'.format(j, self.j_uid[j], t, self.j_t_u_on_max[j,t], self.j_mr_end_t[j]))
            for t in range(self.j_out_end_t[j]):
                self.j_t_u_on[j][t].ub = 0
                if self.j_t_u_on_min[j,t] > 0:
                    print('j: {}, uid: {}, t: {}, u_on_min: {}, out_end_t: {}'.format(j, self.j_uid[j], t, self.j_t_u_on_min[j,t], self.j_out_end_t[j]))
        # note the feasibility checks here are now also handled in validation outside of the MIP model

    def add_j_t_u_su(self):

        self.j_t_u_su = [
            [self.opt_model.addVar(vtype=gurobipy.GRB.BINARY, name='j_t_u_su[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_u_sd(self):

        self.j_t_u_sd = [
            [self.opt_model.addVar(vtype=gurobipy.GRB.BINARY, name='j_t_u_sd[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_up_time_min_viol(self):

        self.j_t_up_time_min_viol = [
            [self.opt_model.addVar(obj=1.0, name='j_t_up_time_min_viol[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_down_time_min_viol(self):

        self.j_t_down_time_min_viol = [
            [self.opt_model.addVar(obj=1.0, name='j_t_down_time_min_viol[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_w_startups_max_viol(self):

        self.j_w_startups_max_viol = [
            [self.opt_model.addVar(obj=1.0, name='j_w_startups_max_viol[{},{}]'.format(j,w))
             for w in range(self.j_num_w[j])]
            for j in range(self.num_j)]

    def add_j_t_su_sd_def(self):

        self.j_t_su_sd_def = [
            [self.opt_model.addConstr(
                lhs=(
                    self.j_t_u_on[j][t]
                    - (self.j_t_u_on[j][t-1] if t > 0 else self.j_u_on_init[j])
                    - self.j_t_u_su[j][t]
                    + self.j_t_u_sd[j][t]),
                sense=gurobipy.GRB.EQUAL, rhs=0.0, name='j_t_su_sd_def[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_su_sd_le_1(self):

        self.j_t_su_sd_le_1 = [
            [self.opt_model.addConstr(
                lhs=(self.j_t_u_su[j][t] + self.j_t_u_sd[j][t] - 1.0),
                sense=gurobipy.GRB.LESS_EQUAL, rhs=0.0, name='j_t_su_sd_le_1[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_up_time_min_constr(self):

        self.j_t_up_time_min_constr = [
            [self.opt_model.addConstr(
                lhs=(
                    self.j_t_u_sd[j][t]
                    + gurobipy.quicksum(
                        self.j_t_u_su[j][t1] for t1 in range(self.j_t_up_time_min_start_t[j][t], t))
                    - self.j_t_up_time_min_viol[j][t] - 1.0),
                sense=gurobipy.GRB.LESS_EQUAL, rhs=0.0, name='j_t_up_time_min_constr[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_t_down_time_min_constr(self):

        self.j_t_down_time_min_constr = [
            [self.opt_model.addConstr(
                lhs=(
                    self.j_t_u_su[j][t]
                    + gurobipy.quicksum(
                        self.j_t_u_sd[j][t1] for t1 in range(self.j_t_down_time_min_start_t[j][t], t))
                    - self.j_t_down_time_min_viol[j][t] - 1.0),
                sense=gurobipy.GRB.LESS_EQUAL, rhs=0.0, name='j_t_up_time_min_constr[{},{}]'.format(j,t))
             for t in range(self.num_t)]
            for j in range(self.num_j)]

    def add_j_w_startups_max_constr(self):

        # print('j_w_start_t: {}'.format(self.j_w_start_t))
        # print('j_w_end_t: {}'.format(self.j_w_end_t))
        # print('j_w_startups_max: {}'.format(self.j_w_startups_max))

        self.j_w_startups_max_constr = [
            [self.opt_model.addConstr(
                lhs=(
                    gurobipy.quicksum(
                        self.j_t_u_su[j][t1] for t1 in range(self.j_w_start_t[j][w], self.j_w_end_t[j][w]))
                    - self.j_w_startups_max_viol[j][w] - self.j_w_startups_max[j][w]),
                sense=gurobipy.GRB.LESS_EQUAL, rhs=0.0, name='j_w_startups_max_constr[{},{}]'.format(j,w))
             for w in range(self.j_num_w[j])]
            for j in range(self.num_j)]

    def get_sol_j_t_u_on(self):

        self.sol_j_t_u_on = [[self.j_t_u_on[j][t].x for t in range(self.num_t)] for j in range(self.num_j)]

    def get_sol_j_t_up_time_min_viol(self):

        self.sol_j_t_up_time_min_viol = [
            [self.j_t_up_time_min_viol[j][t].x for t in range(self.num_t)] for j in range(self.num_j)]

    def get_sol_j_t_down_time_min_viol(self):

        self.sol_j_t_down_time_min_viol = [
            [self.j_t_down_time_min_viol[j][t].x for t in range(self.num_t)] for j in range(self.num_j)]

    def get_sol_j_w_startups_max_viol(self):

        self.sol_j_w_startups_max_viol = [
            [self.j_w_startups_max_viol[j][w].x for w in range(self.j_num_w[j])] for j in range(self.num_j)]

    def get_viols(self):

        viol_nonzero = {}
        viol_nonzero['j_t_up_time_min'] = {
            (j,t): self.sol_j_t_up_time_min_viol[j][t]
            for j in range(self.num_j) for t in range(self.num_t)
            if self.sol_j_t_up_time_min_viol[j][t] > 0.0}
        viol_nonzero['j_t_down_time_min'] = {
            (j,t): self.sol_j_t_down_time_min_viol[j][t]
            for j in range(self.num_j) for t in range(self.num_t)
            if self.sol_j_t_down_time_min_viol[j][t] > 0.0}
        viol_nonzero['j_w_startups_max'] = {
            (j,w): self.sol_j_w_startups_max_viol[j][w]
            for j in range(self.num_j) for w in range(self.j_num_w[j])
            if self.sol_j_w_startups_max_viol[j][w] > 0.0}
        self.viols = viol_nonzero
