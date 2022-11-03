'''

'''

import numpy, networkx, traceback, pprint, json, re, pandas, time
from pydantic.error_wrappers import ValidationError
from datamodel.input.data import InputDataFile
from datamodel.output.data import OutputDataFile
from datautilities import utils, arraydata, evaluation
from datautilities.errors import ModelError, GitError

def write(file_name, mode, text):

    with open(file_name, mode) as f:
        f.write(text)

def read_json(file_name):

    # todo fully decode json so that config prints as a normal python dict
    with open(file_name, 'r') as f:
        data = json.load(f)
    #print('config: {}'.format(config))
    #print(config['timestamp_pattern_str'])
    return data

def write_json(data, file_name):

    with open(file_name, 'w') as f:
        json.dump(data, f)

def get_p_q_linking_geometry(data, config):

    info = {
        i.uid: {
            # basic geometry - exactly one is True, others False
            # narrowest possible description, e.g. a line is not a band
            'plane': False,
            'empty': False,
            'line': False,
            'band': False,
            'cone': False,
            # line/band/cone slope info
            'upper_sloped_up': False,
            'upper_horiz': False,
            'upper_sloped_down': False,
            'lower_sloped_up': False,
            'lower_horiz': False,
            'lower_sloped_down': False,
            # cone orientation info
            'opening_right': False,
            'opening_left': False,
            # line/band/cone constraints
            'qmax0': None,
            'qmin0': None,
            'bmax': None,
            'bmin': None,
            # cone vertex
            'pvx': None,
            'qvx': None,
            # too small nonzero slope errors
            'b_too_small': False,
            'bmax_too_small': False,
            'bmin_too_small': False,
            'bdiff_too_small': False,
        }
        for i in data.network.simple_dispatchable_device
    }

    # set info for each device
    for i in data.network.simple_dispatchable_device:

        # more convenient names to type
        uid = i.uid
        ineq = i.q_bound_cap
        eq = i.q_linear_cap
        b = i.beta if i.q_linear_cap == 1 else None
        bmax = i.beta_ub if i.q_bound_cap == 1 else None
        bmin = i.beta_lb if i.q_bound_cap == 1 else None
        q0 = i.q_0 if i.q_linear_cap == 1 else None
        qmax0 = i.q_0_ub if i.q_bound_cap == 1 else None
        qmin0 = i.q_0_lb if i.q_bound_cap == 1 else None

        # set info for this device
        if ineq == 1: # inequality constraints, so not whole plane
            if bmax != 0.0 and abs(bmax) < config['beta_zero_tol']:
                info[uid]['bmax_too_small'] = True
            if bmin != 0.0 and abs(bmin) < config['beta_zero_tol']:
                info[uid]['bmin_too_small'] = True
            info[uid]['qmax0'] = qmax0
            info[uid]['qmin0'] = qmin0
            info[uid]['bmax'] = bmax
            info[uid]['bmin'] = bmin
            if bmax == bmin: # upper and lower constraints parallel, so not cone
                if qmin0 > qmax0: # empty
                    info[uid]['empty'] = True
                else: # not empty
                    if qmin0 == qmax0: # line
                        info[uid]['line'] = True
                        if bmax == 0.0: # horiz
                            info[uid]['upper_horiz'] = True
                            info[uid]['lower_horiz'] = True
                        else: # sloped
                            if bmax > 0.0: # sloped up
                                info[uid]['upper_sloped_up'] = True
                                info[uid]['lower_sloped_up'] = True
                            else: # sloped down
                                info[uid]['upper_sloped_down'] = True
                                info[uid]['lower_sloped_down'] = True
                    else: # band
                        info[uid]['band'] = True
                        if bmax == 0.0: # horiz
                            info[uid]['upper_horiz'] = True
                            info[uid]['lower_horiz'] = True
                        else: # sloped
                            if bmax > 0.0: # sloped up
                                info[uid]['upper_sloped_up'] = True
                                info[uid]['lower_sloped_up'] = True
                            else: # sloped down
                                info[uid]['upper_sloped_down'] = True
                                info[uid]['lower_sloped_down'] = True
            else: # upper and lower constraints not parallel, so cone
                if abs(bmax - bmin) < config['beta_zero_tol']:
                    info[uid]['bdiff_too_small'] = True
                info[uid]['cone'] = True
                # p vertex
                info[uid]['pvx'] = (qmin0 - qmax0) / (bmax - bmin)
                # q vertex
                if abs(bmax) < abs(bmin):
                    info[uid]['qvx'] = qmax0 + bmax * info[uid]['pvx']
                else:
                    info[uid]['qvx'] = qmin0 + bmin * info[uid]['pvx']
                if bmax > bmin: # opening right
                    info[uid]['opening_right'] = True
                else: # opening left
                    info[uid]['opening_left'] = True
                if bmax == 0.0: # upper constraint horiz
                    info[uid]['upper_horiz'] = True
                else: # upper constraint sloped
                    if bmax > 0.0: # upper constraint sloped up
                        info[uid]['upper_sloped_up'] = True
                    else: # upper constraint sloped down
                        info[uid]['upper_sloped_down'] = True
                if bmin == 0.0: # lower constraint horiz
                    info[uid]['lower_horiz'] = True
                else: # lower constraint sloped
                    if bmin > 0.0: # lower constraint sloped up
                        info[uid]['lower_sloped_up'] = True
                    else: # lower constraint sloped down
                        info[uid]['lower_sloped_down'] = True
        else: # no inequality constraints, so not empty, also not band and not cone
            if eq == 1: # equality constraints, so line
                if b != 0.0 and abs(b) < config['beta_zero_tol']:
                    info[uid]['b_too_small'] = True
                info[uid]['line'] = True
                info[uid]['qmax0'] = q0
                info[uid]['qmin0'] = q0
                info[uid]['bmax'] = b
                info[uid]['bmin'] = b
                if b == 0.0: # horiz line
                    info[uid]['upper_horiz'] = True
                    info[uid]['lower_horiz'] = True
                else: # sloped line
                    if b > 0.0: # sloped up
                        info[uid]['upper_sloped_up'] = True
                        info[uid]['lower_sloped_up'] = True
                    else: # sloped down
                        info[uid]['upper_sloped_down'] = True
                        info[uid]['lower_sloped_down'] = True
            else: # no equality constraints, and no inequality constraints, so whole plane
                info[uid]['plane'] = True

    return info

def compute_max_min_p_from_max_min_p_q_and_linking(p_max, p_min, q_max, q_min, linking):
    '''

    feas, y_max, y_min = compute_max_min_p_from_max_min_p_q_and_linking(p_max, p_min, q_max, q_min, linking)

    Let W be the set of (p,q) satisfying the linking constaints and
    p_min <= p <= p_max and q_min <= q <= q_max.

    determine feas, y_max, y_min, where

    feas =
      True if W is not empty
      False else

    y_max =
      maximum value of p such that (p, q) is in W for some q if W is not empty
      None else

    y_min =
      minimum value of p such that (p, q) is in W for some q if W is not empty
      None else

    If feas is False, y_max and y_min will generally be floats with y_min > y_max.
    In some cases we will return y_max = -float('inf') and y_min = float('inf').
    This happens when the infeasibility is due to nonoverlapping constraints of the form
    q <= q_up and q >= q_lo with q_up < q_lo. In that case nothing about p_min or p_max
    can restore feasibility, so we set y_max = -float('inf') and y_min = float('inf').
    In any case, feas = True if and only if y_min <= y_max.
    '''

    # assume feasible unless prove otherwise
    feas = True

    # start with rectangle bounds on p, then cut them down
    y_max = p_max
    y_min = p_min

    if p_min > p_max: # p bounds infeas
        feas = False
        return feas, y_max, y_min

    if q_min > q_max: # q bounds infeas
        y_max = -float('inf')
        y_min = float('inf')
        feas = False
        return feas, y_max, y_min

    if linking['empty']: # empty linking set is infeas
        y_max = -float('inf')
        y_min = float('inf')
        feas = False
        return feas, y_max, y_min

    if linking['cone']: # cone
        # print('pmax: {}, pmin: {}, qmax: {}, qmin: {}, geometry: {}'.format(p_max, p_min, q_max, q_min, linking))
        # constraints on p implied by upper linking constraint and q_min
        if linking['upper_sloped_up']: # if upper constraint slopes up, then it constrains p from below
            y_min = max(y_min, (q_min - linking['qmax0']) / linking['bmax'])
        elif linking['upper_sloped_down']: # if upper constraint slopes down, then it constrains p from above
            y_max = min(y_max, (q_min - linking['qmax0']) / linking['bmax'])
        elif linking['qmax0'] < q_min: # if upper constraint is horizontal, then q_min can make infeas
            y_max = -float('inf')
            y_min = float('inf')
            feas = False
            return feas, y_max, y_min
        # constraints on p implied by lower linking constraint and q_max
        if linking['lower_sloped_up']: # if lower constraint slopes up, then it constrains p from above
            y_max = min(y_max, (q_max - linking['qmin0']) / linking['bmin'])
        elif linking['lower_sloped_down']: # if lower constraint slopes down, then it constrains p from below
            y_min = max(y_min, (q_max - linking['qmin0']) / linking['bmin'])
        elif linking['qmin0'] > q_max: # if lower constraint is horizontal, then q_max can make infeas
            y_max = -float('inf')
            y_min = float('inf')
            feas = False
            return feas, y_max, y_min
        # constraints on p implied by upper and lower linking constraints
        if linking['opening_right']: # opening right, so vertex constrains p from below
            y_min = max(y_min, linking['pvx'])
        else: # opening left, so vertex constrains p from above
            y_max = min(y_max, linking['pvx'])
        # ready to return
        if y_min > y_max:
            feas = False
        return feas, y_max, y_min

    if linking['band']: # band
        if linking['upper_horiz']: # horizontal band
            if linking['qmax0'] < q_min:
                y_max = -float('inf')
                y_min = float('inf')
                feas = False
                return feas, y_max, y_min
            if linking['qmin0'] > q_max:
                y_max = -float('inf')
                y_min = float('inf')
                feas = False
                return feas, y_max, y_min
        else: # sloped band
            if linking['upper_sloped_up']: # band sloping up
                y_max = min(y_max, (q_max - linking['qmin0']) / linking['bmin'])
                y_min = max(y_min, (q_min - linking['qmax0']) / linking['bmax'])
            else: # band sloping down
                y_max = min(y_max, (q_min - linking['qmax0']) / linking['bmax'])
                y_min = max(y_min, (q_max - linking['qmin0']) / linking['bmin'])
        # ready to return
        if y_min > y_max:
            feas = False
        return feas, y_max, y_min

    if linking['line']: # line
        if linking['upper_horiz']: # horizontal line
            if linking['qmin0'] > q_max:
                y_max = -float('inf')
                y_min = float('inf')
                feas = False
                return feas, y_max, y_min
            if linking['qmax0'] < q_min:
                y_max = -float('inf')
                y_min = float('inf')
                feas = False
                return feas, y_max, y_min
        else: # sloped line
            if linking['upper_sloped_up']: # line sloping up
                y_max = min(y_max, (q_max - linking['qmax0']) / linking['bmax'])
                y_min = max(y_min, (q_min - linking['qmax0']) / linking['bmax'])
            else: # line sloping down
                y_max = min(y_max, (q_min - linking['qmax0']) / linking['bmax'])
                y_min = max(y_min, (q_max - linking['qmax0']) / linking['bmax'])
        # ready to return
        if y_min > y_max:
            feas = False
        return feas, y_max, y_min

    # if we have not returned yet, there is a problem

def scrub_data(problem_file, config_file, scrubbed_problem_file):

    print('scrub problem data and rewrite to new file')

    # read config
    config = read_json(config_file)

    # data file
    print('problem data file: {}\n'.format(problem_file))

    # output file
    print('scrubbed problem data file: {}\n'.format(scrubbed_problem_file))

    # use json? or pydantic model? - json for now
    use_json = True

    if use_json:
        problem_data_dict = read_json(problem_file)
        scrubbed_problem_data_dict = scrub_problem_data_dict(problem_data_dict, config)
        write_json(scrubbed_problem_data_dict, scrubbed_problem_file)
    else:
        problem_data_model = InputDataFile.load(problem_file)
        scrubbed_problem_data_model = scrub_problem_data_model(problem_data_model, config)
        scrubbed_problem_data_model.save(scrubbed_problem_file)

def scrub_problem_data_dict(problem_data_dict, config):

    # todo
    # anonymize UIDs
    # ensure dispatchable device cost functions cover all p-values that may need to be evaluated

    return problem_data_dict

def scrub_problem_data_model(problem_data_model, config):

    return problem_data_model

