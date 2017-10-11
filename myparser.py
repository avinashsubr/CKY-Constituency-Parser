#!/usr/bin/env python3
# right branching "parser"
# from  boilerplate code by Jon May (jonmay@isi.edu)
import argparse
import sys
import codecs
if sys.version_info[0] == 2:
  from itertools import izip
else:
  izip = zip
from collections import defaultdict as dd, defaultdict
import re
import os.path
import gzip
import tempfile
import shutil
import atexit
import bigfloat
import tree as t

class MTree(object):
    def __init__(self, lhs, wrd=None, subs=None):
        self.label = lhs
        self.word = wrd
        self.subs = subs
        self.str = None

    def is_lexicon(self):
        return self.word is not None

    def dostr(self):
        return "(%s %s)" % (self.label, self.word) if self.is_lexicon() \
               else "(%s %s)" % (self.label, " ".join(map(str, self.subs)))


    def __str__(self):
        if True or self.str is None:
            self.str = self.dostr()
        return self.str

class MyParser:
    def __init__(self, rules='pcfg'):
        self.nonTerms = set()
        self.rules_set = set()
        self.rules = {}
        self.probs = defaultdict(float)
        self.lexicons = []
        self.origText = list()
        self.grammar = self.read_grammar(rules)

    def read_grammar(self, f):
        grammar = {}
        rules = open(f, 'r')
        for rule in rules:
            tokens = re.split(r"\-\>|\#", rule.strip())
            lhs = tokens[0].strip()
            rhs = tokens[1].strip().strip('\'')
            prob = tokens[2].strip()
            self.nonTerms.add(lhs)
            self.rules_set.add((lhs, rhs))
            self.rules[lhs] = rhs
            self.probs[(lhs, rhs)] = float(prob)
            if len(rhs.split()) == 1 and rhs != '<unk>':
                self.lexicons.append(rhs)


    def backtrack(self, text, backPointers, terminals):
        n = len(text)
        if (0,n,'TOP') not in backPointers:
            return None

        t = self.helper((0, n, 'TOP'), text, backPointers, terminals)
        return t

    def helper(self, next, text, backPointers, terminals):
        begin = next[0]
        end = next[1]
        A = next[2]

        if next not in backPointers:
            if next in terminals:   #base condition
                word = self.origText[next[0]]
                node = MTree(lhs=A, subs=None, wrd=word)
            return node

        (split, B, C) = backPointers[next]

        next1 = (begin, split, B)
        next2 = (split, end, C)

        t1 = self.helper(next1, text, backPointers, terminals)
        t2 = self.helper(next2, text, backPointers, terminals)
        return MTree(lhs=A, subs=[t1, t2], wrd=None)

    def parse(self, sentence):
        score = defaultdict(float)
        backPointers = {}  # to back track
        terminals = {}
        text = sentence.split()  # the list of words
        self.origText = list(text)
        n = len(text)
        for i, word in enumerate(text):
            if word not in self.lexicons:
                text[i] = '<unk>'

        for i in range(0, n):
            begin = i
            end = i + 1
            word = text[begin]
            # if word == '<unk>':
            #     text[begin] = '<unk>'
            #     for ent in self.rules:
            #         if self.rules[ent] == '<unk>':
            #             score[(begin, end, ent)] = self.probs[(ent, '<unk>')]
            #             terminals[(begin, end, ent)] = '<unk>'
            # else:
            for A in self.nonTerms:
                if (A, word) in self.rules_set: #word found in rules set
                    score[(begin, end, A)] = self.probs[(A, word)]
                    terminals[(begin, end, A)] = word

        for span in range(2, n + 1):
            for begin in range(0, n - span + 1):
                end = begin + span
                for split in range(begin + 1, end):

                    for A, X in self.rules_set:
                        rhs = X.split()
                        if len(rhs) == 2:
                            B = rhs[0].strip()
                            C = rhs[1].strip()

                            prob = score[(begin, split, B)] * score[(split, end, C)] * self.probs[(A, X)]

                            if prob > score[(begin, end, A)]:
                                score[(begin, end, A)] = prob
                                backPointers[(begin, end, A)] = (split, B, C)

        t = self.backtrack(text, backPointers, terminals)
        if t:
            #print t.dostr()
            return t.dostr()
        else:
            return None






