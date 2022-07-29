'''
check_data_list.py

python check_data_list.py [-h, --help]
* display help

python check_data.py <-l, --list> <list_file_name>
* perform all checks in a list
* list_file_name is the name of a CSV formatted file in which each row is a desired check,
i.e. a problem file name
* write a directory containing subdirectories, one for each entry in the list, with each subdirectory containing
the output of the check for that entry
i.e. summary.txt, data_errors.txt, ignored_errors.txt
'''

import os, sys, traceback, argparse, subprocess, pathlib
import pandas
from datautilities import utils

out_dir_default = 'checker_output'
out_csv = 'results.csv'
stdout_file = 'stdout.txt'
stderr_file = 'stderr.txt'
summary_file = 'summary.txt'
data_errors_file = 'data_errors.txt'
ignored_errors_file = 'ignored_errors.txt'
solution_errors_file = 'solution_errors.txt'
config_file = 'config.json'
    
if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument("-l", "--list", help="List file - a CSV formatted text file containing a list of problems to check. Each problem should be on one row.")
    parser.add_argument(
        "-c", "--configuration",
        default=str(pathlib.Path(utils.get_C3DataUtilities_dir(), config_file)),
        help="Configuration file")

    out_dir = out_dir_default
    out_dir = pathlib.Path(out_dir).resolve()
    parser.add_argument("-o", "--out_dir", default=str(out_dir), help="Output directory")

    args = parser.parse_args()
    probs_sols = args.list
    out_dir = str(pathlib.Path(args.out_dir).resolve())

    checks = pandas.read_csv(probs_sols, names=['problem', 'solution'])
    num_checks = checks.shape[0]
    checks['problem'] = [str((pathlib.Path(i).resolve()) if not pandas.isna(i) else i) for i in checks['problem']]
    checks['solution'] = [str((pathlib.Path(i).resolve()) if not pandas.isna(i) else i) for i in checks['solution']]
    checks['results_dir'] = [str(pathlib.Path(out_dir, str(i)).resolve()) for i in range(num_checks)]
    checks['return_code'] = -1
    os.mkdir(out_dir)
    for i in range(num_checks):
        problem = checks['problem'].iloc[i]
        solution = checks['solution'].iloc[i]
        check_dir = checks['results_dir'].iloc[i]
        os.mkdir(check_dir)
        stdout = open(check_dir + '/' + stdout_file, 'w')
        stderr = open(check_dir + '/' + stderr_file, 'w')
        results = None
        results = subprocess.run(
            ['python', 'C3DataUtilities/check_data.py'] +
            ['-p', problem] +
            ([] if pandas.isna(solution) else ['-s', solution]) +
            ['-c', args.configuration] +
            ['-m', check_dir + '/' + summary_file] +
            ['-d', check_dir + '/' + data_errors_file] +
            ['-i', check_dir + '/' + ignored_errors_file] +
            ['-u', check_dir + '/' + solution_errors_file],
            stdout=stdout, stderr=stderr)
        print('return_code: {}'.format(results.returncode))
        stdout.close()
        stderr.close()
        checks['return_code'].iloc[i] = results.returncode # SettingWithCopyWarning but it seems to work

    print('checks:')
    print(checks)

    checks.to_csv(out_dir + '/' + out_csv, index=None)

    # if len(sys.argv) > 1:
    #     problem_data_file_name = sys.argv[1]
    # else:
    #     problem_data_file_name = data_file
    # validation.check(problem_data_file_name, summary_file, data_errors_file, ignored_errors_file)
