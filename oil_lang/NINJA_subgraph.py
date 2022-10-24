"""
oil_lang/NINJA_subgraph.py
"""

from __future__ import print_function

from build.ninja_lib import log

_ = log


def NinjaGraph(ru):
  n = ru.n

  ru.comment('Generated by %s' % __name__)

  ru.py_binary('oil_lang/grammar_gen.py')

  n.rule('grammar-gen',
         # uses shell style
         command='_bin/shwrap/grammar_gen cpp $in $out_dir',
         description='grammar_gen cpp $in $out_dir')

  n.build(['_gen/oil_lang/grammar_nt.h'], 'grammar-gen', ['oil_lang/grammar.pgen2'],
          implicit=['_bin/shwrap/grammar_gen'],
          variables = [('out_dir', '_gen/oil_lang')],
          )
  n.newline()

  ru.cc_library(
      '//oil_lang/grammar',
      srcs = [],
      generated_headers = ['_gen/oil_lang/grammar_nt.h'])

