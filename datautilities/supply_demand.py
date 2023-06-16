import matplotlib.pyplot as plt
import numpy as np

def get_sd_uid(data):

    return [i.uid for i in data.network.simple_dispatchable_device]

def get_num_t(data):

    return len(data.time_series_input.general.interval_duration)

def get_sd_cs(data):
    
    sd_cs = {
        i.uid:(i.device_type == 'consumer')
        for i in data.network.simple_dispatchable_device}
    return sd_cs

def get_sd_t_blocks(data):

    num_t = get_num_t(data)
    sd_cs = get_sd_cs(data)
    sd_t_p_max = get_sd_t_p_max(data)
    sd_t_blocks = {
        i.uid: [
            [{'sd': i.uid,
              'sd_cs': sd_cs[i.uid],
              't': t,
              'sd_t_p_max': sd_t_p_max[i.uid][t],
              'p_max': b[1],
              'c': b[0]}
             for b in i.cost[t]]
            for t in range(num_t)]
        for i in data.time_series_input.simple_dispatchable_device}
    return sd_t_blocks

def get_sd_t_p_max(data):

    num_t = get_num_t(data)
    sd_t_pmax = {
        i.uid: i.p_ub
        for i in data.time_series_input.simple_dispatchable_device}
    return sd_t_pmax

# def convert_sd_t_blocks_pr_to_cs(data, sd_t_blocks):

#     # just repeat cs-to-pr conversion
#     convert_sd_t_blocks_cs_to_pr(data, sd_t_blocks)

# def convert_sd_t_blocks_cs_to_pr(data, sd_t_blocks):

#     sd_uid = get_sd_uid(data)
#     num_t = get_num_t(data)
#     for j in sd_uid:
#         for t in range(num_t):
#             for b in sd_t_blocks[j][t]:
#                 if b['sd_cs']:
#                     b['c'] *= -1.0

def check_sd_t_blocks(sd_t_blocks):

    pass # todo check nonnegative p_max - ok as we do this elsewhere

def sort_sd_t_blocks_by_decreasing_margin(data, sd_t_blocks):
    '''
    i.e. pr blocks by increasing c, cs blocks by decreasing cu
    '''

    sd_uid = get_sd_uid(data)
    num_t = get_num_t(data)
    sd_cs = get_sd_cs(data)
    for j in sd_uid:
        if sd_cs[j]:
            for t in range(num_t):
                sd_t_blocks[j][t] = sorted(sd_t_blocks[j][t], key=(lambda x: -x['c']))
        else:
            for t in range(num_t):
                sd_t_blocks[j][t] = sorted(sd_t_blocks[j][t], key=(lambda x: x['c']))

def sort_t_blocks_by_increasing_c(data, t_blocks):

    num_t = get_num_t(data)
    for t in range(num_t):
        t_blocks[t] = sorted(t_blocks[t], key=(lambda x: x['c']))

def sort_t_blocks_by_decreasing_c(data, t_blocks):

    num_t = get_num_t(data)
    for t in range(num_t):
        t_blocks[t] = sorted(t_blocks[t], key=(lambda x: -x['c']))

def add_p_max_cumul_to_sd_t_blocks(data, sd_t_blocks):

    sd_uid = get_sd_uid(data)
    num_t = get_num_t(data)
    for j in sd_uid:
        for t in range(num_t):
            p_max = 0.0
            for b in sd_t_blocks[j][t]:
                p_max += b['p_max']
                b['p_max_cumul'] = p_max

def filter_sd_t_blocks_by_sd_t_pmax(data, sd_t_blocks):

    sd_uid = get_sd_uid(data)
    num_t = get_num_t(data)
    for j in sd_uid:
        for t in range(num_t):
            blocks = []
            for b in sd_t_blocks[j][t]:
                blocks.append(b)
                if b['p_max_cumul'] > b['sd_t_p_max']:
                    b['p_max'] -= (b['p_max_cumul'] - b['sd_t_p_max'])
                    b['p_max'] = max(0.0, b['p_max'])
                    b['p_max_cumul'] = b['sd_t_p_max']
                    break
            sd_t_blocks[j][t] = blocks

