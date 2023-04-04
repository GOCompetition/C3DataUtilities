'''
Functions needed in various places in datautilities
'''

import os, sys, subprocess, traceback, pathlib, time, psutil, json
import numpy, networkx
from scipy.sparse import sparsetools

import datamodel
from datautilities.errors import GitError

def timeit(function):
    def timed(*args, **kw):
        start_time = time.time()
        result = function(*args, **kw)
        end_time = time.time()
        print('function: {}, time: {}'.format(function.__name__, end_time - start_time))
        return result
    return timed

def get_memory_info():
    '''
    in bytes
    '''

    process = psutil.Process(os.getpid())
    info = process.memory_info()
    rss = info.rss
    rss_human = psutil._common.bytes2human(rss)
    percent = process.memory_percent()
    return {
        'rss bytes': rss,
        'rss human': rss_human,
        'percent': percent}

# from
#   https://stackoverflow.com/questions/50916422/python-typeerror-object-of-type-int64-is-not-json-serializable
# call as:
#   json.dumps(data, cls=NpEncoder)
class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, numpy.bool_):
            return bool(obj)
        if isinstance(obj, numpy.integer):
            return int(obj)
        if isinstance(obj, numpy.floating):
            return float(obj)
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        return super(NpEncoder, self).default(obj)

def get_C3DataUtilities_dir():
    
    return str(pathlib.Path(get_data_utils_dir()).parents[0])

def get_data_utils_dir():

    return os.path.dirname(os.path.realpath(__file__))

def get_data_model_dir():

    return os.path.dirname(os.path.realpath(datamodel.__file__))

def get_git_info(path): # todo get branch also
    '''
    path is a string giving a path from which a git repository can be found
    returns a dict describing the current state of the repository,
    including the commit it is currently pointed to:

        'commit': the alpha-numeric commit ID
        'date': the date of the commit
        'branch': the branch we are on now
    '''

    repo = {
        'branch': None,
        'commit': None,
        'date': None,
        'query_return_code': None,
        'query_err': None,
        }

    repo['query_path'] = path

    # run "git log"
    results = subprocess.run(['git', 'log', '-1'], cwd=path, capture_output=True)

    repo['query_return_code'] = results.returncode
    repo['query_out'] = results.stdout.decode(sys.stdout.encoding)
    repo['query_err'] = results.stderr.decode(sys.stderr.encoding)
    
    keys = ['commit', 'date']
    if repo['query_return_code'] == 0:
        lines = repo['query_out'].splitlines()
        for line in lines:
            line_lower = line.lower()
            for k in keys:
                if line_lower.startswith(k):
                    if repo[k] is not None:
                        raise GitError('"{}" appears more than once'.format(k))
                    repo[k] = line[len(k):].lstrip(':').strip()
        for k in keys:
            if repo[k] is None:
                raise GitError('"{}" does not appear'.format(k))

    return repo

def get_git_info_all():

    git_info = {}
    git_info['C3DataUtilities'] = get_git_info(get_data_utils_dir())
    git_info['Bid-DS-data-model'] = get_git_info(get_data_model_dir())
    return git_info

def get_max(arr, idx_lists=None):

    return get_max_min(arr, use_max=True, idx_lists=idx_lists)

def get_min(arr, idx_lists=None):

    return get_max_min(arr, use_max=False, idx_lists=idx_lists)

def get_max_abs(arr, idx_lists=None):

    max_out = get_max(arr, idx_lists=idx_lists)
    min_out = get_min(arr, idx_lists=idx_lists)
    if max_out['val'] is None or min_out['val'] is None:
        out = max_out
    #elif max_out['abs'] > min_out['abs']:
    elif abs(max_out['val']) > abs(min_out['val']):
        out = max_out
    else:
        out = min_out
    return out

def make_empty_viol(val=None, num_indices=None):

    if num_indices is None:
        return val
    else:
        idx = {i: None for i in range(num_indices)}
        return({'val': val, 'idx': idx})

