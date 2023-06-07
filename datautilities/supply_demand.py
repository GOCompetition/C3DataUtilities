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
        p_max_cumul = np.cumsum([b['p_max_cumul'] for b in t_blocks[t]])
        for i in range(len(t_blocks[t])):
            t_blocks[t][i]['p_max_cumul'] = p_max_cumul[i]
        #p_max = 0.0
        #for b in t_blocks[t]:
        #    p_max += b['p_max']
        #    b['p_max_cumul'] = p_max

def plot_blocks_pr_cs_one_t(blocks_pr, blocks_cs, file_name):

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
        marginal_index = min(np.flatnonzero(np.less_equal(p_demand, block_p_cumulative)).tolist())
        marginal_block = block_indices_sorted[marginal_index]
        lambda_min = block_c[marginal_block]
        lambda_max = block_c[marginal_block]
        # todo could go higher or lower in degenerate cases
        # if p_demand < block_p_cumulative[marginal_index]:
        #     lambda_min = block_c[marginal_block]
        #     lambda_max = block_c[marginal_block]
        # else:
        #     next_block = block_indices_sorted[marginal_index + 1]
        #     lambda_min = block_c[marginal_block]
        #     lambda_max = block_c[next_block]

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
        'lambda_min': lambda_min,
        'lambda_max': lambda_max,
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
    lambda_max = fixed_demand_equilibrium['lambda_min']

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

    # todo fill these in
    if p_max_pr > 0.0:
        if p_max_cs > 0.0:
            block_indices_sorted = sorted(list(range(num_block)), key=(lambda x: pr_block_c[x]))
            marginal_index = max(np.flatnonzero(np.
            pass # todo
        else:
            pass # todo
    else:
        if p_max_cs > 0.0:
            pass # todo
        else:
            pass # todo
    # block_indices_sorted = sorted(list(range(num_block)), key=(lambda x: block_c[x]))
    # block_p_cumulative = np.cumsum([block_p_max[i] for i in block_indices_sorted])
    # marginal_index = min(np.flatnonzero(np.less_equal(p_demand, block_p_cumulative)).tolist())
    # marginal_block = block_indices_sorted[marginal_index]
    # lambda_min = block_c[marginal_block]
    # lambda_max = block_c[marginal_block]
    surplus_total = 0.0
    surplus_pr = 0.0
    surplus_cs = 0.0
    cost_pr = 0.0
    value_cs = 0.0

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
        'lambda_min': lambda_min,
        'lambda_max': lambda_max,
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
                'supply_demand_t_{}.pdf'.format(t))
    return t_equilibrium
