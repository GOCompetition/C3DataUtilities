'''
'''

import os, sys, subprocess, traceback

import datamodel

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
        'branch': '',
        'commit': '',
        'date': '',
        'query_return_code': 0,
        'query_err': '',
        'exception': '',
        }

    repo['query_path'] = path

    # run "git log"
    results = subprocess.run(['git', 'log', '-1'], cwd=path, capture_output=True)

    repo['query_return_code'] = results.returncode
    repo['query_out'] = results.stdout.decode(sys.stdout.encoding)
    repo['query_err'] = results.stderr.decode(sys.stderr.encoding)
    
    if repo['query_return_code'] == 0:
        try:
            lines = repo['query_out'].split('\n')
            for line in out_split:
                if line.startswith('commit'):
                    repo['commit'] = line.split('commit')[1].strip()
                if line.startswith('Date'):
                    repo['date'] = line.split('Date:')[1].strip()
        except Exception as e:
            repo['exception'] = traceback.format_exc()

    return repo

def print_git_info_all():

    git_info = get_git_info(get_data_utils_dir())
    #git_info = get_git_info('error_dir')
    if git_info['query_return_code'] != 0 or len(git_info['exception']) > 0:
        msg = 'get_git_info failed for C3DataUtilities. git_info: {}'.format(git_info)
        print(msg)
        raise Exception(msg)
    else:
        print('C3DataUtilities commit ID: {}'.format(git_info['commit']))
        print('C3DataUtilities commit date: {}'.format(git_info['date']))

    git_info = get_git_info(get_data_model_dir())
    if git_info['query_return_code'] != 0 or len(git_info['exception']) > 0:
        msg = 'get_git_info failed for Bid-DS-data-model. git_info: {}'.format(git_info)
        print(msg)
        raise Exception(msg)
    else:
        print('Bid-DS-data-model commit ID: {}'.format(git_info['commit']))
        print('Bid-DS-data-model commit date: {}'.format(git_info['date']))