def get_max_min(arr, use_max=True, idx_lists=None):
    
    # out = {
    #     'val': None,
    #     #'abs': None,
    #     #'idx_lin': None,
    #     #'idx_int': None,
    #     'idx': None,
    # }
    if idx_lists is None:
        out = make_empty_viol()
    else:
        out = make_empty_viol(num_indices=len(idx_lists))
    # print('arr.size', arr.size)
    # print('use_max', use_max)
    # print('idx_lists', idx_lists)
    # print('out', out)
    if arr.size > 0:
        if use_max:
            arg = numpy.argmax(arr)
        else:
            arg = numpy.argmin(arr)
        #out['idx_lin'] = arg
        arg_tuple = numpy.unravel_index(arg, shape=arr.shape)
        val = arr[arg_tuple]
        out['val'] = val
        #out['abs'] = abs(val)
        #out['idx_int'] = arg_tuple
        if idx_lists is not None:
            #idx = tuple([idx_lists[i][arg_tuple[i]] for i in range(len(idx_lists))])
            idx = {i:idx_lists[i][arg_tuple[i]] for i in range(len(idx_lists))}
            out['idx'] = idx
    return out

def csr_mat_vec_add_to_vec(a, x, out):
    '''
    csr_mat_vec_add_to_vec(a, x, out)

    compute a@x and add result to out

    a - sparse matrix (csr)
    x - vector or dense matrix
    out - vector or dense matrix of conforming shape
    '''

    # This should be a more efficient version of:
    #
    #     out += a.dot(x)
    #
    # or
    #
    #     out[:] += a.dot(x)
    #
    # either of which evidently would create a temporary variable to store the output of dot()
    # before assigning it to out. Limited testing suggests they are about the same though.

    # csr_matvec adds to the out vector, so we need to 0 it out first (or we could take advantage of this)
    #out[:] = 0.0
    #sparsetools.csr_matvec(a.shape[0], a.shape[1], a.indptr, a.indices, a.data, x, out)
    
    out[:] += a.dot(x)
    #numpy.add(out

def csr_mat_vec_max_to_vec(a, x, out):
    '''
    analogous to csr_mat_vec_add_to_vec
    instead of adding the products to the out vector, we take the maximum of them with the out vector

    csr_mat_vec_max_to_vec(a, x, out)

    computes y with
    y[i,k] = max([out[i,k]] + [a[i,j] * x[j,k] for j in range(nj)])
    stores y in out

    a - sparse matrix (csr) - ni-by-nj
    x - vector or dense matrix - nj-by-nk
    out - vector or dense matrix of conforming shape - ni-by-nk

    '''

    shape_a = a.shape
    shape_x = x.shape
    shape_out = out.shape

    assert(len(shape_a) == 2)
    assert(len(shape_x) == 2)
    assert(len(shape_out) == 2)
    assert(shape_a[1] == shape_x[0])
    assert(shape_a[0] == shape_out[0])
    assert(shape_x[1] == shape_out[1])

    ni = shape_a[0]
    nj = shape_a[1]
    nk = shape_x[1]

    temp = numpy.zeros(shape=(nj + 1, nk))
    a_row = numpy.zeros(shape=(1, nj))

    for i in range(ni):
        a[i,:].toarray(out=a_row)
        numpy.multiply(numpy.reshape(a_row, newshape=(nj, 1)), x, out=temp[0:nj,:])
        temp[nj,:] = out[i,:]
        numpy.amax(temp, axis=0, out=out[i,:])

@timeit
def get_connected_components(vertices, od_pairs):
    '''

    components = get_connected_components(vertices, od_pairs)

    vertices
    should be a list of nonnegative ints
    nonnegative ints represent vertices

    od_pairs
    should be a list of pairs of nonnegative ints
    each int in each element of od_pairs should be in vertices
    pairs represent edges specified by the origin and destination vertices

    components
    will be a list of lists of nonnegative ints
    each element of components is a component
    each component is a list of vertices that are connected by edges
    no vertex is listed twice in a single component
    each vertex is listed in exactly one component
    for any two vertices listed in two different components, there is no path of edges connecting them

    The following unusual features ARE OK:
    * empty list of pairs
    * empty list of vertices (requires an empty list of pairs)
    * isolated vertices, i.e. not adjacent to any pairs
    * pairs listing vertices in decreasing order
    * pairs listing vertices in increasing order
    * duplicate pairs
    * pairs that are the same except for the order of vertices
    * pairs where both vertices are the same, i.e. a self edge
    '''

    num_vertices = len(vertices)
    num_edges = len(od_pairs)
    edge_vertices = sorted(list(set([p[0] for p in od_pairs] + [p[1] for p in od_pairs])))
    vertices_in_edges_not_in_vertices = sorted(list(set(edge_vertices).difference(set(vertices))))
    if len(vertices_in_edges_not_in_vertices) > 0:
        print('vertices in edge set but not in vertex set: {}'.format(vertices_in_edges_not_in_vertices))
        assert(len(vertices_in_edges_not_in_vertices) <= 0)
    if num_vertices == 0:
        return []

    # for connectedness, we do not need self edges, duplicate edges, or edges that are duplicates on switching o-d order
    pairs_o_lt_d = (
        [(p[0], p[1]) for p in od_pairs if p[0] < p[1]] +
        [(p[1], p[0]) for p in od_pairs if p[1] < p[0]])
    pairs_sorted = sorted(pairs_o_lt_d)
    pairs_unique = sorted(list(set(pairs_sorted)))

    g = networkx.Graph()
    g.add_nodes_from(sorted(list(set(vertices))))
    #g.add_edges_from(sorted(od_pairs))
    g.add_edges_from(sorted(pairs_unique))
    g_connected_components = networkx.connected_components(g)
    return [sorted(list(c)) for c in g_connected_components]

