#!/usr/bin/env python
# makes a demo grammar that is compliant with HW4 in form but completely ignores the
# input data (the grammar from the class slides is output instead)

import argparse
import sys
import codecs

import bigfloat

if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
from csv import DictReader, DictWriter
from nltk.grammar import Production
from nltk import Tree
from collections import Counter

scriptdir = os.path.dirname(os.path.abspath(__file__))

reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')


def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

def addonoffarg(parser, arg, dest=None, default=True, help="TODO"):
  ''' add the switches --arg and --no-arg that set parser.arg to true/false, respectively'''
  group = parser.add_mutually_exclusive_group()
  dest = arg if dest is None else dest
  group.add_argument('--%s' % arg, dest=dest, action='store_true', default=default, help=help)
  group.add_argument('--no-%s' % arg, dest=dest, action='store_false', default=default, help="See --%s" % arg)


def main():
  parser = argparse.ArgumentParser(description="ignore input; make a demo grammar that is compliant in form",
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  addonoffarg(parser, 'debug', help="debug mode", default=False)
  parser.add_argument("--infile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input file (ignored)")
  parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file (grammar)")

  try:
    args = parser.parse_args()
  except IOError as msg:
    parser.error(str(msg))

  workdir = tempfile.mkdtemp(prefix=os.path.basename(__file__), dir=os.getenv('TMPDIR', '/tmp'))

  fh = open('pcfg_log', 'w')

  def cleanwork():
    shutil.rmtree(workdir, ignore_errors=True)
  if args.debug:
    print(workdir)
  else:
    atexit.register(cleanwork)

  rule_dict = {}
  rule_freq = {}
  treebank_rules = []
  rule_lhs = []
  infile = prepfile(args.infile, 'r')
  outfile = prepfile(args.outfile, 'w')
  for tree in infile:
    t = Tree.fromstring(tree)
    tree_rules = t.productions()
    for rule in tree_rules:
        rule_lhs.append(rule.lhs())
        treebank_rules.append(rule)
    #print treebank_rules
  freq_dict = Counter(rule_lhs)
  treebank_dict = Counter(treebank_rules)
  for production in treebank_dict.iterkeys():
      count = treebank_dict.get(production)
      prob = bigfloat.bigfloat(count) / bigfloat.bigfloat(freq_dict.get(production.lhs()))
      outfile.write('{0} # {1} \n'.format(production, prob))
      fh.write('{0} # {1} \n'.format(production, bigfloat.log10(prob)))
  fh.close()

if __name__ == '__main__':
  main()