def flatten_sd_t_blocks_to_t_blocks(data, sd_t_blocks):
    
    sd_uid = get_sd_uid(data)
    num_t = get_num_t(data)
    t_blocks = [
        [b for j in sd_uid for b in sd_t_blocks[j][t]]
        for t in range(num_t)]
    return t_blocks

def get_t_blocks_pr(data, t_blocks):

    num_t = get_num_t(data)
    t_blocks_pr = [
        [b for b in t_blocks[t] if not b['sd_cs']]
        for t in range(num_t)]
    return t_blocks_pr

def get_t_blocks_cs(data, t_blocks):

    num_t = get_num_t(data)
    t_blocks_cs = [
        [b for b in t_blocks[t] if b['sd_cs']]
        for t in range(num_t)]
    return t_blocks_cs

def add_p_max_cumul_to_t_blocks(data, t_blocks):

    num_t = get_num_t(data)
    for t in range(num_t):
        p_max_cumul = np.cumsum([b['p_max'] for b in t_blocks[t]])
        for i in range(len(t_blocks[t])):
            t_blocks[t][i]['p_max_cumul'] = p_max_cumul[i]
        #p_max = 0.0
        #for b in t_blocks[t]:
        #    p_max += b['p_max']
        #    b['p_max_cumul'] = p_max

def plot_blocks_pr_cs_one_t(blocks_pr, blocks_cs, equilibrium, file_name):

    x_pr = [b['p_max_cumul'] for b in blocks_pr for i in range(2)]
    x_pr = x_pr[0:-1]
    x_pr = [0.0] + x_pr
    y_pr = [b['c'] for b in blocks_pr for i in range(2)]
    x_cs = [b['p_max_cumul'] for b in blocks_cs for i in range(2)]
    x_cs = x_cs[0:-1]
    x_cs = [0.0] + x_cs
    y_cs = [b['c'] for b in blocks_cs for i in range(2)]

    fig,ax = plt.subplots()
    ax.plot(x_pr, y_pr, x_cs, y_cs)
    ax.set_yscale('log')
    ax.set_title('p: {}, lambda: {}'.format(equilibrium['p_med'], equilibrium['lambda_med']))
    ax.legend(['supply', 'demand'])
    ax.set_xlabel('p (pu)')
    ax.set_ylabel('lambda ($/pu-h)')
    plt.savefig(fname=file_name)