@timeit
def get_bridges(od_pairs):
    '''
    bridges = get_bridges(od_pairs)

    od_pairs
    should be a list of pairs of nonnegative ints
    nonnegative ints represent vertices
    pairs represent edges specified by the origin and destination vertices

    bridges
    will be a list of nonnegative ints
    each element of bridges is the index of a bridge as an element of od_pairs
    i.e. [od_pairs[i] for i in bridges] is the set of pairs representing edges that are bridges
    A bridge is an edge such that when it is removed from the graph, the number of connected components
    of the graph increases. Specifically, the connected component containing a bridge will be disconnected
    into two connected components, so the number of connected components increases by 1.

    The following unusual features ARE OK:
    * empty list of pairs
    * empty list of vertices (requires an empty list of pairs)
    * isolated vertices, i.e. not adjacent to any pairs
    * pairs listing vertices in decreasing order
    * pairs listing vertices in increasing order
    * duplicate pairs
    * pairs that are the same except for the order of vertices
    * pairs where both vertices are the same, i.e. a self edge

    the following types of edges cannot be a bridge:
    * self-edge e (o[e] == d[e])
    * edge e that is parallel with another edge e2 (o[e] == o[e2] and d[e] == d[e2)
    * edge e that is parallel with another edge e2 on switching ordder (o[e] == d[e2] and d[e] == o[e2)
    so we could reduce the graph so that it has none of these edges
    and exclude any of them if they show up as bridges    
    '''

    # todo make this more efficient
    
    num_edges = len(od_pairs)
    if num_edges == 0:
        return []
    o_nodes = [p[0] for p in od_pairs]
    d_nodes = [p[1] for p in od_pairs]
    nodes = sorted(list(set(o_nodes + d_nodes)))
    num_nodes = len(nodes)
    if num_nodes == 0:
        return []
    max_node = max(nodes)

    # pair map
    #od_pairs_map = {od_pairs[i]:i for i in range(num_edges)}
    pairs_o_lt_d_map = {}
    for i in range(num_edges): # todo this is likely inefficient
        if od_pairs[i][0] < od_pairs[i][1]:
            pairs_o_lt_d_map[od_pairs[i]] = i
        elif od_pairs[i][1] < od_pairs[i][0]:
            pairs_o_lt_d_map[(od_pairs[i][1], od_pairs[i][0])] = i

    # for connectedness, we do not need self edges, duplicate edges, or edges that are duplicates on switching o-d order
    pairs_o_lt_d = (
        [(p[0], p[1]) for p in od_pairs if p[0] < p[1]] +
        [(p[1], p[0]) for p in od_pairs if p[1] < p[0]])
    pairs_sorted = sorted(pairs_o_lt_d)
    pairs_unique = sorted(list(set(pairs_sorted)))
    pairs_unique_count = {p:0 for p in pairs_unique}
    for p in pairs_o_lt_d:
        pairs_unique_count[p] += 1
    pairs_count_gt_1 = sorted([p for p in pairs_unique if pairs_unique_count[p] > 1])

    # get bridges on reduced graph
    g = networkx.Graph()
    g.add_nodes_from(nodes)
    g.add_edges_from(pairs_unique)
    g_bridges = networkx.bridges(g)

    # get bridges on original graph by removing those that cannot be bridges as they have multiple edges
    bridges = sorted(list(set(list(g_bridges)).difference(set(pairs_count_gt_1))))
    #bridges_idx = sorted([od_pairs_map[i] for i in bridges])
    bridges_idx = sorted([pairs_o_lt_d_map[i] for i in bridges])
    # print('od_pairs: {}'.format(od_pairs))
    # print('o_nodes: {}'.format(o_nodes))
    # print('d_nodes: {}'.format(d_nodes))
    # print('nodes: {}'.format(nodes))
    # print('num_nodes: {}'.format(num_nodes))
    # print('num_edges: {}'.format(num_edges))
    # print('pairs_sorted: {}'.format(pairs_sorted))
    # print('pairs_dict: {}'.format(pairs_dict))
    # print('pairs_local_sorted: {}'.format(pairs_local_sorted))
    # print('pairs_augmented: {}'.format(pairs_augmented))
    # print('nodes(g): {}'.format(list(g.nodes)))
    # print('edges(g): {}'.format(list(g.edges)))
    # print('bridges(g): {}'.format(list(g_bridges)))
    # print('bridge_pair_indices: {}'.format(bridge_pair_indices))
    return bridges_idx

