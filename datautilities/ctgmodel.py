'''
Evaluates the post-contingency AC branch apparent power flow limits
under the DC post-contingency model described in the formulation.

The main computation is the solution of a sequence of closely related
square symmetric nonsingular linear systems.
There is one such system for each time interval and each contingency.
The matrix of each of these systems is the negative admittance matrix
of the network of in service AC branches in a given time interval
and following a given contingency.
The right hand side is derived from the power injections from generators,
loads, and shunts at the buses in the pre-contingency solution,
together with a distributed slack to ensure DC lossless power balance,
along with adjustments from contingencies outaging transformers or
DC lines.

If each of the linear systems is formed and solved from scratch,
in one loop over intervals and contingencies, the evaluation takes a
very long time. This challenge is faced in commercial and academic
work on evaluating security constraints, and a number of technical
approaches have been developed or adapted from more general contexts
in order to handle this, including:
* line outage distribution factors (LODFs)
* partial matrix refactorization and factorization update/downdate
* Sherman-Morrison-Woodbury (SMW) identity for inverse of a matrix with a low rank update

This code primarily uses the SMW approach,
which is a generalization of LODFs to network
changes involving more than one branch,
but we did also consider theother approaches.
We draw ideas and inspiration from the following sources, and sources cited therein:

O. Alsac, B. Stott, and W. F. Tinney, "Sparsity-Oriented Compensation Methods for Modified Network Solutions", in IEEE Transactions on Power Apparatus and Systems, vol. PAS-102, no. 5, pp. 1050-1060, May 1983.

W. W. Hager. "Updating the Inverse of a Matrix", in SIAM Review, 31(2):221–239, 1989.

J. Guo, Y. Fu, Z. Li and M. Shahidehpour, "Direct Calculation of Line Outage Distribution Factors," in IEEE Transactions on Power Systems, vol. 24, no. 3, pp. 1633-1634, Aug. 2009.

S. M. Chan and V. Brandwajn. "Partial Matrix Refactorization," in IEEE Transactions on Power Systems, 1:193–199, 1986.

Y. Chen, A. Casto, F. Wang, Q. Wang, X. Wang, and J. Wan. "Improving Large Scale Day-Ahead Security Constrained Unit Commitment Performance," in IEEE Transactions on Power Systems, 31:4732–4743, 2016.

J. Holzer, Y. Chen, Z. Wu, F. Pan, A. Veeramany. "Fast Simultaneous Feasibility Test for Security Constrained Unit Commitment". Submitted to IEEE Trans. Pow. Sys. (2022). TechRxiv. Preprint. https://doi.org/10.36227/techrxiv.20280384.v1

J. Holzer, J. Cottam, J. Li, C. Xie, G. Kestor, J. Zucker, F. Pan, "Fast Evaluation of Security Constraints with Multiple Line Outage Contingencies", in prep.

J. Holzer, Y. Chen, F. Pan, E. Rothberg, A. Veeramany. "Fast Evaluation of Security Constraints in a Security Constrained Unit Commitment Algorithm", in FERC Technical Conference on Increasing Market and Planning Efficiency Through Improved Software, 2019. https://www.ferc.gov/sites/default/files/2020-09/W1-A-4-Holzer.pdf. [Online; accessed 7-March-2022].

F. Pan, Y. Chen, Y. Guan, J. Holzer, J. Ostrowski, E. Rothberg, A. Veeramany, J. Wan, Y. Yu. HIPPO: High-Performance Power-grid Optimization, ARPA-E HIPPO report, January 2021.

Y. Chen, F. Pan, J. Holzer, E. Rothberg, Y. Ma, and A. Veeramany, "A High PerformanceComputing Based Market Economics Driven Neighborhood Search and Polishing Algorithm for Security Constrained Unit Commitment", in IEEE Transactions on Power Systems, vol. 36, no. 1, pp. 292-302, Jan. 2021.

Y. Chen, F. Pan, J. Holzer, A. Veeramany, and Z. Wu, "On Improving Efficiency of Electricity Market Clearing Software with A Concurrent High Performance Computer Based Security Constrained Unit Commitment Solver", in IEEE PES General Meeting, 2021.
'''