def compute_equilibrium_fixed_demand(block_p_max, block_c, p_demand):

    num_block = len(block_p_max)
    assert len(block_c) == num_block

    min_block_p_max = min([0.0] + block_p_max)
    assert min_block_p_max >= 0.0

    p_min_pr = 0.0
    p_max_pr = sum(block_p_max)
    if num_block == 0:
        lambda_min_pr = None
        lambda_max_pr = None
    else:
        lambda_min_pr = min(block_c)
        lambda_max_pr = max(block_c)

    if p_demand < p_min_pr:
        p_min = None
        p_max = None
        lambda_min = None
        lambda_max = None
    if p_demand > p_max_pr:
        p_min = None
        p_max = None
        lambda_min = None
        lambda_max = None
    if p_demand == p_min_pr and p_demand == p_max_pr:
        p_min = p_demand
        p_max = p_demand
        lambda_min = None
        lambda_max = None
    if p_demand == p_min_pr and p_demand < p_max_pr:
        p_min = p_demand
        p_max = p_demand
        lambda_min = None
        lambda_max = lambda_min_pr
    if p_demand > p_min_pr and p_demand == p_max_pr:
        p_min = p_demand
        p_max = p_demand
        lambda_min = lambda_max_pr
        lambda_max = None
    if p_min_pr < p_demand and p_demand < p_max_pr:
        p_min = p_demand
        p_max = p_demand
        block_indices_sorted = sorted(list(range(num_block)), key=(lambda x: block_c[x]))
        block_p_cumulative = np.cumsum([block_p_max[i] for i in block_indices_sorted])
        indices_below_demand = np.flatnonzero(np.less(block_p_cumulative, p_demand)).tolist()
        indices_at_demand = np.flatnonzero(np.equal(block_p_cumulative, p_demand)).tolist()
        indices_above_demand = np.flatnonzero(np.greater(block_p_cumulative, p_demand)).tolist()
        assert len(indices_above_demand) > 0
        if len(indices_at_demand) == 0:
            min_index_above_demand = min(indices_above_demand)
            lambda_index = min_index_above_demand
            lambda_block = block_indices_sorted[lambda_index]
            lambda_min = block_c[lambda_block]
            lambda_max = block_c[lambda_block]
        else:
            min_index_at_demand = min(indices_at_demand)
            max_index_at_demand = max(indices_at_demand)
            lambda_min_index = min_index_at_demand
            lambda_max_index = max_index_at_demand + 1
            lambda_min_block = block_indices_sorted[lambda_min_index]
            lambda_max_block = block_indices_sorted[lambda_max_index]
            lambda_min = block_c[lambda_min_block]
            lambda_max = block_c[lambda_max_block]
        #
        #marginal_index = min(np.flatnonzero(np.less_equal(p_demand, block_p_cumulative)).tolist())
        #marginal_block = block_indices_sorted[marginal_index]
        #lambda_min = block_c[marginal_block]
        #lambda_max = block_c[marginal_block]
        #

    if p_min is None:
        if p_max is None:
            p_med = None
        else:
            p_med = p_max
    else:
        if p_max is None:
            p_med = p_min
        else:
            p_med = 0.5 * (p_min + p_max)
    if lambda_min is None:
        if lambda_max is None:
            lambda_med = None
        else:
            lambda_med = lambda_max
    else:
        if lambda_max is None:
            lambda_med = lambda_min
        else:
            lambda_med = 0.5 * (lambda_min + lambda_max)

    equilibrium = {
        'fixed_demand': p_demand,
        'num_block': num_block,
        'min_block_p_max': min_block_p_max,
        'p_min_pr': p_min_pr,
        'p_max_pr': p_max_pr,
        'lambda_min_pr': lambda_min_pr,
        'lambda_max_pr': lambda_max_pr,
        'p_min': p_min,
        'p_max': p_max,
        'p_med': p_med,
        'lambda_min': lambda_min,
        'lambda_max': lambda_max,
        'lambda_med': lambda_med,
        }

    #print('fixed demand s-d equilibrium: {}'.format(equilibrium))

    return equilibrium
    