def get_bridges_orig(od_pairs):
    '''
    bridges = get_bridges(od_pairs)

    od_pairs
    should be a list of pairs of nonnegative ints
    nonnegative ints represent vertices
    pairs represent edges specified by the origin and destination vertices

    bridges
    will be a list of nonnegative ints
    each element of bridges is the index of a bridge as an element of od_pairs
    i.e. [od_pairs[i] for i in bridges] is the set of pairs representing edges that are bridges
    A bridge is an edge such that when it is removed from the graph, the number of connected components
    of the graph increases. Specifically, the connected component containing a bridge will be disconnected
    into two connected components, so the number of connected components increases by 1.

    The following unusual features ARE OK:
    * empty list of pairs
    * empty list of vertices (requires an empty list of pairs)
    * isolated vertices, i.e. not adjacent to any pairs
    * pairs listing vertices in decreasing order
    * pairs listing vertices in increasing order
    * duplicate pairs
    * pairs that are the same except for the order of vertices
    * pairs where both vertices are the same, i.e. a self edge
    '''
    # todo: this one has a bug somewhere. the final mapping had a key error
    # this method is faster than the replacement though
    
    num_edges = len(od_pairs)
    if num_edges == 0:
        return []
    o_nodes = [p[0] for p in od_pairs]
    d_nodes = [p[1] for p in od_pairs]
    nodes = sorted(list(set(o_nodes + d_nodes)))
    num_nodes = len(nodes)
    if num_nodes == 0:
        return []
    max_node = max(nodes)
    pairs_o_lt_d = [
        (o_nodes[i], d_nodes[i], i)
        if o_nodes[i] <= d_nodes[i]
        else (d_nodes[i], o_nodes[i], i)
        for i in range(num_edges)]
    pairs_sorted = sorted(pairs_o_lt_d)
    pairs_unique = list(set(pairs_sorted))
    pairs_dict = {p:[] for p in pairs_unique}
    for p in pairs_sorted:
        pairs_dict[(p[0], p[1])].append(p)
    pairs_local_sorted = sorted(
        [(v[i][0], v[i][1], i, v[i][2]) for k, v in pairs_dict.items() for i in range(len(v))])
    pairs_first = [p for p in pairs_local_sorted if p[2] == 0]
    pairs_with_extra_edges = sorted([k for k, v in pairs_dict.items() if len(v) > 1])
    num_pairs_with_extra_edges = len(pairs_with_extra_edges)
    extra_pairs = (
        [(pairs_with_extra_edges[i][0], num_nodes + i, num_edges + i)
         for i in range(num_pairs_with_extra_edges)] +
        [(pairs_with_extra_edges[i][1], num_nodes + i, num_edges + i + num_pairs_with_extra_edges)
         for i in range(num_pairs_with_extra_edges)])
    pairs_augmented = sorted([(p[0], p[1], p[3]) for p in pairs_first] + extra_pairs)
    pairs_augmented_dict = {(p[0], p[1]): p[2] for p in pairs_augmented}
    g = networkx.Graph()
    g.add_edges_from(sorted(pairs_augmented_dict.keys()))
    g_bridges = networkx.bridges(g)
    bridge_pair_indices = [pairs_augmented_dict[p] for p in list(g_bridges)]
    # print('od_pairs: {}'.format(od_pairs))
    # print('o_nodes: {}'.format(o_nodes))
    # print('d_nodes: {}'.format(d_nodes))
    # print('nodes: {}'.format(nodes))
    # print('num_nodes: {}'.format(num_nodes))
    # print('num_edges: {}'.format(num_edges))
    # print('pairs_sorted: {}'.format(pairs_sorted))
    # print('pairs_dict: {}'.format(pairs_dict))
    # print('pairs_local_sorted: {}'.format(pairs_local_sorted))
    # print('pairs_augmented: {}'.format(pairs_augmented))
    # print('nodes(g): {}'.format(list(g.nodes)))
    # print('edges(g): {}'.format(list(g.edges)))
    # print('bridges(g): {}'.format(list(g_bridges)))
    # print('bridge_pair_indices: {}'.format(bridge_pair_indices))
    return bridge_pair_indices

