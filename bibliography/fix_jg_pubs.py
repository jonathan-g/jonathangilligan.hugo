# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 18:52:00 2017

@author: Jonathan Gilligan
"""
# import pybtex as pt
import yaml
import os
import glob
import shutil
import re
import cgi
import string
import time

def fix_files(dir):
    scratch_dir = os.path.join(dir, 'scratch')
    if not os.path.isdir(scratch_dir):
        os.mkdir(scratch_dir)
    for f in os.listdir(dir):
        dest = f.lower()
        os.rename(os.path.join(dir, f), os.path.join(scratch_dir, dest))
        os.rename(os.path.join(scratch_dir, dest), os.path.join(dir, dest))
    time.sleep(0.5)
    os.rmdir(scratch_dir)

def fix_file_ref(s):
    m = re.match("^(?P<prefix>[a-z ]+:)(?P<file>[^:]+)(?P<suffix>:.*$)", s)
    if m is not None:
        matches = m.groupdict()
        res = matches['prefix'] + matches['file'].lower() + matches['suffix']
        return res
    else:
        return s

def fix_file_refs(s):
    m = re.match("^(?P<prefix> *file *= *\\{)(?P<files>[^}]*)(?P<suffix>\\}.*$)", s)
    if m is not None:
        matches = m.groupdict()
        files = [ fix_file_ref(f) for f in string.split(matches['files'], ';') ]
        res = matches['prefix'] + string.join(files,';') + matches['suffix'] + '\n'
        return res
    else:
        return s

def process_file_refs(infile, outfile):
    with open(infile) as input:
        lines = input.readlines()
    processed_lines = [ fix_file_refs(li) for li in lines ]
    with open(outfile, 'w') as output:
        output.writelines(processed_lines)

def preprocess(infile, outfile):
    original = open(infile)
    lines = original.readlines()
    original.close()
    modified = open(outfile, 'w')
    lines = [ re.sub('^( *)[Aa]uthor\\+[Aa][Nn]', '\\1author_an', li) for li in lines ]
    lines = [ fix_file_refs(li) for li in lines ]
    modified.writelines(lines)
    modified.close()

def main():
    try:
        fix_files('pdfs')
    except WindowsError, e:
        print e
    finally:
        pass
    process_file_refs('jg_pubs.bib', 'jg_pubs.bib')

if __name__ == '__main__':
    main()
