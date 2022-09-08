'''
Functions needed in various places in datautilities
'''

import os, sys, subprocess, traceback, pathlib, time
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
    elif max_out['abs'] > min_out['abs']:
        out = max_out
    else:
        out = min_out
    return out

def get_max_min(arr, use_max=True, idx_lists=None):
    
    out = {
        'val': None,
        'abs': None,
        'idx_lin': None,
        'idx_int': None,
        'idx': None,
    }
    if arr.size > 0:
        if use_max:
            arg = numpy.argmax(arr)
        else:
            arg = numpy.argmin(arr)
        out['idx_lin'] = arg
        arg_tuple = numpy.unravel_index(arg, shape=arr.shape)
        val = arr[arg_tuple]
        out['val'] = val
        out['abs'] = abs(val)
        out['idx_int'] = arg_tuple
        if idx_lists is not None:
            idx = tuple([idx_lists[i][arg_tuple[i]] for i in range(len(idx_lists))])
            out['idx'] = idx
    return out

def csr_mat_vec_add_to_vec(a, x, out):
    '''
    csr_mat_vec_add_to_vec(a, x, out)

    a - sparse matrix (csr)
    x - vector or dense matrix
    out - vector or dense matrix of the same shape as x
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

def get_connected_components(vertices, od_pairs):
    # vertices should be a list of ints
    # od_pairs should be a list of pairs of ints
    # each int in each element of od_pars should be in vertices

    num_vertices = len(vertices)
    num_edges = len(od_pairs)
    edge_vertices = sorted(list(set([p[0] for p in od_pairs] + [p[1] for p in od_pairs])))
    vertices_in_edges_not_in_vertices = sorted(list(set(edge_vertices).difference(set(vertices))))
    if len(vertices_in_edges_not_in_vertices) > 0:
        print('vertices in edge set but not in vertex set: {}'.format(vertices_in_edges_not_in_vertices))
        assert(len(vertices_in_edges_not_in_vertices) <= 0)
    if num_vertices == 0:
        return []
    g = networkx.Graph()
    g.add_nodes_from(sorted(vertices))
    g.add_edges_from(sorted(od_pairs))
    g_connected_components = networkx.connected_components(g)
    return [sorted(list(c)) for c in g_connected_components]

def get_bridges(od_pairs):
    # input should be a list of pairs of ints
    
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
    pairs_unique = list(set([(p[0], p[1]) for p in pairs_sorted]))
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
