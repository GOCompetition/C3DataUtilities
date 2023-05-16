import json, argparse

def read_json(file_name):

    data = {}
    with open(file_name, 'r') as f:
        data = json.load(f)
    return data

def write_json(data, file_name, sort_keys=False):

    with open(file_name, 'w') as f:
        json.dump(data, f, sort_keys=sort_keys)

def fix_sd_t_u(prob_data, sol_data):
    '''
    set sd u_max[t] and u_min[t] equal to the value of u[t].
    '''
    
    sd_u_sol_dict = {i['uid']: i['on_status'] for i in sol_data['time_series_output']['simple_dispatchable_device']}
    for i in prob_data['time_series_input']['simple_dispatchable_device']:
        i['on_status_ub'] = sd_u_sol_dict[i['uid']]
        i['on_status_lb'] = sd_u_sol_dict[i['uid']]

def fix_sh_t_u(prob_data, sol_data):
    '''
    set sh t u_max and u_min equal to the value of u[t] for t = t_start.
    if there is any switching after the first interval, this will not work well.
    but we cannot enforce bounds on u other than by prohibiting switching.
    print warning if there is switching after the first interval.
    It may be better to leave these variable bounds as they are.
    '''

    pass

def fix_acl_t_u(prob_data, sol_data):
    '''
    set xfr u0 (initial closed/open indicator) to the value of u[t] for t = t_start.
    if there is any switching after the first interval, this will not work well.
    but we cannot enforce bounds on u other than by prohibiting switching.
    print warning if there is switching after the first interval.
    It may work better to leave the initial value as it is and allow switching.
    '''

    pass

def fix_xfr_t_u(prob_data, sol_data):
    '''
    set xfr u0 (initial closed/open indicator) to the value of u[t] for t = t_start.
    if there is any switching after the first interval, this will not work well.
    but we cannot enforce bounds on u other than by prohibiting switching.
    print warning if there is switching after the first interval.
    It may work better to leave the initial value as it is and allow switching.
    '''

    pass

def main(prob_file_name, sol_file_name, new_prob_file_name):

    prob_data = read_json(prob_file_name)
    sol_data = read_json(sol_file_name)
    fix_sd_t_u(prob_data, sol_data)
    fix_sh_t_u(prob_data, sol_data)
    fix_acl_t_u(prob_data, sol_data)
    fix_xfr_t_u(prob_data, sol_data)
    write_json(prob_data, new_prob_file_name)

if __name__ == '__main__':

    msg = '\n'.join([
            'create a problem file from a solution file.',
            'input files',
            '  problem json',
            '  solution json',
            'output files',
            '  new problem json',
            ])

    parser = argparse.ArgumentParser(description=msg, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--problem", help="The problem file input", default=None)
    parser.add_argument("--solution", help="The solution file input", default=None)
    parser.add_argument("--new_problem", help="The new problem file output", default=None)

    args = parser.parse_args()

    print('args:')
    print(args)

    main(args.problem, args.solution, args.new_problem)
