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
import urllib.parse
# import string
import datetime
from dateutil.parser import parse as duparse
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

fix_file_pattern_1 = re.compile("^(?P<prefix>[a-z ]+:)(?P<file>[^:]+)(?P<suffix>:.*$)")
fix_file_pattern_2 = re.compile("^(?P<prefix> *file *= *\\{)(?P<files>[^}]*)(?P<suffix>\\}.*$)")

def fix_file_ref(s):
    m = fix_file_pattern_1.match(s)
    if m is not None:
        matches = m.groupdict()
        res = matches['prefix'] + matches['file'].lower() + matches['suffix']
        return res
    else:
        return s

def fix_file_refs(s):
    m = fix_file_pattern_2.match(s)
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
        sink.writelines(processed_lines)

patent_strip_pattern = re.compile("[^A-Za-z0-9]+")

def patent_strip(s):
    s = re.sub(patent_strip_pattern, "", s).upper()
    return s

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
    os.system('pandoc ' + source + ' -s -f biblatex -t markdown > ' + target)
    f = open(target, 'rt')
    lines = f.readlines()
    lines = [l for l in lines if l != '---\n']
    f.close()
    f = open(target, 'wt')
    f.writelines(lines)
    f.close()

file_expr = re.compile('^(?P<desc>[^:]*):(?P<path>[^:]+)[\\\\/](?P<file>[^:/\\\\]+):(?P<type>[^:;]*)$')

def extract_file_link(filestr):
    files = filestr.split(';')
    matches = [file_expr.match(s) for s in files ]
    # d = dict([(m.group('desc'), m.group('file')) for m in matches])
    for i in range(len(files)):
        if matches[i] is None:
            print('ERROR: cannot match file string "%s" from "%s".' % (files[i], filestr))
    d = [ {'desc':m.group('desc'), 'file': m.group('file')} for m in matches]
    return d

def merge(bitem, yitem):
    fields = ['file', 'title_md', 'booktitle_md', 'note_md', 'amazon', 'preprint', 'ssrn', 'patent_num']

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
    ybib = yaml.safe_load(open(target, encoding = 'utf-8'))

    for yitem in ybib['references']:
        bitem = bib.entries.get(yitem['id'])
        yitem = merge(bitem, yitem)

    yaml.dump(ybib, open('publications.yml', 'w', encoding="utf-8"))
    return ybib

clean_expr = re.compile('[^a-zA-z0-9]+')

given_s1_expr = re.compile('\\b([A-Z])[a-z]+\\b')
given_s2_expr = re.compile('\\. +')

def shorten_given(s, f):
    s1 = re.sub(given_s1_expr, '\\1.', s)
    s2 = re.sub(given_s2_expr, '.', s1)
    # print('item ', key, ': fam = "', f, '", s = "', s, '", s1 = "', s1, '", s2 = "', s2, '"')
    return s2

def fix_particles(name):
    if ('family' in name.keys()):
        if ('non-dropping-particle' in name.keys()):
            # print('item ', key, ': *** fam = "', name['family'], '", nd part = "', 
            #       name['non-dropping-particle'], '"')
            name['family'] = name['non-dropping-particle'].rstrip() + ' ' +  \
                name['family'].lstrip()
            name.pop('non-dropping-particle')
        if ('dropping-particle' in name.keys()):
            # print('item ', key, ': *** fam = "', name['family'], '", d part = "', 
            #       name['dropping-particle'], '"')
            name['family'] = name['dropping-particle'].rstrip() + ' ' +  \
                name['family'].lstrip()
            name.pop('dropping-particle')
    return name

