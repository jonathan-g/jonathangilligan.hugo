# -*- coding: utf-8 -*-
"""
Created on Tue Jun 13 18:52:00 2017

@author: Jonathan Gilligan
"""
# import pybtex as pt
import os
import glob
import time
import sys
import shutil
import subprocess
import re
import html
import yaml
# import string
import pybtex.database as ptd

def fix_files(path):
    scratch_path = os.path.join(path, 'scratch')
    if not os.path.isdir(scratch_path):
        os.mkdir(scratch_path)
    for f in os.listdir(path):
        dest = f.lower()
        os.rename(os.path.join(path, f), os.path.join(scratch_path, dest))
        os.rename(os.path.join(scratch_path, dest), os.path.join(path, dest))
    time.sleep(0.5)
    os.rmdir(scratch_path)

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
        files = [ fix_file_ref(f) for f in matches['files'].split(';') ]
        res = matches['prefix'] + ';'.join(files) + matches['suffix'] + '\n'
        return res
    else:
        return s

def process_file_refs(infile, outfile):
    with open(infile, encoding="utf-8") as source:
        lines = source.readlines()
    processed_lines = [ fix_file_refs(li) for li in lines ]
    with open(outfile, 'w', encoding="utf-8") as sink:
        s.writelines(processed_lines)

def preprocess(infile, outfile):
    original = open(infile, encoding="utf-8")
    lines = original.readlines()
    original.close()
    modified = open(outfile, 'w', encoding="utf-8")
    lines = [ re.sub('^( *)[Aa]uthor\\+[Aa][Nn]', '\\1author_an', li) for li in lines ]
    lines = [ fix_file_refs(li) for li in lines ]
    modified.writelines(lines)
    modified.close()

def call_citeproc(source, target):
    os.system('pandoc-citeproc -y ' + source + ' > ' + target)

file_expr = re.compile('^(?P<desc>[^:]*):(?P<path>[^:]+)[\\\\/](?P<file>[^:/\\\\]+):(?P<type>[^:;]*)$')

def extract_file_link(filestr):
    files = filestr.split(';')
    matches = [file_expr.match(s) for s in files ]
    # d = dict([(m.group('desc'), m.group('file')) for m in matches])
    d = [ {'desc':m.group('desc'), 'file': m.group('file')} for m in matches]
    return d

def merge(bitem, yitem):
    fields = ['file', 'title_md', 'booktitle_md', 'note_md', 'amazon', 'preprint']

    for f in fields:
        if f in bitem.fields.keys():
            s = str(bitem.fields[f])
            if f == 'file':
                yitem[f] = extract_file_link(s)
            else:
                yitem[f] = s
    return yitem

def process_item(bitem, yitem):
    yitem = merge(bitem, yitem)
    return yitem

def gen_refs(bibfile):
    target = os.path.splitext(os.path.split(bibfile)[1])[0] + '.yml'
    call_citeproc(bibfile, target)

    bib = ptd.parse_file(bibfile)
    ybib = yaml.load(open(target, encoding = 'utf-8'))

    for yitem in ybib['references']:
        bitem = bib.entries.get(yitem['id'])
        yitem = merge(bitem, yitem)

    yaml.dump(ybib, open('publications.yml', 'w', encoding="utf-8"))
    return ybib

clean_expr = re.compile('[^a-zA-z0-9]+')

