import argparse
import json
import logging
import os
import sys
import lzma
import tarfile
import sys
import lzma
import tarfile
from function import makedirs, copyfile

def progress_bar(ratio, width=40):
    filled = int(width * ratio)
    bar = '#' * filled + '-' * (width - filled)
    sys.stdout.write(f"\rCompression Progess: [{bar}] {ratio*100:5.1f}%")
    sys.stdout.flush()

def make_tar_xz_with_progress(src_dir, dest_path):
    members = []
    base_dir = src_dir
    for root, dirs, files in os.walk(src_dir):
        for fn in files:
            full = os.path.join(root, fn)
            arcname = os.path.relpath(full, base_dir)
            members.append((full, arcname))

    total_bytes = sum(os.path.getsize(full) for full, _ in members)
    processed = 0

    with lzma.open(dest_path, "wb") as xz_out:
        with tarfile.open(mode="w|", fileobj=xz_out) as tar:
            for full, arcname in members:
                tarinfo = tar.gettarinfo(full, arcname)
                with open(full, "rb") as f:
                    tar.addfile(tarinfo, fileobj=f)
                processed += os.path.getsize(full)
                progress_bar(processed / total_bytes)
    sys.stdout.write("\n")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description='cms2toj')
    parser.add_argument('inputpath', type=str, help='input directory')
    parser.add_argument('outputpath', type=str, help='output directory')
    parser.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG)
    parser.set_defaults(loglevel=logging.INFO)
    args = parser.parse_args()
    inputpath = args.inputpath
    outputpath = args.outputpath

    logging.basicConfig(level=args.loglevel, format='%(asctime)s %(levelname)s %(message)s')

    with open(os.path.join(inputpath, 'problem.json'), encoding='utf-8') as f:
        data = json.load(f)

    if os.path.exists(outputpath):
        import shutil
        shutil.rmtree(outputpath)
        
    dirname = os.path.dirname(outputpath)
    basename = os.path.basename(outputpath)
    dest = os.path.join(dirname, f"{basename}.tar.xz")
    if os.path.exists(dest):
        os.remove(dest)
        
    makedirs(outputpath)
    
    conf = {
        'timelimit': int(data['time_limit'] * 1000),
        'memlimit': int(data['memory_limit'] * 1024),
        'score': 'rate',
        'check': 'cms' if data['has_checker'] else 'diff',
        'has_grader': data['has_grader'],
        'test': [],
        'metadata': {},
    }
    
    # res/checker
    if data['has_checker']:
        makedirs(outputpath, 'res/checker')
        copyfile((inputpath, 'checker', "checker.cpp"),
                            (outputpath, 'res/checker', "checker.cpp"))
        copyfile((inputpath, 'checker', "testlib.h"),
                            (outputpath, 'res/checker', "testlib.h"))
        copyfile((inputpath, 'checker', "Makefile"),
                            (outputpath, 'res/checker', "Makefile"))
        
    # res/grader
    if data['has_grader']:
        makedirs(outputpath, 'res/grader/cpp')
        copyfile((inputpath, 'grader/cpp', "grader.cpp"),
                            (outputpath, 'res/grader/cpp', "grader.cpp"))
        copyfile((inputpath, 'grader/cpp', f"{data['name']}.h"),
                            (outputpath, 'res/grader/cpp', f"{data['name']}.h"))

    # res/testdata/testcases
    makedirs(outputpath, 'res/testdata')
    
    datacasemap = {}
    offset = 1

    subtasks_json_src = os.path.join(inputpath, 'subtasks.json')
    mapping_src = os.path.join(inputpath, 'tests', 'mapping')
    mapping_data = {}
    with open(subtasks_json_src, 'rt', encoding='utf-8') as json_file:
        subtasks_data = json.load(json_file)
    for sub in subtasks_data['subtasks']:
        mapping_data[sub] = []
    with open(mapping_src, 'rt', encoding='utf-8') as mapping_file:
        for row in mapping_file:
            parts = row.strip().split()
            datacasemap[parts[1]] = offset
            if len(parts) == 2:
                mapping_data[parts[0]].append(offset)
                copyfile((inputpath, 'tests', f"{parts[1]}.in"),
                        (outputpath, 'res/testdata', f"{offset}.in"))
                copyfile((inputpath, 'tests', f"{parts[1]}.out"),
                        (outputpath, 'res/testdata', f"{offset}.out"))
                offset += 1

    for sub, cases in mapping_data.items():
        conf['test'].append({'data': cases, 
                             'weight': subtasks_data['subtasks'][sub]['score']})

    logging.info('Creating config file')
    with open(os.path.join(outputpath, 'conf.json'), 'w') as conffile:
        json.dump(conf, conffile, indent=4)

    # http/statement
    makedirs(outputpath, 'http')
    statement_path = os.path.join(inputpath, 'statement', 'index.pdf')
    if os.path.exists(statement_path):
        logging.info('Copying statements')
        copyfile((statement_path,), 
                 (outputpath, 'http', 'cont.pdf'))

    logging.info('Start compressing with progress...')
    make_tar_xz_with_progress(outputpath, dest)

if __name__ == '__main__':
    main()