def gen_items(bib):
    output_keys = ['title', 'author', 'short_author',
                   'short_title',
                   'container_title', 'collection_title',
                   'editor', 'short_editor',
                   'publisher_place', 'publisher',
                   'genre', 'status',
                   'volume', 'issue', 'page', 'number',
                   'ISBN', 'DOI', # 'URL',
                   'pub_url',
                   'preprint',
                   'ssrn',
                   'patent_num',
                   'issued',
                   'keyword',
                   'note',
                   'file',
                   'amazon'
                   ]
    # title_keys = ['title', 'short_title', 'container_title', 'collection_title']
    proxy_pattern = re.compile(r'^(?P<hostname>[a-z0-9-]+)(?P<proxy>\.proxy(\.[a-z0-9-]+)*\.vanderbilt\.edu)')
    abstract_pattern = re.compile(r"(?P<keep>(?P<emph>([*_]+|&quot;))(?P<text>.+)(?P=emph))(?P=text)")
    if not os.path.exists('content'):
        os.mkdir('content')
    for item in bib:
        keys = item.keys()
        key = clean_expr.sub('_', item['id'])
        # print("Item ", key, " has keys ", ', '.join(keys))
        if 'url' in keys: 
          # print(" item ", key, " has url ", item['url'])
          pass
        if 'doi' in keys:
          item['DOI'] = item.pop('doi')
          if 'url' in item.keys():
            # print("Deleting URL for ", key)
            item.pop('url')
        if 'title-short' in keys:
            item['short_title'] = item['title-short']
        if 'container-title' in keys:
            item['container_title'] = item['container-title']
        if 'collection-title' in keys:
            item['collection_title'] = item['collection-title']
        if 'publisher-place' in keys:
            item['publisher_place'] = item['publisher-place']
        if 'author' in keys:
            item['author'] = [ fix_particles(n) for n in item['author']]
            item['short_author'] = [ {'family':n['family'], 'given':shorten_given(n['given'], n['family'])} for n in item['author'] ]
        if 'editor' in keys:
            item['editor'] = [ fix_particles(n) for n in item['editor']]
            item['short_editor'] = [ {'family':n['family'], 'given':shorten_given(n['given'], n['family'])} for n in item['editor'] ]
        header_items = dict([(k, v) for (k, v) in item.items() if k in output_keys])
        # for tk in title_keys:
        #     if (tk in header_items.keys()):
        #         header_items[tk] = re.sub('\\^([^\\^]+)\\^', '<sup>\\1</sup>', header_items[tk])
        header_items['id'] = key
        if ('issued' in header_items.keys()):
          issued = header_items['issued']
          if isinstance(issued, str):
            dt = duparse(issued)
            dd = { 'year': dt.year, 'month': dt.month, 'day': dt.day}
            print("dd = ", dd)
          elif isinstance(issued, tuple) or isinstance(issued, list):
            dd = header_items['issued'][0]
          elif isinstance(issued, datetime.date):
            dd = {'year': issued.year, 'month': issued.month, 'day': issued.day}
          elif isinstance(issued, int):
            dd = {'year': issued}
          else:
            print("issued: type = ", type(issued), ", value = ", issued)
            exit(1)
          header_items['issued'] = dd
          y = int(dd['year'])
          m = 1
          d = 1
          if 'month' in dd.keys():
              m = int(dd['month'])
          if 'day' in dd.keys():
            d = int(dd['day'])
          header_items['date'] = ("%04d-%02d-%02d" % (y, m, d))
          d = datetime.datetime.strptime(header_items['date'], "%Y-%m-%d").date()
          if (d > datetime.date.today()):
              d = datetime.date.today()
          header_items['pubdate'] = d.isoformat()
        else :
          print("No issued date for ", header_items['id'])
          continue
        if 'url' in keys:
            # print("Item ", key, " has an URL")
            if not 'doi' in keys:
              # print("Fixing up URL for item ", key)
              pub_url = item['url']
              split_url = urllib.parse.urlsplit(pub_url)
              hostname = split_url.netloc
              m = proxy_pattern.match(hostname)
              if m:
                gd = m.groupdict()
                if 'proxy' in gd.keys():
                  hostname = gd['hostname'].replace('-', '.')
                  split_url = split_url._replace(netloc = hostname)
                  pub_url = urllib.parse.urlunsplit(split_url)
                  # print("Replacing proxy for item ", key)
              # print("URL for ", key, " is ", pub_url)
              header_items['pub_url'] = pub_url
            else:
              # print("Ignoring URL for item ", key)
              pass
        if 'preprint' in keys:
            header_items['preprint_url'] = item['preprint']
        if 'ssrn' in keys:
            header_items['ssrn_id'] = item['ssrn']
        header_items['pub_type'] = item['type']
        if 'keyword' in header_items.keys():
            k = header_items['keyword']
            k = re.sub("[a-z\\- ]*tenure[a-z\\- ]*", "", k)
            k = re.sub(", *,", ",", k)
            k = re.sub("^, *", "", k)
            k = re.sub(" *, *$", "", k)
            k = k.strip()
            if (len(k) == 0):
                del header_items['keyword']
            else:
                header_items['keyword'] = k
        if (item['type'] == 'patent' and 'number' in item.keys()):
            header_items['patent_num'] = patent_strip(item['number'])
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
            abstract = abstract_pattern.sub(r'\g<keep>', abstract)
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
        if (m):
          return [m.groupdict()['major'], m.groupdict()['minor']]
        else:
          print("Could not parse version ", ss)
    version = []
    minor = s
    while(len(minor) > 0):
        major, minor = next_version(minor)
        version.append(int(major))
    print("Version = ", version)
    return version

def pandoc_version_check():
    version_check = subprocess.run(['pandoc', '--version'],
                                   stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    if (version_check.returncode != 0):
        sys.stderr.writelines(['Error running pandoc:',
                               version_check.stderr.strip().decode('utf-8')])
        return None
    version_str = version_check.stdout.decode('utf-8').split('\n')[0].strip()
    version = decode_version(version_str)
    return (version[0] >= 2 and (version[0] > 2 or version[1] >= 18))

def main():
    source = sys.argv[1]
    version_ok = pandoc_version_check()
    if version_ok is None:
        sys.stderr.write("Error: Could not find pandoc. Try instlling pandoc.")
        return(1)
    if version_ok:
        print("Skipping pre-processing step")
        intermediate = source
    else:
      sys.stderr.write("Error: you need to update Pandoc to version 2.18 or higher.")
      return(1)
    bib = gen_refs(intermediate)
    gen_items(bib['references'])
    move_md_files()
    move_pdf_files()

if __name__ == '__main__':
    main()
