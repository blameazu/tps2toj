import argparse
import json
import logging
import os
import re
import subprocess
from function import makedirs, copyfile


parser = argparse.ArgumentParser(description='cms2toj')
parser.add_argument('inputpath', type=str, help='輸入資料夾')
parser.add_argument('outputpath', type=str, help='輸出的資料夾')
parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG)
parser.set_defaults(loglevel=logging.INFO)
args = parser.parse_args()
inputpath = args.inputpath
outputpath = args.outputpath

logging.basicConfig(level=args.loglevel, format='%(asctime)s %(levelname)s %(message)s')


with open(os.path.join(inputpath, 'problem.json')) as f:
    data = json.load(f)

makedirs(outputpath)

# conf
conf = {
    'timelimit': 0,
    'memlimit': 0,
    'compile': 'g++',
    'score': 'rate',
    'check': 'diff',
    'test': [],
    'metadata': {},
}
conf['timelimit'] = int(data['time_limit'] * 1000)
conf['memlimit'] = int(data['memory_limit'] * 1024)

# res/testdata / testcases
makedirs(outputpath, 'res/testdata')

datacasemap = {}
offset = 1

subtasks_json_src = os.path.join(inputpath, 'subtasks.json')
mapping_src = os.path.join(inputpath, 'tests', 'mapping')
mapping_data = {}
with open(subtasks_json_src, 'rt', encoding='utf-8') as json_file:
    subtasks_data = json.load(json_file)
for subtask in subtasks_data['subtasks']:
    mapping_data[subtask] = []
with open(mapping_src, 'rt', encoding='utf-8') as mapping_file:
    for row in mapping_file:
        row = row.strip().split(' ')
        datacasemap[row[1]] = offset
        if len(row) == 2:
            mapping_data[row[0]].append(offset)
            copyfile(
                (inputpath, 'tests', '{}.in'.format(row[1])),
                (outputpath, 'res/testdata', '{}.in'.format(offset))
            )
            copyfile(
                (inputpath, 'tests', '{}.out'.format(row[1])),
                (outputpath, 'res/testdata', '{}.out'.format(offset))
            )
            offset += 1

for subtask in mapping_data:
    conf['test'].append({
        'data': mapping_data[subtask],
        'weight': subtasks_data['subtasks'][subtask]['score'],
    })

logging.info('Creating config file')
with open(os.path.join(outputpath, 'conf.json'), 'w') as conffile:
    json.dump(conf, conffile, indent=4)

# http / statements
makedirs(outputpath, 'http')

statement_path = os.path.join(inputpath, 'statement', 'problem.pdf')
if not os.path.exists(statement_path):
    logging.info('No statements')
    statement = None
else:
    logging.info('Copying statements')
    copyfile(
        (statement_path,),
        (outputpath, 'http', 'cont.pdf')
    )

p = subprocess.Popen([
    'tar',
    '-C',
    outputpath,
    '-cJf',
    os.path.join(os.path.dirname(outputpath), '{}.tar.xz'.format(os.path.basename(outputpath))),
    'http',
    'res',
    'conf.json'
])