import time, numpy, scipy, scipy.sparse, scipy.sparse.linalg
from datautilities import utils

# todo - refactor, with a class

@utils.timeit
def eval_post_contingency_model(sol_eval):
    '''
    loop over t
    * create and factor negative admittance matrix A_t[t]
    * evaluate base case flows p_t[t]
    * compute rank-1 adjustments w_tk[t,k], v_tk[t,k], for contingencies k
    * 
    '''

    # problem dimensions
    num_bus = sol_eval.problem.num_bus
    num_acl = sol_eval.problem.num_acl
    num_xfr = sol_eval.problem.num_xfr
    num_dcl = sol_eval.problem.num_dcl
    num_br = num_acl + num_xfr
    num_k = sol_eval.problem.num_k
    num_t = sol_eval.problem.num_t
    print('problem dimensions. bus: {}, acl: {}, xfr: {}, dcl: {}, k: {}, t: {}'.format(
        num_bus, num_acl, num_xfr, num_dcl, num_k, num_t))

    # choose a reference bus
    ref_bus = 0
    nonref_bus = numpy.array(list(range(ref_bus)) + list(range(ref_bus + 1, sol_eval.problem.num_bus)), dtype=int)

    # branch matrices
    nonref_bus_acl_inc = sol_eval.bus_acl_to_inj_mat - sol_eval.bus_acl_fr_inj_mat # inj_mat has -1.0, so (to - fr)
    nonref_bus_acl_inc = nonref_bus_acl_inc[nonref_bus, :]
    nonref_bus_xfr_inc = sol_eval.bus_xfr_to_inj_mat - sol_eval.bus_xfr_fr_inj_mat
    nonref_bus_xfr_inc = nonref_bus_xfr_inc[nonref_bus, :]
    nonref_bus_br_inc = scipy.sparse.hstack((nonref_bus_acl_inc, nonref_bus_xfr_inc))
    acl_b = numpy.array(sol_eval.problem.acl_b_sr, dtype=float)
    xfr_b = numpy.array(sol_eval.problem.xfr_b_sr, dtype=float)
    br_b = numpy.concatenate((acl_b, xfr_b))
    acl_s_max = numpy.array(sol_eval.problem.acl_s_max_ctg, dtype=float)
    xfr_s_max = numpy.array(sol_eval.problem.xfr_s_max_ctg, dtype=float)
    br_s_max = numpy.concatenate((acl_s_max, xfr_s_max))

    # static matrix A = -B = - M*Bsr*Mt on non-reference buses, generally symmetric nonsingular
    # usually positive definite but may be indefinite if some branches have X_sr < 0
    # if positive definite, using a Cholesky factorization instead of LU can improve run time
    start_time = time.time()
    a_mat = nonref_bus_br_inc.transpose().multiply(numpy.reshape(br_b, newshape=(num_br, 1)))
    a_mat = nonref_bus_br_inc.dot(a_mat)
    a_mat = a_mat.multiply(-1.0)
    end_time = time.time()
    print('construct static bus admittance matrix. time: {}'.format(end_time - start_time))

    # factor
    start_time = time.time()
    a_factors = scipy.sparse.linalg.splu(a_mat)
    end_time = time.time()
    print('factor static bus admittance matrix. time: {}'.format(end_time - start_time))

    # get AC branches going out of service in at least one contingency
    #acl_delta_k = numpy.array([
    acl_delta_k = numpy.array(sorted(list(set([
        sol_eval.problem.k_out_acl[k] for k in range(num_k) if sol_eval.problem.k_out_is_acl[k]]))), dtype=int)
    xfr_delta_k = numpy.array(sorted(list(set([
        sol_eval.problem.k_out_xfr[k] for k in range(num_k) if sol_eval.problem.k_out_is_xfr[k]]))), dtype=int)
    dcl_delta_k = numpy.array(sorted(list(set([
        sol_eval.problem.k_out_dcl[k] for k in range(num_k) if sol_eval.problem.k_out_is_dcl[k]]))), dtype=int)
    br_delta_k = numpy.concatenate((acl_delta_k, num_acl + xfr_delta_k))
    num_br_delta_k = br_delta_k.size
    num_acl_delta_k = acl_delta_k.size
    num_xfr_delta_k = xfr_delta_k.size
    num_dcl_delta_k = dcl_delta_k.size
    acl_delta_k_map = {acl_delta_k[i]:i for i in range(num_acl_delta_k)}
    dcl_delta_k_map = {dcl_delta_k[i]:i for i in range(num_dcl_delta_k)}
    xfr_delta_k_map = {xfr_delta_k[i]:i for i in range(num_xfr_delta_k)}
    k_out_is_acl_list = numpy.nonzero(sol_eval.problem.k_out_is_acl)[0]
    k_out_is_acl_acl_list = sol_eval.problem.k_out_acl[k_out_is_acl_list]
    k_out_is_acl_acl_delta_k_list = numpy.array([acl_delta_k_map[i] for i in k_out_is_acl_acl_list], dtype=int)
    k_out_is_dcl_list = numpy.nonzero(sol_eval.problem.k_out_is_dcl)[0]
    k_out_is_dcl_dcl_list = sol_eval.problem.k_out_dcl[k_out_is_dcl_list]
    k_out_is_dcl_dcl_delta_k_list = numpy.array([dcl_delta_k_map[i] for i in k_out_is_dcl_dcl_list], dtype=int)
    k_out_is_xfr_list = numpy.nonzero(sol_eval.problem.k_out_is_xfr)[0]
    k_out_is_xfr_xfr_list = sol_eval.problem.k_out_xfr[k_out_is_xfr_list]
    k_out_is_xfr_xfr_delta_k_list = numpy.array([xfr_delta_k_map[i] for i in k_out_is_xfr_xfr_list], dtype=int)
    br_acl_delta_k_out_idx_lists = (acl_delta_k, numpy.arange(num_acl_delta_k, dtype=int))
    br_xfr_delta_k_out_idx_lists = (num_acl + xfr_delta_k, numpy.arange(num_xfr_delta_k, dtype=int))
    print('contingency delta branches. acl: {}, xfr: {}, dcl: {}'.format(
        num_acl_delta_k, num_xfr_delta_k, num_dcl_delta_k))

    # collect bus-t injections from producers, consumers, and shunts:
    # p_inj = p_pr - p_cs - p_sh
    start_time = time.time()
    sol_eval.bus_t_float[:] = 0.0
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_sd_inj_mat, sol_eval.sd_t_p, out=sol_eval.bus_t_float)
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_sh_inj_mat, sol_eval.sh_t_p, out=sol_eval.bus_t_float)
    # subtract the distributed slack
    t_p_sl = numpy.sum(sol_eval.bus_t_float, axis=0)
    numpy.subtract(
        sol_eval.bus_t_float, (1.0 / num_bus) * numpy.reshape(t_p_sl, newshape=(1, num_t)), out=sol_eval.bus_t_float)
    # subtract pre-contingency power absorption due to DC line flow
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_dcl_fr_inj_mat, sol_eval.dcl_t_p, out=sol_eval.bus_t_float)
    numpy.negative(sol_eval.dcl_t_p, out=sol_eval.dcl_t_float)
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_dcl_to_inj_mat, sol_eval.dcl_t_float, out=sol_eval.bus_t_float)
    # subtract pre-contingency power absorption due to transformer phase difference
    numpy.multiply(numpy.reshape(xfr_b, newshape=(num_xfr, 1)), sol_eval.xfr_t_phi, out=sol_eval.xfr_t_float)
    numpy.multiply(sol_eval.xfr_t_u_on, sol_eval.xfr_t_float, out=sol_eval.xfr_t_float)
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_xfr_fr_inj_mat, sol_eval.xfr_t_float, out=sol_eval.bus_t_float)
    numpy.negative(sol_eval.xfr_t_float, out=sol_eval.xfr_t_float)
    utils.csr_mat_vec_add_to_vec(sol_eval.bus_xfr_to_inj_mat, sol_eval.xfr_t_float, out=sol_eval.bus_t_float)
    # todo - check sign on terms, especially transformer
    end_time = time.time()
    print('construct bus,t-indexed right hand side. time: {}'.format(end_time - start_time))

    # solve for bus-t theta in the base case
    start_time = time.time()
    sol_eval.bus_t_float_1[:] = 0.0
    sol_eval.bus_t_float_1[nonref_bus, :] = a_factors.solve(sol_eval.bus_t_float[nonref_bus, :])
    end_time = time.time()
    print('solve for base case bus,t-indexed theta. time: {}'.format(end_time - start_time))

    #br_t_u = numpy.concatenate((sol_eval.acl_t_u_on, sol_eval.xfr_t_u_on), axis=0)
    #br_t_phi
    acl_phi = numpy.zeros(shape=(num_acl, ), dtype=float)
    m_acl_k = nonref_bus_br_inc[:, acl_delta_k].toarray()
    m_xfr_k = nonref_bus_br_inc[:, xfr_delta_k].toarray()
    #mw_k = numpy.zeros(shape=(num_bus - 1, num_br_delta_k), dtype=float)
    w_acl_k = numpy.zeros(shape=(num_bus - 1, num_acl_delta_k), dtype=float)
    w_xfr_k = numpy.zeros(shape=(num_bus - 1, num_xfr_delta_k), dtype=float)

    bus_rhs = numpy.zeros(shape=(num_bus - 1, ), dtype=float) # main term of RHS
    bus_theta = numpy.zeros(shape=(num_bus - 1, ), dtype=float) # main term
    bus_acl_delta_k_float = numpy.zeros(shape=(num_bus - 1, num_acl_delta_k), dtype=float)
    bus_dcl_delta_k_float = numpy.zeros(shape=(num_bus - 1, num_dcl_delta_k), dtype=float)
    bus_xfr_delta_k_float = numpy.zeros(shape=(num_bus - 1, num_xfr_delta_k), dtype=float)

    br_p = numpy.zeros(shape=(num_br, ), dtype=float) # main term
    br_bool = numpy.zeros(shape=(num_br, ), dtype=bool)
    br_float = numpy.zeros(shape=(num_br, ), dtype=float)
    br_float_1 = numpy.zeros(shape=(num_br, ), dtype=float)
    br_acl_delta_k_float = numpy.zeros(shape=(num_br, num_acl_delta_k), dtype=float)
    br_dcl_delta_k_float = numpy.zeros(shape=(num_br, num_dcl_delta_k), dtype=float)
    br_xfr_delta_k_float = numpy.zeros(shape=(num_br, num_xfr_delta_k), dtype=float)

    acl_delta_k_float = numpy.zeros(shape=(num_acl_delta_k, ), dtype=float)
    dcl_delta_k_float = numpy.zeros(shape=(num_dcl_delta_k, ), dtype=float)
    xfr_delta_k_float = numpy.zeros(shape=(num_xfr_delta_k, ), dtype=float)

    # keep track of run time of certain phases of the loop over t
    get_time_varying_branch_characteristics_time = 0.0
    construct_a_t_time = 0.0
    factor_a_t_time = 0.0
    compute_w_time = 0.0
    compute_v_time = 0.0 # includes v_inv
    compute_bus_theta_time = 0.0
    compute_br_p_time = 0.0
    apply_w_v_wt_time = 0.0
    compute_br_acl_delta_k_p_delta_time = 0.0
    filter_branches_time = 0.0
    compute_br_acl_delta_k_p_time = 0.0
    compute_br_acl_delta_k_s_over_time = 0.0
    zero_out_acl_delta_k_time = 0.0
    get_max_br_acl_delta_k_s_over_time = 0.0
    compute_br_acl_delta_k_z_time = 0.0
    collect_penalties_into_obj_array_time = 0.0

    # largest violations
    viol = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_acl_acl_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_xfr_acl_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_acl_dcl_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_xfr_dcl_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_acl_xfr_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)
    max_viol_xfr_xfr_delta_k = utils.make_empty_viol(val=0.0, num_indices=3)

    t_computation_time = {}

    br_use_where = True

    for t in range(num_t):

        br_acl_delta_k_float[:] = 0.0
        acl_delta_k_float[:] = 0.0

        # todo skip certain computations if there was no change from the previous t, i.e. ac br u_su/sd == 0

        # todo low rank update with respect to t, as in HIPPO/MISO paper
        # need to create test data with more line switching to test this sufficiently
        # e.g. ~ 10 to 100 switches per time interval, some connecting, some disconnecting

        t_start_time = time.time()

        # get some time-varying characteristics of branches from the base case solution
        start_time = time.time()
        xfr_phi = sol_eval.xfr_t_phi[:, t]
        br_phi = numpy.concatenate((acl_phi, xfr_phi))
        acl_u = sol_eval.acl_t_u_on[:, t]
        xfr_u = sol_eval.xfr_t_u_on[:, t]
        br_u = numpy.concatenate((acl_u, xfr_u))
        br_b_t = br_u * br_b
        acl_q_fr = sol_eval.acl_t_q_fr[:, t]
        xfr_q_fr = sol_eval.xfr_t_q_fr[:, t]
        br_q_fr = numpy.concatenate((acl_q_fr, xfr_q_fr))
        acl_q_to = sol_eval.acl_t_q_to[:, t]
        xfr_q_to = sol_eval.xfr_t_q_to[:, t]
        br_q_to = numpy.concatenate((acl_q_to, xfr_q_to))
        br_q = numpy.maximum(numpy.absolute(br_q_fr), numpy.absolute(br_q_to)) # no need to track which side is violated
        end_time = time.time()
        get_time_varying_branch_characteristics_time += (end_time - start_time)

        # form A_t
        start_time = time.time()
        a_mat_t = nonref_bus_br_inc.transpose().multiply(numpy.reshape(br_b_t, newshape=(num_br, 1)))
        a_mat_t = nonref_bus_br_inc.dot(a_mat_t)
        a_mat_t = a_mat_t.multiply(-1.0)
        end_time = time.time()
        construct_a_t_time += (end_time - start_time)

        # factor A_t
        start_time = time.time()
        a_factors_t = scipy.sparse.linalg.splu(a_mat_t)
        end_time = time.time()
        factor_a_t_time += (end_time - start_time)

        # solve with A_t for W_tk - this is expensive ~80 s
        # two ideas can improve this:
        # skipping updates if ac br u_su/sd == 0
        # applying low rank update technique to network changes with respect to t
        start_time = time.time()
        w_acl_k[:] = a_factors_t.solve(m_acl_k)
        w_xfr_k[:] = a_factors_t.solve(m_xfr_k)
        #w_k = a_factors_t.solve(m_k) # no in-place, creating w_k for each t (instead of w[:] = ..) is better
        #for k in range(sol_eval.problem.num_k):
        #    w[:, k] = bus_b_mat_factors.solve(m[:, k])
        end_time = time.time()
        compute_w_time += (end_time - start_time)
        
        # compute V_tk and inverses
        start_time = time.time()
        v_acl_k = (1.0 / acl_b[acl_delta_k]) + numpy.einsum('ij,ij->j', m_acl_k, w_acl_k)
        # v_acl_k should be nonzero so the following division should work
        # for contingencies k where the line going out of service is not already out of service in the base case,
        # we have the assumption that the network remains connected post-contingency,
        # so the post-contingency negative admittance matrix is nonsingular,
        # so the rank-1 update formula holds and the inner factor is nonzero.
        # for contingencies k where the line going out of service is already out of service in the base case,
        # the rank-1 update to the network amounts to putting the line in with its susceptance multiplied by -1.
        # we assume that the pre-contingency network is connected, and adding a line cannot disconnect it,
        # so the post-contingency network is connected.
        # the theoretical result that the negative admittance matrix on the non-reference buses resulting from a
        # connected network is nonsingular does not require that the branch reactances be positive
        # (or that they be negative).
        # if this step ever fails, we have some work to do.
        # todo catch this and ensure that it is not treated as a competitor error
        # and that it raises an issue for debugging.
        v_acl_k_inv = 1.0 / v_acl_k
        v_acl_k = v_acl_k * acl_u[acl_delta_k] # zero out v_acl_k from base case - this is not necessary
        # zero out v_acl_k_inv for any branches that are out of service due to pre-contingency state
        # this will zero out the delta contribution to the solved theta,
        # so the solved theta is that of the base case, as it should be
        v_acl_k_inv = v_acl_k_inv * acl_u[acl_delta_k]
        v_xfr_k = (1.0 / xfr_b[xfr_delta_k]) + numpy.einsum('ij,ij->j', m_xfr_k, w_xfr_k)
        v_xfr_k_inv = 1.0 / v_xfr_k
        v_xfr_k = v_xfr_k * xfr_u[xfr_delta_k]
        v_xfr_k_inv = v_xfr_k_inv * xfr_u[xfr_delta_k]
        end_time = time.time()
        compute_v_time += (end_time - start_time)

        # set RHS terms
        bus_rhs[:] = sol_eval.bus_t_float[nonref_bus, t]

        # compute terms in theta expression

        # solve for base case bus theta in the base case
        # There are no contingencies outaging no branches
        # every contingency outages exactly one branch
        # some branches might be outaged by more than one contingency - why though?
        start_time = time.time()
        bus_theta[:] = a_factors_t.solve(bus_rhs)
        end_time = time.time()
        compute_bus_theta_time += (end_time - start_time)

        # compute br p under no outages
        start_time = time.time()
        #numpy.multiply(nonref_bus_br_inc.transpose(), bus_acl_delta_k_float, out=br_acl_delta_k_float)
        br_p[:] = nonref_bus_br_inc.transpose().dot(bus_theta)
        numpy.subtract(br_p, br_phi, out=br_p)
        numpy.multiply(br_b_t, br_p, out=br_p)
        numpy.negative(br_p, out=br_p)
        end_time = time.time()
        compute_br_p_time += (end_time - start_time)

        # compute bus theta under ACL outages
        # main theta perturbation term for AC lines
        # this is somewhat expensive ~7 s
        # might be able to apply the idea on eliminating AC line computations that cannot possibly lead to violation
        start_time = time.time()
        w_acl_k_rhs = numpy.dot(w_acl_k.transpose(), bus_rhs)
        w_acl_k_rhs = v_acl_k_inv * w_acl_k_rhs
        bus_acl_delta_k_float[:] = w_acl_k * numpy.reshape(w_acl_k_rhs, newshape=(1, num_acl_delta_k)) #subtract this from A^-1 p
        end_time = time.time()
        apply_w_v_wt_time += (end_time - start_time)
        
        # compute AC branch flow deltas under ACL outages
        # this is somewhat expensive ~9 s
        # might be able to apply the idea on eliminating AC line computations that cannot possibly lead to violation
        # apply M, phi, B to get AC branch flows
        start_time = time.time()
        #numpy.multiply(nonref_bus_br_inc.transpose(), bus_acl_delta_k_float, out=br_acl_delta_k_float)
        br_acl_delta_k_float[:] = nonref_bus_br_inc.transpose().dot(bus_acl_delta_k_float)
        numpy.multiply(
            numpy.reshape(br_b_t, newshape=(num_br, 1)), br_acl_delta_k_float, out=br_acl_delta_k_float)
        # zero out br-acl-delta-k that are outaged
        # this is correct, but still need to do it again after adding
        # it is not necessary to do it here for correctness,
        # but ifwe do not do it here, then we lose much of the gain from filtering the delta terms
        # drops number of branches down from ~1700 (out of 3000) to ~40
        br_acl_delta_k_float[br_acl_delta_k_out_idx_lists] = 0.0
        end_time = time.time()
        compute_br_acl_delta_k_p_delta_time += (end_time - start_time)

        # before adding, eliminate entries that do not need to be added because they cannot exceed the limit
        # that could reduce the compute time (and memory use)
        # this appears to be the earliest we could do this
        start_time = time.time()
        if num_acl_delta_k > 0:
            numpy.amax(br_acl_delta_k_float, axis=1, out=br_float)
            numpy.amin(br_acl_delta_k_float, axis=1, out=br_float_1)
            numpy.add(br_p, br_float, out=br_float)
            numpy.add(br_p, br_float_1, out=br_float_1)
            numpy.absolute(br_float, out=br_float)
            numpy.absolute(br_float_1, out=br_float_1)
            numpy.maximum(br_float, br_float_1, out=br_float)
        else:
            br_float[:] = br_p
        numpy.power(br_float, 2, out=br_float)
        numpy.power(br_q, 2, out=br_float_1)
        numpy.add(br_float, br_float_1, out=br_float)
        numpy.power(br_float, 0.5, out=br_float)
        numpy.subtract(br_float, br_s_max, out=br_float)
        numpy.maximum(0.0, br_float, out=br_float)
        
        # do we want a list of nonzero indices?
        # or a boolean array with true at the nonzero indices and false at the others?
        numpy.greater(br_float, 0.0, out=br_bool)
        br_viol_list = numpy.nonzero(br_float)[0]
        num_br_viol_list = br_viol_list.size
        print('num AC branches with possible violations in ACL contingencies: {}'.format(num_br_viol_list))
        end_time = time.time()
        filter_branches_time += (end_time - start_time)

        # add br_p delta term from base case br_p to get post-k br_p - only on filtered branches
        start_time = time.time()
        numpy.add(
            numpy.reshape(br_p, newshape=(num_br, 1)), br_acl_delta_k_float, out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        end_time = time.time()
        compute_br_acl_delta_k_p_time += (end_time - start_time)



        # compute AC branch flow violations under ACL outages
        # this is expensive ~83 s but reduced hugely to about 2 or 3 s by
        # eliminating AC branch computations that cannot possibly lead to violation
        # as in HIPPO SFT
        # using that idea requires a couple of extra steps, including filtering the branches,
        # which take a few seconds.
        # but the time saved is typically much greater.
        # The benefit of this relies on the fact that usually, the number of branches that exceed their limit
        # in at least one contingency is very small
        # this in turn depends on enforcing the base case constraints,
        # but it should be noted that many branches will automatically be within their limits in the base case
        # as long as just a few critical ones are controlled.
        # this redundancy is critical to many security constraint evaluation and enforcement techniques.
        start_time = time.time()
        numpy.power(br_acl_delta_k_float, 2, out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        numpy.add(
            br_acl_delta_k_float, numpy.reshape(numpy.power(br_q, 2), newshape=(num_br, 1)),
            out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        numpy.power(br_acl_delta_k_float, 0.5, out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        numpy.subtract(
            br_acl_delta_k_float, numpy.reshape(br_s_max, newshape=(num_br, 1)), out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        numpy.maximum(0.0, br_acl_delta_k_float, out=br_acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        end_time = time.time()
        compute_br_acl_delta_k_s_over_time += (end_time - start_time)

        # zero out flows for branch-contingency pairs where the branch is out of service
        # may need to use this multiple times so time it - it should be trivial
        start_time = time.time()
        br_acl_delta_k_float[br_acl_delta_k_out_idx_lists] = 0.0
        end_time = time.time()
        zero_out_acl_delta_k_time += (end_time - start_time)

        # get worst violations under ACL outages
        start_time = time.time()
        viol = utils.get_max(
            br_acl_delta_k_float[0:num_acl, :],
            idx_lists=[sol_eval.problem.acl_uid, sol_eval.problem.acl_uid[acl_delta_k]])
        if viol['val'] > max_viol_acl_acl_delta_k['val']:
            viol['idx'][2] = t
            max_viol_acl_acl_delta_k = viol
        viol = utils.get_max(
            br_acl_delta_k_float[0:num_xfr, :],
            idx_lists=[sol_eval.problem.xfr_uid, sol_eval.problem.acl_uid[acl_delta_k]])
        if viol['val'] > max_viol_xfr_acl_delta_k['val']:
            viol['idx'][2] = t
            max_viol_xfr_acl_delta_k = viol
        end_time = time.time()
        get_max_br_acl_delta_k_s_over_time += (end_time - start_time)

        # compute AC branch flow penalties under ACL outages
        start_time = time.time()
        numpy.sum(br_acl_delta_k_float, axis=0, out=acl_delta_k_float,
            where=(numpy.reshape(br_bool, newshape=(num_br, 1)) if br_use_where else True))
        numpy.multiply(sol_eval.problem.c_s, acl_delta_k_float, out=acl_delta_k_float)
        end_time = time.time()
        compute_br_acl_delta_k_z_time += (end_time - start_time)

        # todo compute dcl rhs
        # todo compute xfr rhs and xfr perturbation
        
        # acl_delta_k_float, dcl_delta_k_float, and xfr_delta_k_float
        # have the total penalties for this t under ACL, DCL, and XFR outages
        # need to collect these into total penalty for this t under each contingency
        # goes into sol_eval.t_k_z (with minus sign)
        start_time = time.time()
        sol_eval.t_k_z[t, k_out_is_acl_list] = (-1.0) * acl_delta_k_float[k_out_is_acl_acl_delta_k_list]
        sol_eval.t_k_z[t, k_out_is_dcl_list] = (-1.0) * dcl_delta_k_float[k_out_is_dcl_dcl_delta_k_list]
        sol_eval.t_k_z[t, k_out_is_xfr_list] = (-1.0) * xfr_delta_k_float[k_out_is_xfr_xfr_delta_k_list]
        end_time = time.time()
        collect_penalties_into_obj_array_time += (end_time - start_time)

        t_end_time = time.time()
        t_computation_time[t] = t_end_time - t_start_time
        print('t: {}, time: {}, memory_info: {}'.format(t, t_computation_time[t], utils.get_memory_info()))

    # todo check result

    # todo
    # reduce as in HIPPO SFT
    # LHS : monitored branches (well, they are all monitored so this will not help)
    # RHS : injection buses (generators, loads, shunts) and deal with distributed slack
    # really this is only of value in case of repeated evaluation, as in a solver callback, not in solution eval

    # todo
    # GPU deployment of linear algebra, as in DMC-SCY0 paper

    # report worst violations
    sol_eval.viol_acl_acl_t_s_max_ctg = max_viol_acl_acl_delta_k
    sol_eval.viol_xfr_acl_t_s_max_ctg = max_viol_xfr_acl_delta_k
    sol_eval.viol_acl_dcl_t_s_max_ctg = max_viol_acl_dcl_delta_k
    sol_eval.viol_xfr_dcl_t_s_max_ctg = max_viol_xfr_dcl_delta_k
    sol_eval.viol_acl_xfr_t_s_max_ctg = max_viol_acl_xfr_delta_k
    sol_eval.viol_xfr_xfr_t_s_max_ctg = max_viol_xfr_xfr_delta_k
        
    print('get_time_varying_branch_characteristics_time: {}'.format(get_time_varying_branch_characteristics_time))
    print('construct_a_t_time: {}'.format(construct_a_t_time))
    print('factor_a_t_time: {}'.format(factor_a_t_time))
    print('compute_w_time: {}'.format(compute_w_time))
    print('compute_v_time: {}'.format(compute_v_time))
    print('compute_bus_theta_time: {}'.format(compute_bus_theta_time))
    print('compute_br_p_time: {}'.format(compute_br_p_time))
    print('apply_w_v_wt_time: {}'.format(apply_w_v_wt_time))
    print('compute_br_acl_delta_k_p_delta_time: {}'.format(compute_br_acl_delta_k_p_delta_time))
    print('filter_branches_time: {}'.format(filter_branches_time))
    print('compute_br_acl_delta_k_p_time: {}'.format(compute_br_acl_delta_k_p_time))
    print('compute_br_acl_delta_k_s_over_time: {}'.format(compute_br_acl_delta_k_s_over_time))
    print('zero_out_acl_delta_k_time: {}'.format(zero_out_acl_delta_k_time))
    print('get_max_br_acl_delta_k_s_over_time: {}'.format(get_max_br_acl_delta_k_s_over_time))
    print('compute_br_acl_delta_k_z_time: {}'.format(compute_br_acl_delta_k_z_time))
    print('collect_penalties_into_obj_array_time: {}'.format(collect_penalties_into_obj_array_time))
    print('end of contingency model method 1, memory info: {}'.format(utils.get_memory_info()))