def gen_items(bib):
    output_keys = ['title', 'author', 'short_author',
                   'short_title',
                   'container_title', 'collection_title',
                   'editor', 'short_editor',
                   'publisher_place', 'publisher',
                   'genre', 'status',
                   'volume', 'issue', 'page', 'number',
                   'ISBN', 'DOI', # 'URL',
                   'preprint',
                   'issued',
                   'keyword',
                   'note',
                   'file',
                   'amazon',
                   ]
    # title_keys = ['title', 'short_title', 'container_title', 'collection_title']
    if not os.path.exists('content'):
        os.mkdir('content')
    for item in bib:
        key = clean_expr.sub('_', item['id'])
        if 'title-short' in item.keys():
            item['short_title'] = item['title-short']
        if 'container-title' in item.keys():
            item['container_title'] = item['container-title']
        if 'collection-title' in item.keys():
            item['collection_title'] = item['collection-title']
        if 'publisher-place' in item.keys():
            item['publisher_place'] = item['publisher-place']
        if 'author' in item.keys():
            item['short_author'] = [ {'family':n['family'], 'given':re.sub('\\b([A-Z])[a-z][a-z]+\\b', '\\1.', n['given'])} for n in item['author'] ]
        if 'editor' in item.keys():
            item['short_editor'] = [ {'family':n['family'], 'given':re.sub('\\b([A-Z])[a-z][a-z]+\\b', '\\1.', n['given'])} for n in item['editor'] ]
        header_items = dict([(k, v) for (k, v) in item.items() if k in output_keys])
        # for tk in title_keys:
        #     if (tk in header_items.keys()):
        #         header_items[tk] = re.sub('\\^([^\\^]+)\\^', '<sup>\\1</sup>', header_items[tk])
        header_items['id'] = key
        dd = header_items['issued'][0]
        y = int(dd['year'])
        m = 1
        d = 1
        if 'month' in dd.keys():
            m = int(dd['month'])
        if 'day' in dd.keys():
            d = int(dd['day'])
        header_items['date'] = ("%04d-%02d-%02d" % (y, m, d))
        if 'URL' in item.keys():
            header_items['pub_url'] = item['URL']
        if 'preprint' in item.keys():
            header_items['preprint_url'] = item['preprint']
        header_items['pub_type'] = item['type']
        outfile = open(os.path.join('content', key + '.md'), 'w', encoding="utf-8")
        outfile.write('---\n')
        yaml.dump(header_items, outfile)
        outfile.write('---\n')
        abstract = None
        if 'abstract_md' in item.keys():
            abstract = item['abstract_md']
        elif 'abstract' in item.keys():
            abstract = item['abstract']
        if abstract is not None:
            abstract = html.escape(abstract).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
            outfile.write(abstract + '\n')
        outfile.close()

def move_md_files(src = 'content', dest = '../content/publications'):
    files = glob.glob(os.path.join(src, '*.md'))
    if not os.path.isdir(dest):
        os.makedirs(dest)
    for f in files:
        base = os.path.split(f)[1]
        dest_file = os.path.join(dest, base)
        shutil.copyfile(f, dest_file)

def move_pdf_files(src = 'pdfs', dest = '../static/files/pubs/pdfs'):
    files = os.listdir(src)
    if not os.path.isdir(dest):
        os.makedirs(dest)
    for f in files:
        src_file = os.path.join(src, f)
        dest_file = os.path.join(dest, f)
        if os.path.isfile(src_file):
            shutil.copyfile(src_file, dest_file)

def decode_version(s):
    def next_version(ss):
        m = re.search('(?P<major>\\d+)(?P<minor>(\\.\\d+)*)$', ss)
        return [m.groupdict()['major'], m.groupdict()['minor']]
    version = []
    minor = s
    while(len(minor) > 0):
        major, minor = next_version(minor)
        version.append(int(major))
    return version

def pandoc_version_check():
    version_check = subprocess.run(['pandoc-citeproc', '--version'],
                                   stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if (version_check.returncode != 0):
        sys.stderr.writelines(['Error running pandoc-citeproc:',
                               version_check.stderr.strip().decode('utf-8')])
        return None
    version = decode_version(version_check.stdout.strip().decode('utf-8'))
    return (version[0] > 0 or version[1] >= 11)

def main():
    source = sys.argv[1]
    version_ok = pandoc_version_check()
    if version_ok is None:
        sys.stderr.write("Error: Could not find pandoc-citeproc. Try instlling pandoc.")
        return(1)
    if version_ok:
        intermediate = source
    else:
        intermediate = os.path.splitext(source)[0] + "_an" + ".bib"
        preprocess(source, intermediate)
    bib = gen_refs(intermediate)
    gen_items(bib['references'])
    move_md_files()
    move_pdf_files()

if __name__ == '__main__':
    main()