def check_data(problem_file, solution_file, config_file, summary_csv_file, summary_json_file, problem_errors_file, ignored_errors_file, solution_errors_file):

    # read config
    config = read_json(config_file)

    # open files
    for fn in [summary_csv_file, summary_json_file, problem_errors_file, ignored_errors_file, solution_errors_file]:
        with open(fn, 'w') as f:
            pass

    # summary - write this to the summary file when exiting
    summary = {
        'problem_data_file': problem_file,
        'solution_data_file': solution_file,
        'git_info': {},
        'problem': {},
        'solution': {},
        'evaluation': {}}

    # data files
    print('problem data file: {}\n'.format(problem_file))
    print('solution data file: {}\n'.format(solution_file))

    # git info
    try:
        git_info = utils.get_git_info_all()
        print('git info: {}\n'.format(git_info))
    except GitError:
        print('git info error ignored\n')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())
    except Exception:
        print('git info error ignored\n')
        with open(ignored_errors_file, 'a') as f:
            f.write(traceback.format_exc())
    else:
        summary['git_info'] = git_info

    # read problem data file without validation (faster)
    start_time = time.time()
    try:
        problem_data_dict = read_json(problem_file)
    except Exception as e:
        summary['problem']['pass'] = 0
        write_summary(summary, summary_csv_file, summary_json_file)
        print('data read error - read without validation\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    print('after reading problem without validation, memory info: {}'.format(utils.get_memory_info()))
    end_time = time.time()
    print('read problem data file without validation time: {}'.format(end_time - start_time))

    # read data
    # this is the main part of the run time of the problem data checker
    # on 6000 bus case on constance, this is ~20 sec and the rest is <1 sec
    # in particular, set membership and connectedness are fast even if not implemented efficiently
    # solution read time seems to be about comparable to problem read time
    # (i.e. 5 on D1 which could translate to 10 to 20 sec on D2)
    # not sure yet about larger cases or solution data check or solution eval
    # have not yet implemented more expensive problem data checks - initial AC feas, independent device feas
    # have not yet implemented scrubber - i.e. UID anonymization
    start_time = time.time()
    try:
        data_model = InputDataFile.load(problem_file)
    except ValidationError as e:
        summary['problem']['pass'] = 0
        write_summary(summary, summary_csv_file, summary_json_file)
        print('data read error - pydantic validation\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    print('after reading problem with validation, memory info: {}'.format(utils.get_memory_info()))
    end_time = time.time()
    print('load time: {}'.format(end_time - start_time))

    # independent data model checks
    start_time = time.time()
    try:
        model_checks(data_model, config)
    except ModelError as e:
        summary['problem']['pass'] = 0
        write_summary(summary, summary_csv_file, summary_json_file)
        print('model error - independent checks\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    print('after problem model checks, memory info: {}'.format(utils.get_memory_info()))
    end_time = time.time()
    print('model_checks time: {}'.format(end_time - start_time))

    # connectedness check
    start_time = time.time()
    try:
        connected(data_model, config)
    except ModelError as e:
        summary['problem']['pass'] = 0
        write_summary(summary, summary_csv_file, summary_json_file)
        print('model error - connectedness\n')
        with open(problem_errors_file, 'a') as f:
            f.write(traceback.format_exc())
        raise e
    print('after checking problem connectedness, memory info: {}'.format(utils.get_memory_info()))
    end_time = time.time()
    print('connected time: {}'.format(end_time - start_time))

    # summary
    problem_summary = get_summary(data_model)
    pp = pprint.PrettyPrinter()
    pp.pprint(problem_summary)
    summary['problem'] = problem_summary
    summary['problem']['pass'] = 1

    if solution_file is not None:

        # read solution data file without validation (faster)
        start_time = time.time()
        try:
            solution_data_dict = read_json(solution_file)
        except Error as e:
            summary['solution']['pass'] = 0
            write_summary(summary, summary_csv_file, summary_json_file)
            print('solution read error - read without validation')
            with open(solution_errors_file, 'a') as f:
                f.write(traceback.format_exc())
            raise e
        print('after read solution without validation, memory info: {}'.format(utils.get_memory_info()))
        end_time = time.time()
        print('read solution data file without validation time: {}'.format(end_time - start_time))

        # read solution
        start_time = time.time()
        #print('solution file: {}'.format(solution_file))
        try:
            solution_data_model = OutputDataFile.load(solution_file)
        except ValidationError as e:
            summary['solution']['pass'] = 0
            write_summary(summary, summary_csv_file, summary_json_file)
            print('solution read error - pydantic validation')
            with open(solution_errors_file, 'a') as f:
                f.write(traceback.format_exc())
            raise e
        print('after read solution with validation, memory info: {}'.format(utils.get_memory_info()))
        end_time = time.time()
        print('solution load time: {}'.format(end_time - start_time))
        
        # solution data model checks
        start_time = time.time()
        try:
            solution_model_checks(data_model, solution_data_model, config)
        except ModelError as e:
            summary['solution']['pass'] = 0
            write_summary(summary, summary_csv_file, summary_json_file)
            print('solution model error - independent checks\n')
            with open(solution_errors_file, 'a') as f:
                f.write(traceback.format_exc())
            raise e
        print('after solution_model_checks(), memory info: {}'.format(utils.get_memory_info()))
        end_time = time.time()
        print('solution model_checks time: {}'.format(end_time - start_time))

        # summary
        solution_summary = get_solution_summary(data_model, solution_data_model)
        pp = pprint.PrettyPrinter()
        pp.pprint(solution_summary)
        summary['solution'] = solution_summary
        summary['solution']['pass'] = 1

        # convert problem data to numpy arrays
        start_time = time.time()
        problem_data_array = arraydata.InputData()
        problem_data_array.set_from_data_model(data_model)
        print('after problem_data_array.set_from_data_model(), memory info: {}'.format(utils.get_memory_info()))
        end_time = time.time()
        print('convert problem data to numpy arrays time: {}'.format(end_time - start_time))

        # convert solution data to numpy arrays
        start_time = time.time()
        solution_data_array = arraydata.OutputData()
        solution_data_array.set_from_data_model(problem_data_array, solution_data_model)
        print('after solution_data_array.set_from_data_model(), memory info: {}'.format(utils.get_memory_info()))
        end_time = time.time()
        print('convert solution data to numpy arrays time: {}'.format(end_time - start_time))
        # todo more systematic memory measurement
        # print('bus_t_v numpy array memory info. shape: {}, size: {}, itemsize: {}, size*itemsize: {}, nbytes: {}'.format(
        #     solution_data_array.bus_t_v.shape,
        #     solution_data_array.bus_t_v.size,
        #     solution_data_array.bus_t_v.itemsize,
        #     solution_data_array.bus_t_v.size *
        #     solution_data_array.bus_t_v.itemsize,
        #     solution_data_array.bus_t_v.nbytes))

        # evaluate solution
        start_time = time.time()
        solution_evaluator = evaluation.SolutionEvaluator(problem_data_array, solution_data_array, config=config)
        #solution_evaluator.problem = problem_data_array
        #solution_evaluator.solution = solution_data_array
        solution_evaluator.run()
        print('after solution_evaluator.run(), memory info: {}'.format(utils.get_memory_info()))
        evaluation_summary = solution_evaluator.get_summary()
        infeas_summary = solution_evaluator.get_infeas_summary()
        obj = solution_evaluator.get_obj()
        feas = solution_evaluator.get_feas()
        pp = pprint.PrettyPrinter()
        print('evaluation summary:')
        pp.pprint(evaluation_summary)
        print('infeasibility summary:')
        pp.pprint(infeas_summary)            
        print('feas: {}'.format(feas))
        print('obj: {}'.format(obj))
        summary['evaluation'] = evaluation_summary
        end_time = time.time()
        print('evaluate solution time: {}'.format(end_time - start_time))

        # print('solution data')
        # for s in ['bus', 'shunt', 'simple_dispatchable_device', 'ac_line', 'dc_line', 'two_winding_transformer']:
        #     print('section: {}'.format(s))
        #     for i in solution_data_model.time_series_output.__dict__[s]:
        #         for k, v in i.__dict__.items():
        #             if k == 'uid':
        #                 print('  {}: {}'.format(k, v))
        #             else:
        #                 print('    {}: {}'.format(k, v))            

    write_summary(summary, summary_csv_file, summary_json_file)
    # todo - capture any error messages in json summary file too

    print('end of check_data(), memory info: {}'.format(utils.get_memory_info()))

def write_summary(summary, summary_csv_file=None, summary_json_file=None):

    if summary_csv_file is not None:
        summary_table = pandas.json_normalize(summary)
        summary_table.to_csv(summary_csv_file, index=False)
    if summary_json_file is not None:
        with open(summary_json_file, 'w') as f:
            json.dump(summary, f, indent=4, cls=utils.NpEncoder)

def get_summary(data):

    summary = {}

    network = data.network
    
    summary['general'] = network.general.dict()
    summary['violation costs'] = network.violation_cost.dict()
    
    bus = network.bus
    acl = network.ac_line
    dcl = network.dc_line
    xfr = network.two_winding_transformer
    sh = network.shunt
    sd = network.simple_dispatchable_device
    pd = [i for i in network.simple_dispatchable_device if i.device_type == 'producer']
    cd = [i for i in network.simple_dispatchable_device if i.device_type == 'consumer']
    prz = network.active_zonal_reserve
    qrz = network.reactive_zonal_reserve
    
    num_bus = len(bus)
    num_acl = len(acl)
    num_dcl = len(dcl)
    num_xfr = len(xfr)
    num_sh = len(sh)
    num_sd = len(sd)
    num_pd = len(pd)
    num_cd = len(cd)
    num_prz = len(prz)
    num_qrz = len(qrz)
    
    summary['num buses'] = num_bus
    summary['num ac lines'] = num_acl
    summary['num dc lines'] = num_dcl
    summary['num transformers'] = num_xfr
    summary['num shunts'] = num_sh
    summary['num simple dispatchable devices'] = num_sd
    summary['num producing devices'] = num_pd
    summary['num consuming devices'] = num_cd
    summary['num real power reserve zones'] = num_prz
    summary['num reactive power reserve zones'] = num_qrz
    
    time_series_input = data.time_series_input
    
    ts_general = time_series_input.general
    
    num_t = ts_general.time_periods
    summary['num intervals'] = num_t
    
    ts_intervals = ts_general.interval_duration
    ts_sd = time_series_input.simple_dispatchable_device
    ts_prz = time_series_input.active_zonal_reserve
    ts_qrz = time_series_input.reactive_zonal_reserve

    ctgs = data.reliability.contingency
    num_k = len(ctgs)
    summary['num contingencies'] = num_k

    summary['total duration'] = sum(ts_intervals)
    summary['interval durations'] = ts_intervals
    
    return summary

def get_solution_summary(problem_data, solution_data):

    problem_summary = get_summary(problem_data)
    # todo add solution info - is there anything?
    solution_summary = {}
    return solution_summary

def model_checks(data, config):

    checks = [
        timestamp_start_required,
        timestamp_stop_required,
        timestamp_start_valid,
        timestamp_stop_valid,
        timestamp_start_ge_min,
        total_horizon_le_timestamp_max_minus_start,
        timestamp_stop_le_max,
        timestamp_stop_minus_start_eq_total_horizon,
        # interval_duratations in interval_duration_schedules - distinguish between divisions - TODO
        interval_duration_in_schedules,
        network_and_reliability_uids_not_repeated,
        ts_uids_not_repeated,
        ctg_dvc_uids_in_domain,
        bus_prz_uids_in_domain,
        bus_qrz_uids_in_domain,
        shunt_bus_uids_in_domain,
        sd_bus_uids_in_domain,
        sd_type_in_domain,
        acl_fr_bus_uids_in_domain,
        acl_to_bus_uids_in_domain,
        xfr_fr_bus_uids_in_domain,
        xfr_to_bus_uids_in_domain,
        dcl_fr_bus_uids_in_domain,
        dcl_to_bus_uids_in_domain,
        ts_sd_uids_in_domain,
        ts_sd_uids_cover_domain,
        ts_prz_uids_in_domain,
        ts_prz_uids_cover_domain,
        ts_qrz_uids_in_domain,
        ts_qrz_uids_cover_domain,
        ts_sd_on_status_ub_len_eq_num_t,
        ts_sd_on_status_lb_len_eq_num_t,
        ts_sd_p_lb_len_eq_num_t,
        ts_sd_p_ub_len_eq_num_t,
        ts_sd_q_lb_len_eq_num_t,
        ts_sd_q_ub_len_eq_num_t,
        ts_sd_cost_len_eq_num_t,
        ts_sd_p_reg_res_up_cost_len_eq_num_t,
        ts_sd_p_reg_res_down_cost_len_eq_num_t,
        ts_sd_p_syn_res_cost_len_eq_num_t,
        ts_sd_p_nsyn_res_cost_len_eq_num_t,
        ts_sd_p_ramp_res_up_online_cost_len_eq_num_t,
        ts_sd_p_ramp_res_down_online_cost_len_eq_num_t,
        ts_sd_p_ramp_res_down_offline_cost_len_eq_num_t,
        ts_sd_p_ramp_res_up_offline_cost_len_eq_num_t,
        ts_sd_q_res_up_cost_len_eq_num_t,
        ts_sd_q_res_down_cost_len_eq_num_t,
        ts_prz_ramping_reserve_up_len_eq_num_t,
        ts_prz_ramping_reserve_down_len_eq_num_t,
        ts_qrz_react_up_len_eq_num_t,
        ts_qrz_react_down_len_eq_num_t,
        ts_sd_on_status_lb_le_ub,
        ts_sd_p_lb_le_ub,
        ts_sd_q_lb_le_ub,
        t_d_discrete,
        sd_d_up_0_discrete,
        sd_d_dn_0_discrete,
        sd_d_up_min_discrete,
        sd_d_dn_min_discrete,
        sd_sus_d_dn_max_discrete,
        sd_w_a_en_max_start_discrete,
        sd_w_a_en_max_end_discrete,
        sd_w_a_en_min_start_discrete,
        sd_w_a_en_min_end_discrete,
        sd_w_a_su_max_start_discrete,
        sd_w_a_su_max_end_discrete,
        supc_not_ambiguous,
        sdpc_not_ambiguous,
        ts_sd_cost_function_covers_p_max,
        sd_p_q_linking_set_nonempty,
        sd_p_q_beta_not_too_small,
        sd_p_q_beta_max_not_too_small,
        sd_p_q_beta_min_not_too_small,
        sd_p_q_beta_diff_not_too_small,
        ts_sd_p_q_linking_feas,
        ts_sd_p_q_ramping_feas,
        ts_sd_p_q_linking_ramping_feas,
        sd_t_cost_function_covers_supc,
        sd_t_cost_function_covers_sdpc,
        sd_t_q_max_min_p_q_linking_supc_feasible,
        sd_t_q_max_min_p_q_linking_sdpc_feasible,
        sd_t_supc_sdpc_no_overlap,
        ]
    errors = []
    # try:
    #     timestamp_start_ge_min(data, config)
    # except ModelError as e:
    #     errors.append(e)
    # except Exception as e:
    #     msg = (
    #         'validation.model_checks found errors\n' + 
    #         'number of errors: {}\n'.format(len(errors)) +
    #         '\n'.join([str(e) for e in errors]))
    #     if len(errors) > 0:
    #         raise ModelError(msg)
    #     else:
    #         raise e
    for c in checks:
        try:
            c(data, config)
        except ModelError as e:
            errors.append(e)
        except Exception as e:
            msg = (
                'validation.model_checks found errors\n' + 
                'number of errors: {}\n'.format(len(errors)) +
                '\n'.join([str(e) for e in errors]))
            if len(errors) > 0:
                raise ModelError(msg)
            else:
                raise e
    if len(errors) > 0:
        msg = (
            'validation.model_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(r) for r in errors]))
        raise ModelError(msg)

def solution_model_checks(data, solution_data, config):

    checks = [
        output_ts_uids_not_repeated,
        output_ts_bus_uids_in_domain,
        output_ts_bus_uids_cover_domain,
        output_ts_shunt_uids_in_domain,
        output_ts_shunt_uids_cover_domain,
        output_ts_simple_dispatchable_device_uids_in_domain,
        output_ts_simple_dispatchable_device_uids_cover_domain,
        output_ts_ac_line_uids_in_domain,
        output_ts_ac_line_uids_cover_domain,
        output_ts_dc_line_uids_in_domain,
        output_ts_dc_line_uids_cover_domain,
        output_ts_two_winding_transformer_uids_in_domain,
        output_ts_two_winding_transformer_uids_cover_domain,
        output_ts_bus_vm_len_eq_num_t,
        output_ts_bus_va_len_eq_num_t,
        output_ts_shunt_step_len_eq_num_t,
        output_ts_simple_dispatchable_device_on_status_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_on_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_reg_res_up_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_reg_res_down_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_syn_res_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_nsyn_res_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_up_online_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_down_online_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_up_offline_len_eq_num_t,
        output_ts_simple_dispatchable_device_p_ramp_res_down_offline_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_res_up_len_eq_num_t,
        output_ts_simple_dispatchable_device_q_res_down_len_eq_num_t,
        output_ts_ac_line_on_status_len_eq_num_t,
        output_ts_dc_line_pdc_fr_len_eq_num_t,
        output_ts_dc_line_qdc_fr_len_eq_num_t,
        output_ts_dc_line_qdc_to_len_eq_num_t,
        output_ts_two_winding_transformer_on_status_len_eq_num_t,
        output_ts_two_winding_transformer_tm_len_eq_num_t,
        output_ts_two_winding_transformer_ta_len_eq_num_t,
    ]
    errors = []
    for c in checks:
        try:
            c(data, solution_data, config)
        except ModelError as e:
            errors.append(e)
        except Exception as e:
            msg = (
                'validation.solution_model_checks found errors\n' + 
                'number of errors: {}\n'.format(len(errors)) +
                '\n'.join([str(e) for e in errors]))
            if len(errors) > 0:
                raise ModelError(msg)
            else:
                raise e
    if len(errors) > 0:
        msg = (
            'validation.solution_model_checks found errors\n' + 
            'number of errors: {}\n'.format(len(errors)) +
            '\n'.join([str(r) for r in errors]))
        raise ModelError(msg)

def valid_timestamp_str(timestamp_pattern_str, data):
    '''
    returns True if data is a valid timestamp string else False
    '''

    valid = True
    if not isinstance(data, str):
        valid = False
    elif re.search(timestamp_pattern_str, data) is None:
        valid = False
    return valid

def timestamp_start_required(data, config):

    if config['timestamp_start_required']:
        if data.network.general.timestamp_start is None:
            msg = 'data -> general -> timestamp_start required by config, not present in data'
            raise ModelError(msg)

def timestamp_stop_required(data, config):

    if config['timestamp_stop_required']:
        if data.network.general.timestamp_stop is None:
            msg = 'data -> general -> timestamp_stop required by config, not present in data'
            raise ModelError(msg)

def timestamp_start_valid(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        if not valid_timestamp_str(config['timestamp_pattern_str'], start):
            raise ModelError(
                'data -> general -> timestamp_start not a valid timestamp string - incorrect format. expected: "{}", got: "{}"'.format(
                    config['timestamp_pattern_str'], start))
        try:
            timestamp = pandas.Timestamp(start)
        except:
            raise ModelError(
                'data -> general -> timestamp_start not a valid timestamp string - could not parse data: "{}"'.format(start))            

def timestamp_stop_valid(data, config):

    end = data.network.general.timestamp_stop
    if end is not None:
        if not valid_timestamp_str(config['timestamp_pattern_str'], end):
            raise ModelError(
                'data -> general -> timestamp_stop not a valid timestamp string - incorrect format. expected: "{}", got: "{}"'.format(
                    config['timestamp_pattern_str'], end))
        try:
            timestamp = pandas.Timestamp(end)
        except:
            raise ModelError(
                'data -> general -> timestamp_stop not a valid timestamp string - could not parse data: "{}"'.format(end))            

def timestamp_start_ge_min(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        min_time = config['timestamp_min']
        if pandas.Timestamp(min_time) > pandas.Timestamp(start):
            msg = 'fails {} <= {}. {}: {}, {}: {}'.format(
                'config.timestamp_min', 'data.network.general.timestamp_start',
                'config.timestamp_min', min_time, 'data.network.general.timestamp_start', start)
            raise ModelError(msg)

def total_horizon_le_timestamp_max_minus_start(data, config):

    start = data.network.general.timestamp_start
    if start is not None:
        max_time = config['timestamp_max']
        timestamp_delta = (pandas.Timestamp(max_time) - pandas.Timestamp(start)).total_seconds() / 3600.0
        total_horizon = sum(data.time_series_input.general.interval_duration)
        if total_horizon > timestamp_delta:
            msg = 'fails total_horizon <= timestamp_max - timestamp_start. config.timestamp_max: {}, data.timestamp_start: {}, data.interval_duration: {}, timestamp_max - timestamp_start: {}, sum(interval_duration): {}'.format(
                max_time, start, data.time_series_input.general.interval_duration, timestamp_delta, total_horizon)
            raise ModelError(msg)

def timestamp_stop_le_max(data, config):

    stop = data.network.general.timestamp_stop
    if stop is not None:
        max_time = config['timestamp_max']
        if pandas.Timestamp(max_time) < pandas.Timestamp(stop):
            msg = 'fails {} <= {}. {}: {}, {}: {}'.format(
                'data.network.general.timestamp_stop',
                'config.timestamp_max',
                'data.network.general.timestamp_stop', stop,
                'config.timestamp_max', max_time)
            raise ModelError(msg)

def timestamp_stop_minus_start_eq_total_horizon(data, config):

    start = data.network.general.timestamp_start
    stop = data.network.general.timestamp_stop
    if (start is not None) and (stop is not None):
        timestamp_delta = (pandas.Timestamp(stop) - pandas.Timestamp(start)).total_seconds() / 3600.0
        total_horizon = sum(data.time_series_input.general.interval_duration)
        if abs(timestamp_delta - total_horizon) > config['time_eq_tol']:
            msg = 'fails timestamp_stop - timestamp_start == sum(interval_duration). timestamp_stop: {}, timestamp_start: {}, interval_duration: {}, timestamp_stop - timestamp_start: {}, sum(interval_duration): {}, config.time_eq_tol: {}'.format(
                stop, start, data.time_series_input.general.interval_duration, timestamp_delta, total_horizon, config['time_eq_tol'])
            raise ModelError(msg)

# interval_duratations in interval_duration_schedules - TODO - recognize division
def interval_duration_in_schedules(data, config):
    
    interval_durations = data.time_series_input.general.interval_duration
    num_intervals = len(interval_durations)
    schedules = config['interval_duration_schedules']
    schedules_right_len = [s for s in schedules if len(s) == num_intervals]
    schedules_match = [
        s for s in schedules_right_len
        if all([(s[i] == interval_durations[i]) for i in range(num_intervals)])]
    found = (len(schedules_match) > 0)
    if not found:
        msg = "fails data.time_series_input.general.interval_duration in config.interval_duration_schedules. data: {}, config: {}".format(
            interval_durations, schedules)
        raise ModelError(msg)

def output_ts_uids_not_repeated(data, output_data, config):

    uids = output_data.time_series_output.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in time_series_output section. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def ts_uids_not_repeated(data, config):

    uids = data.time_series_input.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in time_series_input section. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def network_and_reliability_uids_not_repeated(data, config):
    
    uids = data.network.get_uids() + data.reliability.get_uids()
    uids_sorted = sorted(uids)
    uids_set = set(uids_sorted)
    uids_num = {i:0 for i in uids_set}
    for i in uids:
        uids_num[i] += 1
    uids_num_max = max([0] + list(uids_num.values()))
    if uids_num_max > 1:
        msg = "fails uid uniqueness in network and reliability sections. repeated uids (uid, number of occurrences): {}".format(
            [(k, v) for k, v in uids_num.items() if v > 1])
        raise ModelError(msg)

def ctg_dvc_uids_in_domain(data, config):

    # todo make this more efficient
    domain = (
        data.network.get_ac_line_uids() +
        data.network.get_two_winding_transformer_uids() +
        data.network.get_dc_line_uids())
    domain = set(domain)
    num_ctg = len(data.reliability.contingency)
    ctg_comp_not_in_domain = [
        list(set(data.reliability.contingency[i].components).difference(domain))
        for i in range(num_ctg)]
    ctg_idx_comp_not_in_domain = [
        i for i in range(num_ctg)
        if len(ctg_comp_not_in_domain[i]) > 0]
    ctg_comp_not_in_domain = [
        (i, data.reliability.contingency[i].uid, ctg_comp_not_in_domain[i])
        for i in ctg_idx_comp_not_in_domain]
    if len(ctg_idx_comp_not_in_domain) > 0:
        msg = "fails contingency outaged devices in branches. failing contingencies (index, uid, failing devices): {}".format(
            ctg_comp_not_in_domain)
        raise ModelError(msg)

def items_field_in_domain(items, field, domain, items_name, domain_name):
    # todo - use this - more efficient than set membership in a loop

    domain_set = set(domain)
    domain_size = len(domain_set)
    values = [getattr(i, field) for i in items]
    values_not_in_domain = set(values).difference(domain_set)
    all_values = list(domain_set) + list(values_not_in_domain)
    all_values_map = {all_values[i]:i for i in range(len(all_values))}
    failures = [(i, items[i].uid, values[i]) for i in range(len(items)) if all_values_map[values[i]] >= domain_size]
    if len(failures) > 0:
        msg = "fails items field in domain. items: {}, field: {}, domain: {}, failing items (index, uid, field value): {}".format(items_name, field, domain_name, failures)
        raise ModelError(msg)

def items_field_cover_domain(items, field, domain, items_name, domain_name):
    # todo - use this - more efficient than set membership in a loop

    values = [getattr(i, field) for i in items]
    values = set(values)
    failures = list(set(domain).difference(values))
    if len(failures) > 0:
        msg = "fails items field cover domain. items: {}, field: {}, domain: {}, failing domain elements: {}".format(items_name, field, domain_name, failures)
        raise ModelError(msg)

def output_ts_bus_uids_in_domain(data, solution, config):

    items = solution.time_series_output.bus
    field = 'uid'
    domain = data.network.get_bus_uids()
    items_name = 'time_series_output.bus'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_bus_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.bus
    field = 'uid'
    domain = data.network.get_bus_uids()
    items_name = 'time_series_output.bus'
    domain_name = 'network.bus.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_shunt_uids_in_domain(data, solution, config):

    items = solution.time_series_output.shunt
    field = 'uid'
    domain = data.network.get_shunt_uids()
    items_name = 'time_series_output.shunt'
    domain_name = 'network.shunt.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_shunt_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.shunt
    field = 'uid'
    domain = data.network.get_shunt_uids()
    items_name = 'time_series_output.shunt'
    domain_name = 'network.shunt.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_simple_dispatchable_device_uids_in_domain(data, solution, config):

    items = solution.time_series_output.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_output.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_simple_dispatchable_device_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_output.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_ac_line_uids_in_domain(data, solution, config):

    items = solution.time_series_output.ac_line
    field = 'uid'
    domain = data.network.get_ac_line_uids()
    items_name = 'time_series_output.ac_line'
    domain_name = 'network.ac_line.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_ac_line_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.ac_line
    field = 'uid'
    domain = data.network.get_ac_line_uids()
    items_name = 'time_series_output.ac_line'
    domain_name = 'network.ac_line.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_dc_line_uids_in_domain(data, solution, config):

    items = solution.time_series_output.dc_line
    field = 'uid'
    domain = data.network.get_dc_line_uids()
    items_name = 'time_series_output.dc_line'
    domain_name = 'network.dc_line.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_dc_line_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.dc_line
    field = 'uid'
    domain = data.network.get_dc_line_uids()
    items_name = 'time_series_output.dc_line'
    domain_name = 'network.dc_line.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def output_ts_two_winding_transformer_uids_in_domain(data, solution, config):

    items = solution.time_series_output.two_winding_transformer
    field = 'uid'
    domain = data.network.get_two_winding_transformer_uids()
    items_name = 'time_series_output.two_winding_transformer'
    domain_name = 'network.two_winding_transformer.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def output_ts_two_winding_transformer_uids_cover_domain(data, solution, config):

    items = solution.time_series_output.two_winding_transformer
    field = 'uid'
    domain = data.network.get_two_winding_transformer_uids()
    items_name = 'time_series_output.two_winding_transformer'
    domain_name = 'network.two_winding_transformer.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def bus_prz_uids_in_domain(data, config):

    # todo - this might be inefficient - can we get it down to just one set difference operation? I think so,
    # look at the set of (i, j) for i in buses for j in reserve_zones[i] and
    # the set of (i, j) for i in buses for j in reserve_zones
    domain = data.network.get_active_zonal_reserve_uids()
    domain = set(domain)
    num_bus = len(data.network.bus)
    bus_prz_not_in_domain = [
        list(set(data.network.bus[i].active_reserve_uids).difference(domain))
        for i in range(num_bus)]
    bus_idx_prz_not_in_domain = [
        i for i in range(num_bus)
        if len(bus_prz_not_in_domain[i]) > 0]
    bus_prz_not_in_domain = [
        (i, data.network.bus[i].uid, bus_prz_not_in_domain[i])
        for i in bus_idx_prz_not_in_domain]
    if len(bus_idx_prz_not_in_domain) > 0:
        msg = "fails bus real power reserve zones in real power reserve zones. failing buses (index, uid, failing zones): {}".format(
            bus_prz_not_in_domain)
        raise ModelError(msg)

def bus_qrz_uids_in_domain(data, config):

    # todo see above todo item in bus_prz_uids_in_domain
    domain = data.network.get_reactive_zonal_reserve_uids()
    domain = set(domain)
    num_bus = len(data.network.bus)
    bus_qrz_not_in_domain = [
        list(set(data.network.bus[i].reactive_reserve_uids).difference(domain))
        for i in range(num_bus)]
    bus_idx_qrz_not_in_domain = [
        i for i in range(num_bus)
        if len(bus_qrz_not_in_domain[i]) > 0]
    bus_qrz_not_in_domain = [
        (i, data.network.bus[i].uid, bus_qrz_not_in_domain[i])
        for i in bus_idx_qrz_not_in_domain]
    if len(bus_idx_qrz_not_in_domain) > 0:
        msg = "fails bus reactive power reserve zones in reactive power reserve zones. failing buses (index, uid, failing zones): {}".format(
            bus_qrz_not_in_domain)
        raise ModelError(msg)

def shunt_bus_uids_in_domain(data, config):

    items = data.network.shunt
    field = 'bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.shunt'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def sd_bus_uids_in_domain(data, config):

    items = data.network.simple_dispatchable_device
    field = 'bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.simple_dispatchable_device'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def sd_type_in_domain(data, config):

    items = data.network.simple_dispatchable_device
    field = 'device_type'
    domain = ['producer', 'consumer']
    items_name = 'network.simple_dispatchable_device'
    domain_name = str(domain)
    items_field_in_domain(items, field, domain, items_name, domain_name)

def acl_fr_bus_uids_in_domain(data, config):

    start_time = time.time()

    ### should be fast
    items = data.network.ac_line
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.ac_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

    ### might be slower - no difference though on 6000 bus case on constance
    # domain = data.network.get_bus_uids()
    # domain = set(domain)
    # num_dvc = len(data.network.ac_line)
    # dvc_idx_bus_not_in_domain = [
    #     i for i in range(num_dvc)
    #     if not (data.network.ac_line[i].fr_bus in domain)]
    # dvc_bus_not_in_domain = [
    #     (i, data.network.ac_line[i].uid, data.network.ac_line[i].fr_bus)
    #     for i in dvc_idx_bus_not_in_domain]
    # if len(dvc_idx_bus_not_in_domain) > 0:
    #     msg = "fails ac line from bus in buses. failing devices (index, uid, from bus uid): {}".format(
    #         dvc_bus_not_in_domain)
    #     raise ModelError(msg)

    end_time = time.time()
    print('acl_fr_bus_uids_in_domain time: {}'.format(end_time - start_time))

def acl_to_bus_uids_in_domain(data, config):

    items = data.network.ac_line
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.ac_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def xfr_fr_bus_uids_in_domain(data, config):

    items = data.network.two_winding_transformer
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.two_winding_transformer'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def xfr_to_bus_uids_in_domain(data, config):

    items = data.network.two_winding_transformer
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.two_winding_transformer'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def dcl_fr_bus_uids_in_domain(data, config):

    items = data.network.dc_line
    field = 'fr_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.dc_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def dcl_to_bus_uids_in_domain(data, config):

    items = data.network.dc_line
    field = 'to_bus'
    domain = data.network.get_bus_uids()
    items_name = 'network.dc_line'
    domain_name = 'network.bus.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_sd_uids_in_domain(data, config):

    items = data.time_series_input.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_input.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_sd_uids_cover_domain(data, config):

    items = data.time_series_input.simple_dispatchable_device
    field = 'uid'
    domain = data.network.get_simple_dispatchable_device_uids()
    items_name = 'time_series_input.simple_dispatchable_device'
    domain_name = 'network.simple_dispatchable_device.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_prz_uids_in_domain(data, config):

    items = data.time_series_input.active_zonal_reserve
    field = 'uid'
    domain = data.network.get_active_zonal_reserve_uids()
    items_name = 'time_series_input.active_zonal_reserve'
    domain_name = 'network.active_zonal_reserve.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_prz_uids_cover_domain(data, config):

    items = data.time_series_input.active_zonal_reserve
    field = 'uid'
    domain = data.network.get_active_zonal_reserve_uids()
    items_name = 'time_series_input.active_zonal_reserve'
    domain_name = 'network.active_zonal_reserve.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_qrz_uids_in_domain(data, config):

    items = data.time_series_input.reactive_zonal_reserve
    field = 'uid'
    domain = data.network.get_reactive_zonal_reserve_uids()
    items_name = 'time_series_input.reactive_zonal_reserve'
    domain_name = 'network.reactive_zonal_reserve.uid'
    items_field_in_domain(items, field, domain, items_name, domain_name)

def ts_qrz_uids_cover_domain(data, config):
    
    items = data.time_series_input.reactive_zonal_reserve
    field = 'uid'
    domain = data.network.get_reactive_zonal_reserve_uids()
    items_name = 'time_series_input.reactive_zonal_reserve'
    domain_name = 'network.reactive_zonal_reserve.uid'
    items_field_cover_domain(items, field, domain, items_name, domain_name)

def ts_sd_on_status_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'on_status_ub')

def ts_sd_on_status_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'on_status_lb')

def ts_sd_p_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_lb')

def ts_sd_p_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ub')

def ts_sd_q_lb_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_lb')

def ts_sd_q_ub_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_ub')

def ts_sd_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'cost')

def ts_sd_p_reg_res_up_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_reg_res_up_cost')

def ts_sd_p_reg_res_down_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_reg_res_down_cost')

def ts_sd_p_syn_res_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_syn_res_cost')

def ts_sd_p_nsyn_res_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_nsyn_res_cost')

def ts_sd_p_ramp_res_up_online_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_up_online_cost')

def ts_sd_p_ramp_res_down_online_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_down_online_cost')

def ts_sd_p_ramp_res_down_offline_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_down_offline_cost')

def ts_sd_p_ramp_res_up_offline_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'p_ramp_res_up_offline_cost')

def ts_sd_q_res_up_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_res_up_cost')

def ts_sd_q_res_down_cost_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'simple_dispatchable_device', 'q_res_down_cost')

def ts_prz_ramping_reserve_up_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'active_zonal_reserve', 'RAMPING_RESERVE_UP')

