'''
'''

import os, sys, subprocess, traceback, pathlib
import numpy

import datamodel
from datautilities.errors import GitError

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
            idx = [idx_lists[i][arg_tuple[i]] for i in range(len(idx_lists))]
            out['idx'] = idx
    return out
