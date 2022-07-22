'''
'''

import os, sys, subprocess, traceback

import datamodel
from datautilities.errors import GitError

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