def ts_prz_ramping_reserve_down_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'active_zonal_reserve', 'RAMPING_RESERVE_DOWN')

def ts_qrz_react_up_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'reactive_zonal_reserve', 'REACT_UP')

def ts_qrz_react_down_len_eq_num_t(data, config):
    
    ts_component_field_len_eq_num_t(data, 'reactive_zonal_reserve', 'REACT_DOWN')

def ts_component_field_len_eq_num_t(data, component, field):

    num_t = len(data.time_series_input.general.interval_duration)
    component_uids = [c.uid for c in getattr(data.time_series_input, component)]
    component_lens = [len(getattr(c, field)) for c in getattr(data.time_series_input, component)]
    idx_err = [
        (i, component_uids[i], component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_input {} len({}) == len(intervals). len(intervals): {}. failing items (idx, uid, len({})): {}".format(
            component, field, num_t, field, idx_err)
        raise ModelError(msg)

def output_ts_component_field_len_eq_num_t(data, solution, component, field):

    num_t = len(data.time_series_input.general.interval_duration)
    component_uids = [c.uid for c in getattr(solution.time_series_output, component)]
    component_lens = [len(getattr(c, field)) for c in getattr(solution.time_series_output, component)]
    idx_err = [
        (i, component_uids[i], component_lens[i])
        for i in range(len(component_lens))
        if component_lens[i] != num_t]
    if len(idx_err) > 0:
        msg = "fails time_series_output {} len({}) == len(time_series_input.intervals). len(intervals): {}. failing items (idx, uid, len({})): {}".format(
            component, field, num_t, field, idx_err)
        raise ModelError(msg)

def output_ts_bus_vm_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'bus', 'vm')

