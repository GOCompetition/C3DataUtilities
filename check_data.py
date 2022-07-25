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

    parser = argparse.ArgumentParser()

    parser.add_argument("problem", help="The problem file that we are checking")

    args = parser.parse_args()

    print('args:')
    print(args)

    validation.check(args.problem, summary_file, data_errors_file, ignored_errors_file)
