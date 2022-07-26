'''
check_data.py

python check_data.py [-h, --help]
* display help

python check_data.py <problem_file_name>
python check_data.py [-p, --problem] <problem_file_name>
* check a problem file
* write summary.txt, data_errors.txt, ignored_errors.txt

# python check_data.py <problem_file_name> <solution_file_name>
# python check_data.py [-p, --problem] <problem_file_name> [-s, --solution] <solution_file_name>
# * check a problem file and a solution file
# * does not check feasibility of the solution or compute objective
# * this is mainly about formatting
'''

import argparse
from datautilities import validation
    
summary_file = 'summary.txt'
data_errors_file = 'data_errors.txt'
ignored_errors_file = 'ignored_errors.txt'

if __name__ == '__main__':

    msg = '\n'.join([
            'check a problem file.',
            'output files',
            '  summary',
            '  data errors',
            '  ignored errors',
            ])
    parser = argparse.ArgumentParser(description=msg, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    group = parser.add_mutually_exclusive_group()
    group.add_argument("problem_opt", nargs="?", help="The problem file that we are checking - optional positional argument for backward compatibility, do not use with -p")
    group.add_argument("-p", "--problem", help="The problem file that we are checking")

    parser.add_argument("-s", "--solution", help="The solution file that we are checking - not supported yet")
    parser.add_argument("-c", "--configuration", help="Configuration file - not supported yet")
    parser.add_argument("-m", "--summary", default=summary_file, help="Summary output file", )
    parser.add_argument("-d", "--data_errors", default=data_errors_file, help="Data errors output file")
    parser.add_argument("-i", "--ignored_errors", default=ignored_errors_file, help="Ignored errors output file")

    args = parser.parse_args()

    # assert(args.problem is None or args.problem_opt is None)

    # print('args:')
    # print(args)

    if args.problem is not None:
        problem = args.problem
    else:
        problem = args.problem_opt

    validation.check(problem, args.summary, args.data_errors, args.ignored_errors)