def output_ts_bus_va_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'bus', 'va')
    
def output_ts_shunt_step_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'shunt', 'step')

def output_ts_simple_dispatchable_device_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'on_status')

def output_ts_simple_dispatchable_device_p_on_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_on')

def output_ts_simple_dispatchable_device_q_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q')

def output_ts_simple_dispatchable_device_p_reg_res_up_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_reg_res_up')

def output_ts_simple_dispatchable_device_p_reg_res_down_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_reg_res_down')

def output_ts_simple_dispatchable_device_p_syn_res_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_syn_res')

def output_ts_simple_dispatchable_device_p_nsyn_res_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_nsyn_res')

def output_ts_simple_dispatchable_device_p_ramp_res_up_online_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_up_online')

def output_ts_simple_dispatchable_device_p_ramp_res_down_online_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_down_online')

def output_ts_simple_dispatchable_device_p_ramp_res_up_offline_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_up_offline')

def output_ts_simple_dispatchable_device_p_ramp_res_down_offline_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'p_ramp_res_down_offline')

def output_ts_simple_dispatchable_device_q_res_up_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q_res_up')

def output_ts_simple_dispatchable_device_q_res_down_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'simple_dispatchable_device', 'q_res_down')

def output_ts_ac_line_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'ac_line', 'on_status')

def output_ts_dc_line_pdc_fr_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'pdc_fr')

def output_ts_dc_line_qdc_fr_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'qdc_fr')

def output_ts_dc_line_qdc_to_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'dc_line', 'qdc_to')

def output_ts_two_winding_transformer_on_status_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'on_status')

def output_ts_two_winding_transformer_tm_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'tm')

def output_ts_two_winding_transformer_ta_len_eq_num_t(data, solution, config):
    
    output_ts_component_field_len_eq_num_t(data, solution, 'two_winding_transformer', 'ta')

def ts_sd_on_status_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.on_status_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.on_status_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device on_status_lb <= on_status_ub. failures (device index, device uid, interval index, on_status_lb, on_status_ub): {}".format(idx_err)
        raise ModelError(msg)

def supc_not_ambiguous(data, config):
    '''
    check that:

    for each dispatchable device j
    for each interval t
    the set T_supc[j,t] of intervals in the startup trajectory of device j for startup in interval t
    is unambiguously defined
    Specifically, membership of an interval t1 in this set depends on a floating point computation,
    and this check requires that the result of that computation should be sufficiently far from a threshold,
    so that no alternative organization of the computation could have arrived at a different determination
    of memebership of t1 in T_supc[j,t].
    We say t1 is in T_supc[j,t] if the computed value p_supc[j,t,t1] > 0.0.
    unmbiguity requires that p_supc[j,t,t1] be not close to 0.0,
    and the tolerance is contained in config.
    If p_supc[j,t,t1] is too close to 0.0, then there is some ambiguity on whether t1 should be considered
    as part of the startup trajectory or not.
    The data needs to be set up so that no such ambiguity occurs.
    '''

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]

    # time it here. If this is expensive we might need to re-think the organization of the code
    # so as to only get the su/sd trajectories once.
    start_time = time.time()
    sd_t_supc = get_supc(data, config, check_ambiguous=True)
    #sd_t_supc = get_supc(data, config, check_ambiguous=True, debug=True) 
    end_time = time.time()
    print('get_supc time: {}'.format(end_time - start_time))

    idx_err = [(i, t) for i in range(num_sd) for t in range(num_t) if sd_t_supc[i][t][1] is not None]
    if len(idx_err) > 0:
        errors = [(sd_uid[i[0]], i[1], sd_t_supc[i[0]][i[1]][0], sd_t_supc[i[0]][i[1]][1]) for i in idx_err]
        msg = 'fails startup trajectory unambiguous, i.e. p-value too close to 0.0. tolerance: {}. failures (device uid, startup interval index, startup trajectory list of (t, p), ambiguous (t, p)): {}'.format(config['su_sd_pc_zero_tol'], errors)
        raise ModelError(msg)