def eval_convex_cost_function(num_block, p_max, c, p):
    '''
    assumes
    '''

    # todo - what if p exceeds sum(p_max)? - nothing terrible happens, we just do not apply a cost to the excess
    # need to add something to the checker to prevent this
    # just check that sd_t_p_max <= sum_b sd_t_b_p_max
    # but what about su/sd trajectories?
    # also should require that the trajectories do not go past sd_t_pmax
    # safer to require that pmin[t] - pmax[t-1] <= d[t]*min(ru, suru) and pmin[t] - pmax[t+1] <= d[t+1]*min(rd, sdrd)

    p_remaining = float(p)
    z_so_far = 0.0
    for i in range(num_block):
        if p_remaining > p_max[i]:
            z_so_far += c[i] * p_max[i]
            p_remaining -= p_max[i]
        else:
            z_so_far += c[i] * p_remaining
            break
    return z_so_far

def eval_market(
        fixed_quantity=None, fixed_price=None,
        supply_block_quantity=None, supply_block_price=None,
        demand_block_quantity=None, demand_block_price=None):
    '''
    (quantity_max, quantity_min, price_max, price_min) = eval_market(
        fixed_quantity, fixed_price, supply_block_quantity, supply_block_price, demand_block_quantity, demand_block_price)

    evaluates the market outcome given an appropriate combination of inputs.

    The inputs are either:
    a supply curve and a demand curve
    a supply curve and a fixed quantity
    a supply curve and a fixed price
    a demand curve and a fixed quantity
    a demand curve and a fixed price

    A supply or demand curve is represented by a set of blocks each parameterized by
    a nonnegative quantity and a price

    The market outcome is conceptually a quantity and price representing a market equilibrium.
    Since the supply and demand curves are represented by step functions,
    the set of equilibria is typically a line segment with either
    constant quantity and price varying between a minimum and a maximum value or
    constant price and quantity varying between a minimum and a maximum value.

    Input arguments:
    fixed_quantity None or float
    fixed_price None or float
    supply_block_quantity None or 1-d array of floats
    supply_block_price None or 1-d array of floats
    demand_block_quantity None or 1-d array of floats
    demand_block_price None or 1-d array of floats

    Output arguments:
    quantity_max float
    quantity_min float
    price_max float
    price_min float

    The outputs will satisfy
      (quantity_max == quantity_min) or (price_max == price_min)
    unless there is an error
    '''

    quantity_max = float('inf')
    quantity_min = -float('inf')
    price_max = float('inf')
    price_min = -float('inf')
    
    do_eval_x_p_from_s_d = (
        (fixed_quantity is None) and (fixed_price is None)
        and (supply_block_quantity is not None) and (supply_block_price is not None)
        and (demand_block_quantity is not None) and (demand_block_price is not None))
    do_eval_x_from_p_s = (
        (fixed_quantity is None) and (fixed_price is not None)
        and (supply_block_quantity is not None) and (supply_block_price is not None)
        and (demand_block_quantity is None) and (demand_block_price is None))
    do_eval_x_from_p_d = (
        (fixed_quantity is None) and (fixed_price is not None)
        and (supply_block_quantity is None) and (supply_block_price is None)
        and (demand_block_quantity is not None) and (demand_block_price is not None))
    do_eval_p_from_x_s = (
        (fixed_quantity is not None) and (fixed_price is None)
        and (supply_block_quantity is not None) and (supply_block_price is not None)
        and (demand_block_quantity is None) and (demand_block_price is None))
    do_eval_p_from_x_d = (
        (fixed_quantity is not None) and (fixed_price is None)
        and (supply_block_quantity is None) and (supply_block_price is None)
        and (demand_block_quantity is not None) and (demand_block_price is not None))
    
    assert(do_eval_x_p_from_s_d or do_eval_x_from_p_s or do_eval_x_from_p_d or do_eval_p_from_x_s or do_eval_p_from_x_d)

    s_exists = (do_eval_x_p_from_s_d or do_eval_x_from_p_s or do_eval_p_from_x_s)
    d_exists = (do_eval_x_p_from_s_d or do_eval_x_from_p_d or do_eval_p_from_x_d)

    if s_exists:
        assert(supply_block_quantity.size == supply_block_price.size)
        assert(numpy.count_nonzero(numpy.less(supply_block_quantity, 0.0)) == 0)
    if d_exists:
        assert(demand_block_quantity.size == demand_block_price.size)
        assert(numpy.count_nonzero(numpy.less(demand_block_quantity, 0.0)) == 0)

    if do_eval_x_p_from_s_d:
        return eval_x_p_from_s_d(
            supply_block_quantity, supply_block_price,
            demand_block_quantity, demand_block_price)
    if do_eval_x_from_p_s:
        return eval_x_from_p_s(
            fixed_price,
            supply_block_quantity, supply_block_price)
    if do_eval_x_from_p_d:
        return eval_x_from_p_d(
            fixed_price,
            demand_block_quantity, demand_block_price)
    if do_eval_p_from_x_s:
        return eval_p_from_x_s(
            fixed_quantity,
            supply_block_quantity, supply_block_price)
    if do_eval_p_from_x_d:
        return eval_p_from_x_d(
            fixed_quantity,
            demand_block_quantity, demand_block_price)

