'''
'''

import os, sys, subprocess

import datamodel

def get_data_utils_dir():

    return os.path.dirname(os.path.realpath(__file__))

def get_data_model_dir():

    return os.path.dirname(os.path.realpath(datamodel.__file__))

def get_git_info(path):
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
        'query_err': ''
        }

    results = subprocess.run(['git', 'log', '-1'], cwd=path, capture_output=True)

    repo['query_return_code'] = results.returncode
    repo['query_out'] = results.stdout.decode(sys.stdout.encoding)
    repo['query_err'] = results.stderr.decode(sys.stderr.encoding)
    
    if repo['query_return_code'] == 0:
        out_split = repo['query_out'].split('\n')
        repo['commit'] = out_split[0].split('commit')[1].strip()
        repo['author'] = out_split[1].split('Author:')[1].strip()
        repo['date'] = out_split[2].split('Date:')[1].strip()

    return repo

def print_git_info_all():

    git_info = get_git_info(get_data_utils_dir())
    if git_info['query_return_code'] != 0:
        msg = 'get_git_info failed for C3DataUtilities. git_info: {}'.format(git_info)
        #print(msg)
        raise Exception(msg)
    else:
        print('C3DataUtilities commit ID: {}'.format(git_info['commit']))
        print('C3DataUtilities commit date: {}'.format(git_info['date']))

    git_info = get_git_info(get_data_model_dir())
    if git_info['query_return_code'] != 0:
        msg = 'get_git_info failed for Bid-DS-data-model. git_info: {}'.format(git_info)
        #print(msg)
        raise Exception(msg)
    else:
        print('Bid-DS-data-model commit ID: {}'.format(git_info['commit']))
        print('Bid-DS-data-model commit date: {}'.format(git_info['date']))