def compute_equilibrium_flexible_demand(pr_block_max_p, pr_block_c, cs_block_max_p, cs_block_c, fixed_demand):

    assert fixed_demand == 0.0

    num_pr_block = len(pr_block_max_p)
    num_cs_block = len(cs_block_max_p)
    assert len(pr_block_c) == num_pr_block
    assert len(cs_block_c) == num_cs_block

    pr_min_block_max_p = min([0.0] + pr_block_max_p)
    cs_min_block_max_p = min([0.0] + cs_block_max_p)
    # print('pr_block_max_p: {}'.format(pr_block_max_p))
    # print('pr_block_c: {}'.format(pr_block_c))
    # print('cs_block_max_p: {}'.format(cs_block_max_p))
    # print('cs_block_c: {}'.format(cs_block_c))
    assert pr_min_block_max_p >= 0.0
    assert cs_min_block_max_p >= 0.0

    #cs_block_c_minus = [-c for c in cs_block_c]
    fixed_demand_plus_flex_demand_max = fixed_demand + sum(cs_block_max_p)

    fixed_demand_equilibrium = compute_equilibrium_fixed_demand(
        block_p_max=(pr_block_max_p + cs_block_max_p),
        #block_c=(pr_block_c + cs_block_c_minus),
        block_c=(pr_block_c + cs_block_c),
        p_demand=fixed_demand_plus_flex_demand_max)

    lambda_min = fixed_demand_equilibrium['lambda_min']
    lambda_max = fixed_demand_equilibrium['lambda_max']

    p_min_pr = 0.0
    p_max_pr = sum(pr_block_max_p)
    p_min_cs = 0.0
    p_max_cs = sum(cs_block_max_p)

    if num_pr_block > 0:
        lambda_min_pr = min(pr_block_c)
        lambda_max_pr = max(pr_block_c)
    else:
        lambda_min_pr = None
        lambda_max_pr = None
    if num_cs_block > 0:
        lambda_min_cs = min(cs_block_c)
        lambda_max_cs = max(cs_block_c)
    else:
        lambda_min_cs = None
        lambda_max_cs = None

    p_min = 0.0
    p_max = 0.0
    # todo fill these in
    surplus_total = 0.0
    surplus_pr = 0.0
    surplus_cs = 0.0
    cost_pr = 0.0
    value_cs = 0.0
    if p_max_pr > 0.0:
        if p_max_cs > 0.0:
            #pr_block_indices_sorted = sorted(list(range(num_pr_block)), key=(lambda x: pr_block_c[x]))
            #pr_block_p_max_cumulative = np.cumsum([pr_block_p_max[i] for i in pr_block_indices_sorted])
            #cs_block_indices_sorted = sorted(list(range(num_cs_block)), key=(lambda x: -cs_block_c[x]))
            #cs_block_p_max_cumulative = np.cumsum([cs_block_p_max[i] for i in cs_block_indices_sorted])
            if lambda_min is None:
                if lambda_max is None:
                    pr_block_indices_in_money = []
                    pr_block_indices_out_of_money = []
                    pr_block_indices_marginal = list(range(num_pr_block))
                    cs_block_indices_in_money = []
                    cs_block_indices_out_of_money = []
                    cs_block_indices_marginal = list(range(num_cs_block))
                else:
                    pr_block_indices_in_money = []
                    pr_block_indices_out_of_money = np.flatnonzero(np.greater(pr_block_c, lambda_max)).tolist()
                    pr_block_indices_marginal = np.flatnonzero(np.less_equal(pr_block_c, lambda_max)).tolist()
                    cs_block_indices_in_money = np.flatnonzero(np.greater(cs_block_c, lambda_max)).tolist()
                    cs_block_indices_out_of_money = []
                    cs_block_indices_marginal = np.flatnonzero(np.less_equal(cs_block_c, lambda_max)).tolist()
            else:
                if lambda_max is None:
                    pr_block_indices_in_money = np.flatnonzero(np.less(pr_block_c, lambda_min)).tolist()
                    pr_block_indices_out_of_money = []
                    pr_block_indices_marginal = np.flatnonzero(np.greater_equal(pr_block_c, lambda_min)).tolist(),
                    cs_block_indices_in_money = []
                    cs_block_indices_out_of_money = np.flatnonzero(np.less(cs_block_c, lambda_min)).tolist()
                    cs_block_indices_marginal = np.flatnonzero(np.greater_equal(cs_block_c, lambda_min)).tolist()
                else:
                    pr_block_indices_in_money = np.flatnonzero(np.less(pr_block_c, lambda_min)).tolist()
                    pr_block_indices_out_of_money = np.flatnonzero(np.greater(pr_block_c, lambda_max)).tolist()
                    pr_block_indices_marginal = np.flatnonzero(
                        np.logical_and(
                            np.greater_equal(pr_block_c, lambda_min),
                            np.less_equal(pr_block_c, lambda_max))).tolist()
                    cs_block_indices_in_money = np.flatnonzero(np.greater(cs_block_c, lambda_max)).tolist()
                    cs_block_indices_out_of_money = np.flatnonzero(np.less(cs_block_c, lambda_min)).tolist()
                    cs_block_indices_marginal = np.flatnonzero(
                        np.logical_and(
                            np.greater_equal(cs_block_c, lambda_min),
                            np.less_equal(cs_block_c, lambda_max))).tolist()
            pr_p_max_in_money = sum(pr_block_max_p[i] for i in pr_block_indices_in_money)
            pr_p_max_out_of_money = sum(pr_block_max_p[i] for i in pr_block_indices_out_of_money)
            pr_p_max_marginal = sum(pr_block_max_p[i] for i in pr_block_indices_marginal)
            cs_p_max_in_money = sum(cs_block_max_p[i] for i in cs_block_indices_in_money)
            cs_p_max_out_of_money = sum(cs_block_max_p[i] for i in cs_block_indices_out_of_money)
            cs_p_max_marginal = sum(cs_block_max_p[i] for i in cs_block_indices_marginal)
            p_min = max(pr_p_max_in_money, cs_p_max_in_money)
            p_max = min(pr_p_max_in_money + pr_p_max_marginal, cs_p_max_in_money + cs_p_max_marginal)
            # todo
        else:
            pass # OK
    else:
        if p_max_cs > 0.0:
            pass # OK
        else:
            pass # OK
    # block_indices_sorted = sorted(list(range(num_block)), key=(lambda x: block_c[x]))
    # block_p_cumulative = np.cumsum([block_p_max[i] for i in block_indices_sorted])
    # marginal_index = min(np.flatnonzero(np.less_equal(p_demand, block_p_cumulative)).tolist())
    # marginal_block = block_indices_sorted[marginal_index]
    # lambda_min = block_c[marginal_block]
    # lambda_max = block_c[marginal_block]

    if p_min is None:
        if p_max is None:
            p_med = None
        else:
            p_med = p_max
    else:
        if p_max is None:
            p_med = p_min
        else:
            p_med = 0.5 * (p_min + p_max)
    if lambda_min is None:
        if lambda_max is None:
            lambda_med = None
        else:
            lambda_med = lambda_max
    else:
        if lambda_max is None:
            lambda_med = lambda_min
        else:
            lambda_med = 0.5 * (lambda_min + lambda_max)

    equilibrium = {
        'fixed_demand': fixed_demand,
        'num_pr_block': num_pr_block,
        'num_cs_block': num_cs_block,
        'p_min_pr': p_min_pr,
        'p_max_pr': p_max_pr,
        'p_min_cs': p_min_cs,
        'p_max_cs': p_max_cs,
        'lambda_min_pr': lambda_min_pr,
        'lambda_max_pr': lambda_max_pr,
        'lambda_min_cs': lambda_min_cs,
        'lambda_max_cs': lambda_max_cs,
        'p_min': p_min,
        'p_max': p_max,
        'p_med': p_med,
        'lambda_min': lambda_min,
        'lambda_max': lambda_max,
        'lambda_med': lambda_med,
        'surplus_total': surplus_total,
        'surplus_pr': surplus_pr,
        'surplus_cs': surplus_cs,
        'cost_pr': cost_pr,
        'value_cs': value_cs,
        }

    #print('flexible demand s-d equilibrium: {}'.format(equilibrium))

    return equilibrium
    