def eval_x_p_from_s_d(sx, sp, dx, dp):

    x_max = float('inf')
    x_min = -float('inf')
    p_max = float('inf')
    p_min = -float('inf')

    num_s = sx.size
    num_d = dx.size

    # remove zero-x blocks and sort by p
    # could also combine equal-p blocks
    s = (sx, sp)
    s = remove_zero_quantity_blocks_from_curve(s[0], s[1])
    s = sort_supply_curve(s[0], s[1])
    sx = s[0]
    sp = s[1]
    sxc = numpy.cumsum(sx)
    d = (dx, dp)
    d = remove_zero_quantity_blocks_from_curve(d[0], d[1])
    d = sort_demand_curve(d[0], d[1])
    dx = d[0]
    dp = d[1]
    dxc = numpy.cumsum(dx)

    if num_s == 0:
        if num_d == 0:
            x_max = 0.0
            x_min = 0.0
        else: # at least one d block, and it has positive x
            x_max = 0.0
            x_min = 0.0
            p_min = dxp[0]
    else: # at least one s block, and it has positive x
        if num_d == 0:
            x_max = 0.0
            x_min = 0.0
            p_max = sxp[0]
        else: # each curve has at least one block, and both have positive x, so x and p both cannot be infinite
            pass
            # todo
            # i = 0
            # j = 0
            # x_cleared = 0.0
            # done = False
            # while not done:
            #     if

    return (x_max, x_min, p_max, p_min)

def remove_zero_quantity_blocks_from_curve(x, p):

    if x.size > 0:
        nonzero_blocks = numpy.flatnonzero(x)
        return (x[nonzero_blocks], p[nonzero_blocks])
    else:
        return (x, p)

def eval_x_from_p_s(p0, sx, sp):

    x_max = float('inf')
    x_min = -float('inf')
    p_max = float('inf')
    p_min = -float('inf')

    # todo

    return (x_max, x_min, p_max, p_min)

def eval_x_from_p_d(p0, dx, dp):

    x_max = float('inf')
    x_min = -float('inf')
    p_max = float('inf')
    p_min = -float('inf')

    # todo

    return (x_max, x_min, p_max, p_min)

def eval_p_from_x_s(x0, sx, sp):

    x_max = float('inf')
    x_min = -float('inf')
    p_max = float('inf')
    p_min = -float('inf')

    # todo

    return (x_max, x_min, p_max, p_min)

def eval_p_from_x_d(x0, dx, dp):

    x_max = float('inf')
    x_min = -float('inf')
    p_max = float('inf')
    p_min = -float('inf')

    # todo

    return (x_max, x_min, p_max, p_min)

def sort_supply_curve(block_quantity, block_price):

    return sort_curve(block_quantity, block_price, 'supply')

def sort_demand_curve(block_quantity, block_price):

    return sort_curve(block_quantity, block_price, 'demand')

def sort_curve(block_quantity, block_price, supply_demand):

    coef = (1 if supply_demand == 'supply' else -1)
    num_blocks = block_quantity.size
    assert(block_price.size == num_blocks)
    sorted_blocks = numpy.argsort(coef * block_price)
    sorted_block_quantity = block_quantity[sorted_blocks]
    sorted_block_price = block_price[sorted_blocks]
    return (sorted_block_quantity, sorted_block_price)