def sdpc_not_ambiguous(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_t_sdpc = get_sdpc(data, config, check_ambiguous=True)
    idx_err = [(i, t) for i in range(num_sd) for t in range(num_t) if sd_t_sdpc[i][t][1] is not None]
    if len(idx_err) > 0:
        errors = [(sd_uid[i[0]], i[1], sd_t_sdpc[i[0]][i[1]][0], sd_t_sdpc[i[0]][i[1]][1]) for i in idx_err]
        msg = 'fails shutdown trajectory unambiguous, i.e. p-value too close to 0.0. tolerance: {}. failures (device uid, shutdown interval index, shutdown trajectory list of (t, p), ambiguous (t, p)): {}'.format(config['su_sd_pc_zero_tol'], errors)
        raise ModelError(msg)

def sd_t_cost_function_covers_supc(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_t_supc = get_supc(data, config, check_ambiguous=False)
    sd_t_cpmax = get_sd_t_cost_function_pmax(data)
    idx_err = [
        (sd_uid[i], t, c[0], c[1], sd_t_cpmax[i][c[0]])
        for i in range(num_sd) for t in range(num_t) for c in sd_t_supc[i][t]
        if c[1] > sd_t_cpmax[i][c[0]]]
    if len(idx_err) > 0:
        msg = 'fails startup trajectory covered by energy cost function. failures (device uid, startup interval index, uncovered interval index, uncovered trajectory p value, cost function p max): {}'.format(idx_err)
        raise ModelError(msg)

def sd_t_cost_function_covers_sdpc(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_t_sdpc = get_sdpc(data, config, check_ambiguous=False)
    sd_t_cpmax = get_sd_t_cost_function_pmax(data)
    idx_err = [
        (sd_uid[i], t, c[0], c[1], sd_t_cpmax[i][c[0]])
        for i in range(num_sd) for t in range(num_t) for c in sd_t_sdpc[i][t]
        if c[1] > sd_t_cpmax[i][c[0]]]
    if len(idx_err) > 0:
        msg = 'fails shutdown trajectory covered by energy cost function. failures (device uid, shutdown interval index, uncovered interval index, uncovered trajectory p value, cost function p max): {}'.format(idx_err)
        raise ModelError(msg)

def sd_t_q_max_min_p_q_linking_supc_feasible(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_p_q_eq = [(c.q_linear_cap == 1) for c in data.network.simple_dispatchable_device]
    sd_p_q_ineq = [(c.q_bound_cap == 1) for c in data.network.simple_dispatchable_device]
    sd_q_0 = [(c.q_0 if c.q_linear_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_q_max_0 = [(c.q_0_ub if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_q_min_0 = [(c.q_0_lb if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta = [(c.beta if c.q_linear_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta_max = [(c.beta_ub if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta_min = [(c.beta_lb if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_supc = get_supc(data, config, check_ambiguous=False)
    sd_t_qmax = [sd_ts_dict[sd_uid[i]].q_ub for i in range(num_sd)]
    sd_t_qmin = [sd_ts_dict[sd_uid[i]].q_lb for i in range(num_sd)]
    idx_err_eq = [
        (i, sd_uid[i], t, c[0], c[1])
        for i in range(num_sd) if sd_p_q_eq[i]
        for t in range(num_t) for c in sd_t_supc[i][t]
        if (sd_q_0[i] + sd_beta[i] * c[1] > sd_t_qmax[i][c[0]] or
            sd_q_0[i] + sd_beta[i] * c[1] < sd_t_qmin[i][c[0]])]
    idx_err_ineq = [
        (i, sd_uid[i], t, c[0], c[1])
        for i in range(num_sd) if sd_p_q_ineq[i]
        for t in range(num_t) for c in sd_t_supc[i][t]
        if (sd_q_min_0[i] + sd_beta_min[i] * c[1] > sd_t_qmax[i][c[0]] or
            sd_q_max_0[i] + sd_beta_max[i] * c[1] < sd_t_qmin[i][c[0]] or
            sd_q_min_0[i] + sd_beta_min[i] * c[1] > sd_q_max_0[i] + sd_beta_max[i] * c[1])]
    idx_err_eq = [
        (i[1], i[2], i[3], i[4], sd_p_q_eq[i[0]], sd_p_q_ineq[i[0]],
         sd_q_0[i[0]], sd_q_max_0[i[0]], sd_q_min_0[i[0]],
         sd_beta[i[0]], sd_beta_max_0[i[0]], sd_beta_min[i[0]],
         sd_q_0[i[0]] + sd_beta[i[0]] * i[4], sd_q_0[i[0]] + sd_beta[i[0]] * i[4],
         sd_t_qmax[i[0]][i[3]], sd_t_qmin[i[0]][i[3]])
        for i in idx_err_eq]
    idx_err_ineq = [
        (i[1], i[2], i[3], i[4], sd_p_q_eq[i[0]], sd_p_q_ineq[i[0]],
         sd_q_0[i[0]], sd_q_max_0[i[0]], sd_q_min_0[i[0]],
         sd_beta[i[0]], sd_beta_max[i[0]], sd_beta_min[i[0]],
         sd_q_max_0[i[0]] + sd_beta_max[i[0]] * i[4], sd_q_min_0[i[0]] + sd_beta_min[i[0]] * i[4],
         sd_t_qmax[i[0]][i[3]], sd_t_qmin[i[0]][i[3]])
        for i in idx_err_ineq]
    if len(idx_err_eq) + len(idx_err_ineq) > 0:
        msg = 'fails startup trajectory feasible with respect to q max/min and p-q linking constraints. failures (device uid, startup interval index, infeasible interval index, trajectory p value, p_q_eq, p_q_ineq, q_0, q_max_0, q_min_0, beta, beta_max, beta_min, q_max_computed, q_min_computed, q_max bound, q_min bound): {}'.format(idx_err_eq + idx_err_ineq)
        raise ModelError(msg)

def sd_t_q_max_min_p_q_linking_sdpc_feasible(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_p_q_eq = [(c.q_linear_cap == 1) for c in data.network.simple_dispatchable_device]
    sd_p_q_ineq = [(c.q_bound_cap == 1) for c in data.network.simple_dispatchable_device]
    sd_q_0 = [(c.q_0 if c.q_linear_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_q_max_0 = [(c.q_0_ub if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_q_min_0 = [(c.q_0_lb if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta = [(c.beta if c.q_linear_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta_max = [(c.beta_ub if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_beta_min = [(c.beta_lb if c.q_bound_cap == 1 else None) for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_sdpc = get_sdpc(data, config, check_ambiguous=False)
    sd_t_qmax = [sd_ts_dict[sd_uid[i]].q_ub for i in range(num_sd)]
    sd_t_qmin = [sd_ts_dict[sd_uid[i]].q_lb for i in range(num_sd)]
    idx_err_eq = [
        (i, sd_uid[i], t, c[0], c[1])
        for i in range(num_sd) if sd_p_q_eq[i]
        for t in range(num_t) for c in sd_t_sdpc[i][t]
        if (sd_q_0[i] + sd_beta[i] * c[1] > sd_t_qmax[i][c[0]] or
            sd_q_0[i] + sd_beta[i] * c[1] < sd_t_qmin[i][c[0]])]
    idx_err_ineq = [
        (i, sd_uid[i], t, c[0], c[1])
        for i in range(num_sd) if sd_p_q_ineq[i]
        for t in range(num_t) for c in sd_t_sdpc[i][t]
        if (sd_q_min_0[i] + sd_beta_min[i] * c[1] > sd_t_qmax[i][c[0]] or
            sd_q_max_0[i] + sd_beta_max[i] * c[1] < sd_t_qmin[i][c[0]] or
            sd_q_min_0[i] + sd_beta_min[i] * c[1] > sd_q_max_0[i] + sd_beta_max[i] * c[1])]
    idx_err_eq = [
        (i[1], i[2], i[3], i[4], sd_p_q_eq[i[0]], sd_p_q_ineq[i[0]],
         sd_q_0[i[0]], sd_q_max_0[i[0]], sd_q_min_0[i[0]],
         sd_beta[i[0]], sd_beta_max_0[i[0]], sd_beta_min[i[0]],
         sd_q_0[i[0]] + sd_beta[i[0]] * i[4], sd_q_0[i[0]] + sd_beta[i[0]] * i[4],
         sd_t_qmax[i[0]][i[3]], sd_t_qmin[i[0]][i[3]])
        for i in idx_err_eq]
    idx_err_ineq = [
        (i[1], i[2], i[3], i[4], sd_p_q_eq[i[0]], sd_p_q_ineq[i[0]],
         sd_q_0[i[0]], sd_q_max_0[i[0]], sd_q_min_0[i[0]],
         sd_beta[i[0]], sd_beta_max[i[0]], sd_beta_min[i[0]],
         sd_q_max_0[i[0]] + sd_beta_max[i[0]] * i[4], sd_q_min_0[i[0]] + sd_beta_min[i[0]] * i[4],
         sd_t_qmax[i[0]][i[3]], sd_t_qmin[i[0]][i[3]])
        for i in idx_err_ineq]
    if len(idx_err_eq) + len(idx_err_ineq) > 0:
        msg = 'fails shutdown trajectory feasible with respect to q max/min and p-q linking constraints. failures (device uid, shutdown interval index, infeasible interval index, trajectory p value, p_q_eq, p_q_ineq, q_0, q_max_0, q_min_0, beta, beta_max, beta_min, q_max_computed, q_min_computed, q_max bound, q_min bound): {}'.format(idx_err_eq + idx_err_ineq)
        raise ModelError(msg)

def sd_t_supc_sdpc_no_overlap(data, config):
    '''
    get su/sd trajectories
    for each device J
    for each interval T1 # shutdown interval
    consider minimum downtime
    determine earliest interval T2 > T1 # startup interval
    such that shutting down in T1 and starting up in T2 does not violate the minimum downtime constraint
    '''

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_min_downtime = [c.down_time_lb for c in data.network.simple_dispatchable_device]
    sd_startup_ramp = [c.p_startup_ramp_ub for c in data.network.simple_dispatchable_device]
    sd_shutdown_ramp = [c.p_shutdown_ramp_ub for c in data.network.simple_dispatchable_device]
    t_d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    t_a_end = numpy.cumsum(t_d)
    t_a_start = numpy.zeros(shape=(num_t, ), dtype=float)
    t_a_start[1:num_t] = t_a_end[0:(num_t - 1)]
    supc = get_supc(data, config, check_ambiguous=False)
    sdpc = get_sdpc(data, config, check_ambiguous=False)

    # print('supcs:')
    # print(supc)

    # print('sdpcs:')
    # print(sdpc)

    idx_err = []
    for i in range(num_sd):
        for t1 in range(num_t):
            t2 = sd_t_get_earliest_startup_after_shutdown(t1, sd_min_downtime[i], num_t, t_a_start, config)
            if t2 is not None:
                len_sdpc = len(sdpc[i][t1])
                len_supc = len(supc[i][t2])
                # t1 is the shutdown interval
                # t1 + len_sdpc - 1 is the last interval in the shutdown trajectory
                # t2 is the startup interval
                # t2 - len_supc is the first interval in the startup trajectory
                # so the trajectories overlap if and only if
                # t1 + len_sdpc - 1 >= t2 - len_supc
                if t1 + len_sdpc - 1 >= t2 - len_supc:
                    idx_err.append(
                        (sd_uid[i], t1, t2, sd_min_downtime[i], sd_shutdown_ramp[i], sd_startup_ramp[i],
                         sdpc[i][t1], supc[i][t2]))
    if len(idx_err) > 0:
        msg = 'fails no overlap of shutdown and earliest subsequent startup trajectories. failures (device uid, shutdown interval, startup interval, minimum downtime, shutdown ramp rate, startup ramp rate, shutdown trajectory, startup trajectory): {}'.format(idx_err)
        raise ModelError(msg)

def sd_t_get_earliest_startup_after_shutdown(t_shutdown, min_downtime, num_t, t_a_start, config):
    '''
    If startup in interval T then no shutdown in intervals T' in
    T^dn,min_jt = { T' < T : A^start_T – A^start_T' < D^dn,min }
    I.e. given shutdown in interval T1, earliest possible startup T2 is
    T2 = min { T2 > T1 : A^start_T2 – A^start_T1 >= D^dn,min }
    And we use a tolerance on the time:
    T2 = min { T2 > T1 : A^start_T2 – A^start_T1 >= D^dn,min – config['time_eq_tol'] }
    '''

    assert(t_shutdown >= 0)
    assert(t_shutdown <= num_t - 1)
    t_startup = t_shutdown
    done = False
    while not done:
        t_startup += 1
        if t_startup >= num_t:
            done = True
            t_startup = None
        else:
            if t_a_start[t_startup] - t_a_start[t_shutdown] >= min_downtime - config['time_eq_tol']:
                done = True
    return t_startup

def get_supc(data, config, check_ambiguous=False, debug=False):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_p_min = [sd_ts_dict[i].p_lb for i in sd_uid]
    sd_p_0 = [c.initial_status.p for c in data.network.simple_dispatchable_device]
    sd_p_ru_su = [c.p_startup_ramp_ub for c in data.network.simple_dispatchable_device]

    t_d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    t_a_end = numpy.cumsum(t_d)
    t_a_start = numpy.zeros(shape=(num_t, ), dtype=float)
    t_a_start[1:num_t] = t_a_end[0:(num_t - 1)]

    if debug:
        print('num_t: {}'.format(num_t))
        print('t_a_end: {}'.format(t_a_end))
        print('t_a_start: {}'.format(t_a_start))
        for i in range(num_sd):
            print('sd_uid: {}'.format(sd_uid[i]))
            print('sd_t_p_min: {}'.format(sd_t_p_min[i]))
            print('sd_p_0: {}'.format(sd_p_0[i]))
            print('sd_p_ru_su: {}'.format(sd_p_ru_su[i]))
            for t in [0, num_t - 1]:
                supc = sd_t_get_supc(
                    sd_t_p_min[i], sd_p_0[i], sd_p_ru_su[i], t, num_t, t_a_end, t_a_start, config, debug=True)
                print('supc: {}'.format(supc))

    if check_ambiguous:
        sd_t_supc = [
            [sd_t_get_supc(sd_t_p_min[i], sd_p_0[i], sd_p_ru_su[i], t, num_t, t_a_end, t_a_start, config)
             for t in range(num_t)]
            for i in range(num_sd)]
    else:
        sd_t_supc = [
            [sd_t_get_supc(sd_t_p_min[i], sd_p_0[i], sd_p_ru_su[i], t, num_t, t_a_end, t_a_start, config)[0]
             for t in range(num_t)]
            for i in range(num_sd)]

    return sd_t_supc

def get_sdpc(data, config, check_ambiguous=False, debug=False):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_p_min = [sd_ts_dict[i].p_lb for i in sd_uid]
    sd_p_0 = [c.initial_status.p for c in data.network.simple_dispatchable_device]
    sd_p_rd_sd = [c.p_shutdown_ramp_ub for c in data.network.simple_dispatchable_device]

    t_d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    t_a_end = numpy.cumsum(t_d)
    t_a_start = numpy.zeros(shape=(num_t, ), dtype=float)
    t_a_start[1:num_t] = t_a_end[0:(num_t - 1)]

    if debug:
        print('num_t: {}'.format(num_t))
        print('t_a_end: {}'.format(t_a_end))
        print('t_a_start: {}'.format(t_a_start))
        for i in range(num_sd):
            print('sd_uid: {}'.format(sd_uid[i]))
            print('sd_t_p_min: {}'.format(sd_t_p_min[i]))
            print('sd_p_0: {}'.format(sd_p_0[i]))
            print('sd_p_rd_sd: {}'.format(sd_p_rd_sd[i]))
            for t in [0, num_t - 1]:
                sdpc = sd_t_get_sdpc(
                    sd_t_p_min[i], sd_p_0[i], sd_p_rd_sd[i], t, num_t, t_a_end, t_a_start, config, debug=True)
                print('sdpc: {}'.format(sdpc))
            
    if check_ambiguous:
        sd_t_sdpc = [
            [sd_t_get_sdpc(sd_t_p_min[i], sd_p_0[i], sd_p_rd_sd[i], t, num_t, t_a_end, t_a_start, config)
             for t in range(num_t)]
            for i in range(num_sd)]
    else:
        sd_t_sdpc = [
            [sd_t_get_sdpc(sd_t_p_min[i], sd_p_0[i], sd_p_rd_sd[i], t, num_t, t_a_end, t_a_start, config)[0]
             for t in range(num_t)]
            for i in range(num_sd)]

    return sd_t_sdpc

def sd_t_get_supc(p_min, p_0, p_ru_su, t, num_t, t_a_end, t_a_start, config, debug=False):
    '''
    Get the startup trajectory for a single dispatchable device and a single startup interval

    supc, p_ambiguous = get_supc(p_min, p_0, p_ru_su, t, num_t, t_a_end, t_a_start, config)

    supc = [(t', psu[t']) for t' in [t-1, t-2, ...]] = points on the startup trajectory
    
    supc_ambiguous = None if there is no ambiguity in defining the startup trajectory
    supc_ambiguous = (t', p') where p' is the possible final p-value if there is ambiguity, relative to tolerance

    p_min = array of minimum p-values

    p_0 = initial p-value
    
    p_ru_su = startup ramp up rate
    
    t = interval index when starting up

    num_t = number of intervals

    t_a_end = array of end time values of intervals

    t_a_start = array of start time values of intervals

    config = configuration data
    '''

    supc = []
    supc_ambiguous = None
    done = False
    p_start = p_min[t]
    t_new = t
    p_new = 0.0

    if t_new <= 0:
        done = True

    while not done:
        t_new = t_new - 1
        p_new = p_start - p_ru_su * (t_a_end[t] - t_a_end[t_new])
        if p_new <= config['su_sd_pc_zero_tol']:
            done = True
            if p_new >= -config['su_sd_pc_zero_tol']:
                supc_ambiguous = (t_new, p_new)
        else:
            supc.append((t_new, p_new))
            if t_new <= 0:
                done = True
    
    return supc, supc_ambiguous # todo - check

def sd_t_get_sdpc(p_min, p_0, p_rd_sd, t, num_t, t_a_end, t_a_start, config, debug=False):
    '''
    Get the shutdown trajectory for a single dispatchable device and a single shutdown interval

    sdpc, sdpc_ambiguous = sd_t_get_sdpc(p_min, p_0, p_rd_sd, t, num_t, t_a_end, t_a_start, config)

    sdpc = [(t', psd[t']) for t' in [t-1, t-2, ...]] = points on the shutdown trajectory
    
    sdpc_ambiguous = None if there is no ambiguity in defining the shutdown trajectory
    sdpc_ambiguous = (t', p') where p' is the possible final p-value if there is ambiguity, relative to tolerance

    p_min = array of minimum p-values

    p_0 = initial p-value
    
    p_rd_sd = shutdown ramp down rate
    
    t = interval index when starting up

    num_t = number of intervals

    t_a_end = array of end time values of intervals

    t_a_start = array of start time values of intervals

    config = configuration data
    '''

    sdpc = []
    sdpc_ambiguous = None
    done = False
    if t == 0:
        p_start = p_0
    else:
        p_start = p_min[t - 1]
    t_new = t
    p_new = 0.0

    while not done:
        p_new = p_start - p_rd_sd * (t_a_end[t_new] - t_a_start[t])
        if p_new <= config['su_sd_pc_zero_tol']:
            done = True
            if p_new >= -config['su_sd_pc_zero_tol']:
                sdpc_ambiguous = (t_new, p_new)
        else:
            sdpc.append((t_new, p_new))
            t_new = t_new + 1
            if t_new >= num_t:
                done = True
    
    return sdpc, sdpc_ambiguous # todo - check

def get_sd_t_cost_function_pmax(data):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid: c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_sum_cpmax = [
            [numpy.sum([p[1] for p in sd_ts_dict[sd_uid[i]].cost[t]]) for t in range(num_t)]
        for i in range(num_sd)]
    return sd_t_sum_cpmax

def ts_sd_cost_function_covers_p_max(data, config):
    '''
    check that for each t, the cost function covers pmax
    note - here we are not necessarily covering the startup or shutdown trajectories
    this needs to be checked in some other way
    '''

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.network.simple_dispatchable_device)
    sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
    sd_p0 = [c.initial_status.p for c in data.network.simple_dispatchable_device]
    #sd_p0 = [0.05 for c in data.network.simple_dispatchable_device]
    sd_ts_dict = {c.uid: c for c in data.time_series_input.simple_dispatchable_device}
    sd_t_pmax = [
            sd_ts_dict[sd_uid[i]].p_ub
        for i in range(num_sd)]
    sd_t_cpmax = get_sd_t_cost_function_pmax(data)
    idx_err = [
        (i, sd_uid[i], t, sd_t_pmax[i][t], sd_t_cpmax[i][t])
        for i in range(num_sd) for t in range(num_t) if sd_t_cpmax[i][t] < sd_t_pmax[i][t]]
    pmax_err = [[p[1] for p in sd_ts_dict[sd_uid[i[0]]].cost[i[2]]] for i in idx_err]
    idx_err = [
        (idx_err[i][0], idx_err[i][1], idx_err[i][2], idx_err[i][3], idx_err[i][4], pmax_err[i])
        for i in range(len(idx_err))]
    if len(idx_err) > 0:
        msg = "fails cost function covers p_max for each time. failures (device index, device uid, interval index, p_max, cost_pmax, cost_block_pmax): {}".format(idx_err)
        raise ModelError(msg)

# def ts_sd_cost_function_covers_p_init(data, config):
#     '''
#     check that cost function for time t covers p_init for all t
#     '''

#     num_t = len(data.time_series_input.general.interval_duration)
#     num_sd = len(data.network.simple_dispatchable_device)
#     sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
#     sd_p0 = [c.initial_status.p for c in data.network.simple_dispatchable_device]
#     sd_ts_dict = {c.uid: c for c in data.time_series_input.simple_dispatchable_device}
#     sd_min_t_sum_cpmax = [
#         numpy.amin(
#             [numpy.sum([p[1] for p in sd_ts_dict[sd_uid[i]].cost[t]]) for t in range(num_t)],
#             initial=float('inf'))
#         for i in range(num_sd)]
#     idx_err = [(i, sd_uid[i], sd_p0[i]) for i in range(num_sd) if sd_min_t_sum_cpmax[i] < sd_p0[i]]
#     t_err = [
#         numpy.argmin([numpy.sum([p[1] for p in sd_ts_dict[sd_uid[i[0]]].cost[t]]) for t in range(num_t)])
#         for i in idx_err]
#     pmax_err = [[p[1] for p in sd_ts_dict[sd_uid[idx_err[i][0]]].cost[t_err[i]]] for i in range(len(idx_err))]
#     idx_err = [
#         (idx_err[i][0], idx_err[i][1], t_err[i], idx_err[i][2], sd_min_t_sum_cpmax[idx_err[i][0]], pmax_err[i])
#         for i in range(len(idx_err))]
#     if len(idx_err) > 0:
#         msg = "fails cost function for each time covers p_init. failures worst t for each device (device index, device uid, interval index, p_init, cost_total_pmax, cost_pmax): {}".format(idx_err)
#         raise ModelError(msg)

# def ts_sd_cost_function_covers_p_max(data, config):


#     num_t = len(data.time_series_input.general.interval_duration)
#     num_sd = len(data.network.simple_dispatchable_device)
#     sd_uid = [c.uid for c in data.network.simple_dispatchable_device]
#     sd_p0 = [c.initial_status.p for c in data.network.simple_dispatchable_device]
#     #sd_p0 = [0.05 for c in data.network.simple_dispatchable_device]
#     sd_ts_dict = {c.uid: c for c in data.time_series_input.simple_dispatchable_device}
#     sd_max_t_pmax = [
#         numpy.amax(
#             sd_ts_dict[sd_uid[i]].p_ub,
#             initial=-float('inf'))
#         for i in range(num_sd)]
#     sd_min_t_sum_cpmax = [
#         numpy.amin(
#             [numpy.sum([p[1] for p in sd_ts_dict[sd_uid[i]].cost[t]]) for t in range(num_t)],
#             initial=float('inf'))
#         for i in range(num_sd)]
#     idx_err = [(i, sd_uid[i], sd_max_t_pmax[i]) for i in range(num_sd) if sd_min_t_sum_cpmax[i] < sd_max_t_pmax[i]]
#     t1_err = [
#         numpy.argmin([numpy.sum([p[1] for p in sd_ts_dict[sd_uid[i[0]]].cost[t]]) for t in range(num_t)])
#         for i in idx_err]
#     t2_err = [numpy.argmax(sd_ts_dict[sd_uid[i[0]]].p_ub) for i in idx_err]
#     pmax_err = [[p[1] for p in sd_ts_dict[sd_uid[idx_err[i][0]]].cost[t1_err[i]]] for i in range(len(idx_err))]
#     idx_err = [
#         (idx_err[i][0], idx_err[i][1], t1_err[i], t2_err[i], idx_err[i][2], sd_min_t_sum_cpmax[idx_err[i][0]], pmax_err[i])
#         for i in range(len(idx_err))]
#     if len(idx_err) > 0:
#         msg = "fails cost function for each time (t1) covers p_max for each time (t2). failures worst (t1, t2) for each device (device index, device uid, interval index t1, interval index t2, p_max, cost_total_pmax, cost_pmax): {}".format(idx_err)
#         raise ModelError(msg)

def sd_p_q_linking_set_nonempty(data, config):

    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    # print('geometry:')
    # print(sd_p_q_linking_geometry)
    idx_err = [(k, v['qmax0'], v['qmin0'], v['bmax'], v['bmin']) for k, v in sd_p_q_linking_geometry.items() if v['empty']]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device q_bound_cap either q_0_lb <= q_0_ub or beta_max != beta_min. failures (uid, q_0_ub, q_0_lb, beta_ub, beta_lb): {}".format(idx_err)
        raise ModelError(msg)

def sd_p_q_beta_not_too_small(data, config):

    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    idx_err = [(k, v['b']) for k, v in sd_p_q_linking_geometry.items() if v['b_too_small']]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device q_linear_cap either beta == 0.0 or abs(beta) >= tol. tol = {}. failures (uid, beta): {}".format(config['beta_zero_tol'], idx_err)
        raise ModelError(msg)

def sd_p_q_beta_max_not_too_small(data, config):

    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    idx_err = [(k, v['bmax']) for k, v in sd_p_q_linking_geometry.items() if v['bmax_too_small']]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device q_bound_cap either beta_max == 0.0 or abs(beta_max) >= tol. tol = {}. failures (uid, beta_max): {}".format(config['beta_zero_tol'], idx_err)
        raise ModelError(msg)

def sd_p_q_beta_min_not_too_small(data, config):

    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    idx_err = [(k, v['bmin']) for k, v in sd_p_q_linking_geometry.items() if v['bmin_too_small']]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device q_bound_cap either beta_min == 0.0 or abs(beta_min) >= tol. tol = {}. failures (uid, beta_min): {}".format(config['beta_zero_tol'], idx_err)
        raise ModelError(msg)

def sd_p_q_beta_diff_not_too_small(data, config):

    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    idx_err = [(k, v['bmax'], v['bmin']) for k, v in sd_p_q_linking_geometry.items() if v['bdiff_too_small']]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device q_bound_cap either beta_max == beta_min or abs(beta_max - beta_min) >= tol. tol = {}. failures (uid, beta_max, beta_min): {}".format(config['beta_zero_tol'], idx_err)
        raise ModelError(msg)

def check_p_q_linking_ramping_feas(
        # float t-arrays
        d, # interval duration
        p_max, p_min, q_max, q_min, # max/min p/q (input)
        y_max, y_min, # max and min real power (output)
        # bool t-arrays
        feas, # feasibility (output)
        # dicts
        p_q_linking_geometry=None,
        ramping_info=None,
        debug=False,
):

    if debug:
        print('d: ', d)
        print('p_max: ', p_max)
        print('p_min: ', p_min)
        print('q_max: ', q_max)
        print('q_min: ', q_min)
        print('y_max: ', y_max)
        print('y_min: ', y_min)
        print('feas: ', feas)
        print('p_q_linking_geometry: ', p_q_linking_geometry)
        print('ramping_info: ', ramping_info)

    feas[:] = False
    y_max[:] = 0.0
    y_min[:] = 0.0
    feas_scalar = False
    feas_scalar_2 = False
    y_max_scalar = 0.0
    y_min_scalar = 0.0
    num_t = p_max.size

    y_max[:] = p_max
    y_min[:] = p_min
    numpy.less_equal(y_min, y_max, out=feas)

    if p_q_linking_geometry is not None or ramping_info is not None:
        if ramping_info is not None:
            y_max_scalar = ramping_info['p0']
            y_min_scalar = ramping_info['p0']
            if debug:
                print('y_max_scalar: ', y_max_scalar)
                print('y_min_scalar: ', y_min_scalar)
        for i in range(num_t):
            if debug:
                print('t: ', i)
            if ramping_info is not None:
                y_max_scalar = y_max_scalar + d[i] * ramping_info['pru']
                y_min_scalar = y_min_scalar - d[i] * ramping_info['prd']
                y_max_scalar = min(y_max_scalar, p_max[i])
                y_min_scalar = max(y_min_scalar, p_min[i])
            else:
                y_max_scalar = p_max[i]
                y_min_scalar = p_min[i]
            feas_scalar = (y_min_scalar <= y_max_scalar)
            if debug:
                print('t: ', i)
                print('y_max_scalar: ', y_max_scalar)
                print('y_min_scalar: ', y_min_scalar)
                print('feas_scalar: ', feas_scalar)
            if p_q_linking_geometry is not None:
                feas_scalar_2, y_max_scalar, y_min_scalar = compute_max_min_p_from_max_min_p_q_and_linking(
                    y_max_scalar, y_min_scalar, q_max[i], q_min[i], p_q_linking_geometry)
                feas_scalar = (feas_scalar and feas_scalar_2)
                if debug:
                    print('y_max_scalar: ', y_max_scalar)
                    print('y_min_scalar: ', y_min_scalar)
                    print('feas_scalar: ', feas_scalar)
                    print('feas_scalar_2: ', feas_scalar_2)
            y_max[i] = y_max_scalar
            y_min[i] = y_min_scalar
            feas[i] = feas_scalar
            if debug:
                print('y_max: ', y_max)
                print('y_min: ', y_min)
                print('feas: ', feas)
                if not feas_scalar:
                    debug = False

def ts_sd_p_q_linking_feas(data, config):
    '''
    check that the intersection of the p/q max/min rectangle and the p/q linking constraints is nonempty

    q_linear_cap == 1
    q_0
    beta

    q_bound_cap == 1
    q_0_ub
    q_0_lb
    beta_ub
    beta_lb
    '''

    idx_err = []
    uid_sd_ts_map = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    pmax = numpy.zeros(shape=(num_t, ), dtype=float)
    pmin = numpy.zeros(shape=(num_t, ), dtype=float)
    qmax = numpy.zeros(shape=(num_t, ), dtype=float)
    qmin = numpy.zeros(shape=(num_t, ), dtype=float)
    ymax = numpy.zeros(shape=(num_t, ), dtype=float)
    ymin = numpy.zeros(shape=(num_t, ), dtype=float)
    feas = numpy.zeros(shape=(num_t, ), dtype=bool)
    bool1 = numpy.zeros(shape=(num_t, ), dtype=bool)
    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    for j in range(num_sd):
        sd = data.network.simple_dispatchable_device[j]
        if sd.q_bound_cap == 1 or sd.q_linear_cap == 1:
            sd_ts = uid_sd_ts_map[sd.uid]
            pmax[:] = sd_ts.p_ub
            pmin[:] = sd_ts.p_lb
            qmax[:] = sd_ts.q_ub
            qmin[:] = sd_ts.q_lb
            feas[:] = False
            ymax[:] = 0.0
            ymin[:] = 0.0
            p_q_linking_geometry = sd_p_q_linking_geometry[sd.uid]
            check_p_q_linking_ramping_feas(
                d, pmax, pmin, qmax, qmin, ymax, ymin,
                feas,
                p_q_linking_geometry=p_q_linking_geometry,
                ramping_info=None)
            numpy.logical_not(feas, out=bool1)
            infeas_t = numpy.flatnonzero(bool1)
            idx_err += [
                (sd.uid, t, sd_ts.p_ub[t], sd_ts.p_lb[t], sd_ts.q_ub[t], sd_ts.q_lb[t],
                 sd.q_linear_cap, sd.q_bound_cap, sd.q_0, sd.q_0_ub, sd.q_0_lb, sd.beta, sd.beta_ub, sd.beta_lb,
                 ymax[t], ymin[t])
                for t in infeas_t]
    if len(idx_err) > 0:
        msg = "fails simple_dispatchable_device p/q max/min time series constraints and p/q linking constraints have nonempty intersection. failures (device uid, interval index, pmax, pmin, qmax, qmin, q_linear_cap, q_bound_cap, q_0, q_0_ub, q_0_lb, beta, beta_ub, beta_lb, pmax_implied, pmin_implied): {}".format(idx_err)
        raise ModelError(msg)    

def ts_sd_p_q_ramping_feas(data, config):
    '''
    check that the intersection of the p max/min interval and the p ramping constraints is nonempty
    '''

    idx_err = []
    uid_sd_ts_map = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    pmax = numpy.zeros(shape=(num_t, ), dtype=float)
    pmin = numpy.zeros(shape=(num_t, ), dtype=float)
    qmax = numpy.zeros(shape=(num_t, ), dtype=float)
    qmin = numpy.zeros(shape=(num_t, ), dtype=float)
    ymax = numpy.zeros(shape=(num_t, ), dtype=float)
    ymin = numpy.zeros(shape=(num_t, ), dtype=float)
    feas = numpy.zeros(shape=(num_t, ), dtype=bool)
    bool1 = numpy.zeros(shape=(num_t, ), dtype=bool)
    #sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    found_err = False
    first_err = None
    for j in range(num_sd):
        sd = data.network.simple_dispatchable_device[j]
        if sd.initial_status.on_status == 1:
            sd_ts = uid_sd_ts_map[sd.uid]
            pmax[:] = sd_ts.p_ub
            pmin[:] = sd_ts.p_lb
            qmax[:] = sd_ts.q_ub
            qmin[:] = sd_ts.q_lb
            feas[:] = False
            ymax[:] = 0.0
            ymin[:] = 0.0
            # if sd.q_bound_cap == 1 or sd.q_linear_cap == 1:
            #     p_q_linking_geometry = sd_p_q_linking_geometry[sd.uid]
            # else:
            #     p_q_linking_geometry = None
            #p_q_linking_geometry = None
            check_p_q_linking_ramping_feas(
                d, pmax, pmin, qmax, qmin, ymax, ymin,
                feas,
                p_q_linking_geometry=None,
                ramping_info={'p0': sd.initial_status.p, 'pru': sd.p_ramp_up_ub, 'prd': sd.p_ramp_down_ub},
                #debug=(sd.uid == '')
            )
            numpy.logical_not(feas, out=bool1)
            infeas_t = numpy.flatnonzero(bool1)
            if infeas_t.size > 0:
                t = infeas_t[0]
                idx_err.append(
                    (sd.uid, t, sd.initial_status.on_status, d[0:(t+1)].tolist(),
                     sd_ts.p_ub[0:(t+1)], sd_ts.p_lb[0:(t+1)],
                     sd.initial_status.p, sd.p_ramp_up_ub, sd.p_ramp_down_ub,
                     ymax[0:(t+1)].tolist(), ymin[0:(t+1)].tolist()))
    if len(idx_err) > 0:
        msg = "fails simple_dispatchable_device p max/min time series constraints and p ramping constraints have nonempty intersection. failures (device uid, interval index - first interval per device, u_init, d, pmax, pmin, p_init, pru, prd, pmax_implied, pmin_implied): {}".format(idx_err)
        raise ModelError(msg)    

def ts_sd_p_q_linking_ramping_feas(data, config):
    '''
    check that the intersection of the p/q max/min rectangle and the p/q linking constraints and the p ramping constraints is nonempty

    q_linear_cap == 1
    q_0
    beta

    q_bound_cap == 1
    q_0_ub
    q_0_lb
    beta_ub
    beta_lb
    '''

    idx_err = []
    uid_sd_ts_map = {c.uid:c for c in data.time_series_input.simple_dispatchable_device}
    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    d = numpy.array(data.time_series_input.general.interval_duration, dtype=float)
    pmax = numpy.zeros(shape=(num_t, ), dtype=float)
    pmin = numpy.zeros(shape=(num_t, ), dtype=float)
    qmax = numpy.zeros(shape=(num_t, ), dtype=float)
    qmin = numpy.zeros(shape=(num_t, ), dtype=float)
    ymax = numpy.zeros(shape=(num_t, ), dtype=float)
    ymin = numpy.zeros(shape=(num_t, ), dtype=float)
    feas = numpy.zeros(shape=(num_t, ), dtype=bool)
    bool1 = numpy.zeros(shape=(num_t, ), dtype=bool)
    sd_p_q_linking_geometry = get_p_q_linking_geometry(data, config)
    found_err = False
    first_err = None
    for j in range(num_sd):
        sd = data.network.simple_dispatchable_device[j]
        if sd.initial_status.on_status == 1:
            sd_ts = uid_sd_ts_map[sd.uid]
            pmax[:] = sd_ts.p_ub
            pmin[:] = sd_ts.p_lb
            qmax[:] = sd_ts.q_ub
            qmin[:] = sd_ts.q_lb
            feas[:] = False
            ymax[:] = 0.0
            ymin[:] = 0.0
            if sd.q_bound_cap == 1 or sd.q_linear_cap == 1:
                p_q_linking_geometry = sd_p_q_linking_geometry[sd.uid]
            else:
                p_q_linking_geometry = None
            check_p_q_linking_ramping_feas(
                d, pmax, pmin, qmax, qmin, ymax, ymin,
                feas,
                p_q_linking_geometry=p_q_linking_geometry,
                ramping_info={'p0': sd.initial_status.p, 'pru': sd.p_ramp_up_ub, 'prd': sd.p_ramp_down_ub})
            numpy.logical_not(feas, out=bool1)
            infeas_t = numpy.flatnonzero(bool1)
            if infeas_t.size > 0:
                t = infeas_t[0]
                idx_err.append(
                    (sd.uid, t, sd.initial_status.on_status, d[0:(t+1)].tolist(),
                     sd_ts.p_ub[0:(t+1)], sd_ts.p_lb[0:(t+1)], sd_ts.q_ub[0:(t+1)], sd_ts.q_lb[0:(t+1)],
                     sd.q_linear_cap, sd.q_bound_cap, sd.q_0, sd.q_0_ub, sd.q_0_lb,
                     sd.beta, sd.beta_ub, sd.beta_lb,
                     sd.initial_status.p, sd.p_ramp_up_ub, sd.p_ramp_down_ub,
                     ymax[0:(t+1)].tolist(), ymin[0:(t+1)].tolist()))
    if len(idx_err) > 0:
        msg = "fails simple_dispatchable_device p/q max/min time series constraints and p/q linking constraints and p ramping constraints have nonempty intersection. failures (device uid, interval index - first interval per device, u_init, d, pmax, pmin, qmax, qmin, q_linear_cap, q_bound_cap, q_0, q_0_ub, q_0_lb, beta, beta_ub, beta_lb, p_init, pru, prd, pmax_implied, pmin_implied): {}".format(idx_err)
        raise ModelError(msg)    

def ts_sd_p_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.p_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.p_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device p_lb <= p_ub. failures (device index, device uid, interval index, p_lb, p_ub): {}".format(idx_err)
        raise ModelError(msg)

def ts_sd_q_lb_le_ub(data, config):

    num_t = len(data.time_series_input.general.interval_duration)
    num_sd = len(data.time_series_input.simple_dispatchable_device)
    uid = [c.uid for c in data.time_series_input.simple_dispatchable_device]
    lb = [c.q_lb for c in data.time_series_input.simple_dispatchable_device]
    ub = [c.q_ub for c in data.time_series_input.simple_dispatchable_device]
    idx_err = [(i, uid[i], j, lb[i][j], ub[i][j]) for i in range(num_sd) for j in range(num_t) if lb[i][j] > ub[i][j]]
    if len(idx_err) > 0:
        msg = "fails time_series_input simple_dispatchable_device q_lb <= q_ub. failures (device index, device uid, interval index, q_lb, q_ub): {}".format(idx_err)
        raise ModelError(msg)

def t_d_discrete(data, config):
    '''
    '''

    t = data.time_series_input.general.interval_duration
    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    num_t = len(t)
    idx_err = [(i, t[i]) for i in range(num_t) if abs(0.5 * t[i] / tu - round(0.5 * t[i] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails time_series_input general interval_duration 0.5 * d / TU within TOL of an integer. TU: {}, TOL: {}, failures (t num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_d_up_0_discrete(data, config):
    '''
    '''

    uid = [i.uid for i in data.network.simple_dispatchable_device]
    t = [i.initial_status.accu_up_time for i in data.network.simple_dispatchable_device]
    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    num_sd = len(uid)
    idx_err = [(uid[i], t[i]) for i in range(num_sd) if abs(t[i] / tu - round(t[i] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device initial_status accu_up_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_d_dn_0_discrete(data, config):
    '''
    '''

    uid = [i.uid for i in data.network.simple_dispatchable_device]
    t = [i.initial_status.accu_down_time for i in data.network.simple_dispatchable_device]
    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    num_sd = len(uid)
    idx_err = [(uid[i], t[i]) for i in range(num_sd) if abs(t[i] / tu - round(t[i] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device initial_status accu_down_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_d_up_min_discrete(data, config):
    '''
    '''

    uid = [i.uid for i in data.network.simple_dispatchable_device]
    t = [i.in_service_time_lb for i in data.network.simple_dispatchable_device]
    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    num_sd = len(uid)
    idx_err = [(uid[i], t[i]) for i in range(num_sd) if abs(t[i] / tu - round(t[i] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device in_service_time_lb d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_d_dn_min_discrete(data, config):
    '''
    '''

    uid = [i.uid for i in data.network.simple_dispatchable_device]
    t = [i.down_time_lb for i in data.network.simple_dispatchable_device]
    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    num_sd = len(uid)
    idx_err = [(uid[i], t[i]) for i in range(num_sd) if abs(t[i] / tu - round(t[i] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device down_time_lb d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_sus_d_dn_max_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.startup_states[j][1])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.startup_states))
        if abs(i.startup_states[j][1] / tu - round(i.startup_states[j][1] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device startup_states max_down_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, state num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_en_max_start_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.energy_req_ub[j][0])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.energy_req_ub))
        if abs(i.energy_req_ub[j][0] / tu - round(i.energy_req_ub[j][0] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device energy_req_ub start_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_en_max_end_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.energy_req_ub[j][1])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.energy_req_ub))
        if abs(i.energy_req_ub[j][1] / tu - round(i.energy_req_ub[j][1] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device energy_req_ub end_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_en_min_start_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.energy_req_lb[j][0])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.energy_req_lb))
        if abs(i.energy_req_lb[j][0] / tu - round(i.energy_req_lb[j][0] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device energy_req_lb start_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_en_min_end_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.energy_req_lb[j][1])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.energy_req_lb))
        if abs(i.energy_req_lb[j][1] / tu - round(i.energy_req_lb[j][1] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device energy_req_lb end_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_su_max_start_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.startups_ub[j][0])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.startups_ub))
        if abs(i.startups_ub[j][0] / tu - round(i.startups_ub[j][0] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device startups_ub start_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def sd_w_a_su_max_end_discrete(data, config):
    '''
    '''

    tu = config['minimum_time_unit']
    te = config['float_int_tol']
    idx_err = [
        (i.uid, j, i.startups_ub[j][1])
        for i in data.network.simple_dispatchable_device
        for j in range(len(i.startups_ub))
        if abs(i.startups_ub[j][1] / tu - round(i.startups_ub[j][1] / tu)) > te]
    if len(idx_err) > 0:
        msg = "fails network simple_dispatchable_device startups_ub end_time d / TU within TOL of an integer. TU: {}, TOL: failures (sd uid, constr num, d): {}".format(tu, te, idx_err)
        raise ModelError(msg)

def connected(data, config):
    '''
    check connectedness under the base case and each contingency
    '''
    # todo could use the cleaner interface in utils.get_connected_components and utils.get_bridges

    msg = ""

    # get buses, branches, and contingencies that are relavant to this check
    # i.e. all buses, AC in service branches, contingencies outaging AC in service branches
    buses, branches, ctgs = get_buses_branches_ctgs_on_in_service_ac_network(data)
    num_buses = len(buses)
    num_branches = len(branches)
    num_ctgs = len(ctgs)

    # get uids in natural order (ordinal index -> uid)
    buses_uid = [i.uid for i in buses]
    branches_uid = [i.uid for i in branches]
    branches_fbus_uid = [i.fr_bus for i in branches]
    branches_tbus_uid = [i.to_bus for i in branches]
    ctgs_uid = [i.uid for i in ctgs]
    ctgs_branch_uid = [i.components[0] for i in ctgs] # exactly one branch outaged in each contingency

    # map uids to indices
    bus_uid_map = {buses_uid[i]: i for i in range(num_buses)}
    branch_uid_map = {branches_uid[i]: i for i in range(num_branches)}
    ctg_uid_map = {ctgs_uid[i]: i for i in range(num_ctgs)}

    # get branch outaged by each contingency
    ctgs_branch = [branch_uid_map[i] for i in ctgs_branch_uid]

    # get uids on from and to buses of branch outaged in each contingency
    ctgs_branch_fbus_uid = [branches_fbus_uid[branch_uid_map[i]] for i in ctgs_branch_uid]
    ctgs_branch_tbus_uid = [branches_tbus_uid[branch_uid_map[i]] for i in ctgs_branch_uid]

    # get from and to bus indices on each branch and the branch outaged by each contingency
    branches_fbus = [bus_uid_map[i] for i in branches_fbus_uid]
    branches_tbus = [bus_uid_map[i] for i in branches_tbus_uid]
    ctgs_branch_fbus = [bus_uid_map[i] for i in ctgs_branch_fbus_uid]
    ctgs_branch_tbus = [bus_uid_map[i] for i in ctgs_branch_tbus_uid]

    # get the bus pair (i.e. from and to, listed in natural order) of each branch
    branches_pair = [
        (branches_fbus[i], branches_tbus[i]) # ordered pair (f,t) if f < t
        if (branches_fbus[i] < branches_tbus[i])
        else (branches_tbus[i], branches_fbus[i]) # ordered pair (t,f) if t < t
        for i in range(num_branches)] # note f = t is not possible
    branches_pair_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in branches_pair]
    pairs = list(set(branches_pair))
    num_pairs = len(pairs)
    pairs_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in pairs]

    # get the bus pair of each contingency
    ctgs_pair = [branches_pair[i] for i in ctgs_branch]
    ctgs_pair_uid = [(buses_uid[i[0]], buses_uid[i[1]]) for i in ctgs_pair]
    
    # form graph
    # use only one edge for each bus pair,
    # even if there are multiple branches spanning that pair
    # this will not affect connectedness
    # and as for bridges, just remove the bridges that correspond to pairs spanned by more than one branch
    graph = networkx.Graph()
    graph.add_nodes_from(buses_uid)
    graph.add_edges_from(pairs_uid)

    # check connectedness under the base case
    connected_components = list(networkx.connected_components(graph))
    if len(connected_components) != 1:
        msg += "fails connectedness of graph on all buses and base case in service AC branches. num connected components: {}, expected: 1, components: {}".format(
            len(connected_components), connected_components)

    # what branches span each pair?
    pair_branches = {i:[] for i in pairs}
    for i in range(num_branches):
        j = branches_pair[i]
        pair_branches[j].append(i)
    pair_num_branches = {i:len(pair_branches[i]) for i in pairs}
    #print('pair_num_branches: {}'.format(pair_num_branches))

    # what contingencies outage a branch spanning each pair?
    pair_ctgs = {i:[] for i in pairs}
    for i in range(num_ctgs):
        j = ctgs_pair[i]
        pair_ctgs[j].append(i)

    # check connectedness under each contingency
    bridges_uid = list(networkx.bridges(graph))
    bridges = [(bus_uid_map[i[0]], bus_uid_map[i[1]]) for i in bridges_uid]
    #print('bridges: {}'.format(bridges))
    num_bridges = len(bridges)
    bridges_one_branch = [i for i in bridges if pair_num_branches[i] == 1]
    #print('bridges spanned by one branch: {}'.format(bridges_one_branch))
    num_bridges_one_branch = len(bridges_one_branch)
    #bridges_one_branch_ctgs = [pair_ctgs[i] for i in bridges_one_branch]
    #bridges_one_branch_at_least_one_ctg = [i for i in bridges_one_branch if len(bridges_one_branch_ctgs[i]) > 0]
    disconnecting_ctgs = [j for i in bridges_one_branch for j in pair_ctgs[i]]
    disconnecting_ctgs_uid = [ctgs_uid[i] for i in disconnecting_ctgs]
    if len(disconnecting_ctgs_uid) > 0:
        msg += "fails connectedness of graph on all buses and post-contingency in service AC branches. failing contingencies are those outaging a branch that is a bridge in the graph. num failing contingencies: {}, expected: 0, failing contingencies uid: {}".format(
            len(disconnecting_ctgs_uid), disconnecting_ctgs_uid)

    # report the errors
    if len(msg) > 0:
        raise ModelError(msg)

def get_buses_branches_ctgs_on_in_service_ac_network(data):
    '''
    returns (bu,br,ct) where
    bu is the set of all buses
    br is the set of in service AC branches
    ct is the set of contingencies outaging an in service AC branch
    '''

    buses = data.network.bus
    ac_lines = data.network.ac_line
    in_service_ac_lines = [i for i in ac_lines if i.initial_status.on_status > 0]
    other_ac_lines = [i for i in ac_lines if not (i.initial_status.on_status > 0)]
    transformers = data.network.two_winding_transformer
    in_service_transformers = [i for i in transformers if i.initial_status.on_status > 0]
    other_transformers = [i for i in transformers if not (i.initial_status.on_status > 0)]
    in_service_ac_branches = in_service_ac_lines + in_service_transformers
    num_in_service_ac_branches = len(in_service_ac_branches)
    dc_lines = data.network.dc_line
    other_branches = other_ac_lines + other_transformers + dc_lines
    ctgs = data.reliability.contingency
    ordered_branches = in_service_ac_branches + other_branches
    num_branches = len(ordered_branches)
    ordered_branches_uid = [i.uid for i in ordered_branches]
    ordered_branches_uid_map = {ordered_branches_uid[i]: i for i in range(num_branches)}
    in_service_ac_ctgs = [i for i in ctgs if ordered_branches_uid_map[i.components[0]] < num_in_service_ac_branches]
    return buses, in_service_ac_branches, in_service_ac_ctgs







# def check_connectedness(self):
    
#     buses_id = [r.i for r in self.raw.get_buses()]
#     buses_id = sorted(buses_id)
#     num_buses = len(buses_id)
#     lines_id = [(r.i, r.j, r.ckt) for r in self.raw.get_nontransformer_branches() if r.st == 1] # todo check status
#     num_lines = len(lines_id)
#     xfmrs_id = [(r.i, r.j, r.ckt) for r in self.raw.get_transformers() if r.stat == 1] # todo check status
#     num_xfmrs = len(xfmrs_id)
#     branches_id = lines_id + xfmrs_id
#     num_branches = len(branches_id)
#     branches_id = [(r if r[0] < r[1] else (r[1], r[0], r[2])) for r in branches_id]
#     branches_id = sorted(list(set(branches_id)))
#     ctg_branches_id = [(e.i, e.j, e.ckt) for r in self.con.get_contingencies() for e in r.branch_out_events]
#     ctg_branches_id = [(r if r[0] < r[1] else (r[1], r[0], r[2])) for r in ctg_branches_id]
#     ctg_branches_id = sorted(list(set(ctg_branches_id)))
#     ctg_branches_id_ctg_label_map = {
#         k:[]
#         for k in ctg_branches_id}
#     for r in self.con.get_contingencies():
#         for e in r.branch_out_events:
#             if e.i < e.j:
#                 k = (e.i, e.j, e.ckt)
#             else:
#                 k = (e.j, e.i, e.ckt)
#             ctg_branches_id_ctg_label_map[k].append(r.label)
#     branch_bus_pairs = sorted(list(set([(r[0], r[1]) for r in branches_id])))
#     bus_pair_branches_map = {
#         r:[]
#         for r in branch_bus_pairs}
#     for r in branches_id:
#         bus_pair_branches_map[(r[0], r[1])].append(r)
#     bus_pair_num_branches_map = {
#         k:len(v)
#         for k, v in bus_pair_branches_map.items()}
#     bus_nodes_id = [
#         'node_bus_{}'.format(r) for r in buses_id]
#     extra_nodes_id = [
#         'node_extra_{}_{}_{}'.format(r[0], r[1], r[2])
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     branch_edges = [
#         ('node_bus_{}'.format(r[0]), 'node_bus_{}'.format(r[1]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] == 1
#         for r in bus_pair_branches_map[k]]
#     branch_edge_branch_map = {
#         ('node_bus_{}'.format(r[0]), 'node_bus_{}'.format(r[1])):r
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] == 1
#         for r in bus_pair_branches_map[k]}            
#     extra_edges_1 = [
#         ('node_bus_{}'.format(r[0]), 'node_extra_{}_{}_{}'.format(r[0], r[1], r[2]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     extra_edges_2 = [
#         ('node_bus_{}'.format(r[1]), 'node_extra_{}_{}_{}'.format(r[0], r[1], r[2]))
#         for k in branch_bus_pairs if bus_pair_num_branches_map[k] > 1
#         for r in bus_pair_branches_map[k]]
#     nodes = bus_nodes_id + extra_nodes_id
#     edges = branch_edges + extra_edges_1 + extra_edges_2
#     graph = nx.Graph()
#     graph.add_nodes_from(nodes)
#     graph.add_edges_from(edges)
#     connected_components = list(nx.connected_components(graph))
#     #connected_components = [set(k) for k in connected_components] # todo get only the bus nodes and take only their id number
#     num_connected_components = len(connected_components)

#     # print alert

#     bridges = list(nx.bridges(graph))
#     num_bridges = len(bridges)
#     bridges = sorted(list(set(branch_edges).intersection(set(bridges))))
#     # assert len(bridges) == num_bridges i.e. all bridges are branch edges, i.e. not extra edges. extra edges should be elements of cycles
#     bridges = [branch_edge_branch_map[r] for r in bridges]
#     ctg_bridges = sorted(list(set(bridges).intersection(set(ctg_branches_id))))
#     num_ctg_bridges = len(ctg_bridges)

#     # print alert












        # on_status_ub
        # on_status_lb
        # p_lb
        # p_ub
        # q_lb
        # q_ub
        # cost
        # p_reg_res_up_cost
        # p_reg_res_down_cost
        # p_syn_res_cost
        # p_nsyn_res_cost
        # p_ramp_res_up_online_cost
        # p_ramp_res_down_online_cost
        # p_ramp_res_down_offline_cost
        # p_ramp_res_up_offline_cost
        # q_res_up_cost
        # q_res_down_cost