def analyze_supply_demand(data, do_plots=False):

    num_t = get_num_t(data)
    sd_t_blocks = get_sd_t_blocks(data)
    check_sd_t_blocks(sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    #convert_sd_t_blocks_cs_to_pr(data, sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    sort_sd_t_blocks_by_decreasing_margin(data, sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    add_p_max_cumul_to_sd_t_blocks(data, sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    filter_sd_t_blocks_by_sd_t_pmax(data, sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    #convert_sd_t_blocks_pr_to_cs(data, sd_t_blocks)
    #print('sd_t_blocks: {}'.format(sd_t_blocks))
    t_blocks = flatten_sd_t_blocks_to_t_blocks(data, sd_t_blocks)
    t_blocks_pr = get_t_blocks_pr(data, t_blocks)
    t_blocks_cs = get_t_blocks_cs(data, t_blocks)
    t_equilibrium = [
        compute_equilibrium_flexible_demand(
            pr_block_max_p=[b['p_max'] for b in t_blocks_pr[t]],
            pr_block_c=[b['c'] for b in t_blocks_pr[t]],
            cs_block_max_p=[b['p_max'] for b in t_blocks_cs[t]],
            cs_block_c=[b['c'] for b in t_blocks_cs[t]],
            fixed_demand=0.0)
        for t in range(num_t)]
    for t in range(num_t):
        print('t: {}'.format(t))
        print('equilibrium: {}'.format(t_equilibrium[t]))
    sort_t_blocks_by_increasing_c(data, t_blocks_pr)
    sort_t_blocks_by_decreasing_c(data, t_blocks_cs)
    add_p_max_cumul_to_t_blocks(data, t_blocks_pr)
    add_p_max_cumul_to_t_blocks(data, t_blocks_cs)
    do_plots = True
    if do_plots:
        for t in range(num_t):
            plot_blocks_pr_cs_one_t(
                t_blocks_pr[t],
                t_blocks_cs[t],
                t_equilibrium[t],
                'supply_demand_t_{}.pdf'.format(t))
    return t_equilibrium
