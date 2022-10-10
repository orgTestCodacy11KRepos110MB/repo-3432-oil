#!/usr/bin/env python2
"""
cpp/NINJA_subgraph.py

Runtime options:

  CXXFLAGS     Additional flags to pass to the C++ compiler

Phony targets

  osh-eval-all   # all variants of the binary
  mycpp-all      # all mycpp/examples
  mycpp-typecheck, etc.

  TODO: unit tests

Directory structure:

_bin/   # output binaries
  # The _bin folder is a 3-tuple {cxx,clang}-{dbg,opt,asan ...}-{,sh}
  cxx-opt/
    osh_eval
    osh_eval.stripped              # The end user binary
    osh_eval.symbols

  cxx-opt-sh/                      # with shell script

_build/
  cpp/    # _build/gen is more consistent, but it would take a lot of renaming
    osh_eval.{h,cc}

  obj/
    # The obj folder is a 2-tuple {cxx,clang}-{dbg,opt,asan ...}
    cxx-asan/
      osh_eval.o
      osh_eval.d     # dependency file
      osh_eval.json  # when -ftime-trace is passed
    cxx-dbg/
    cxx-opt/

  preprocessed/
    cxx-dbg/
      leaky_stdlib.cc
    cxx-dbg.txt  # line counts

TODO

- Could fold bloaty reports in here?  See metrics/native-code.sh
  - Takes both dbg and opt.  Depends on the symbolized, optimized file.
  - make bloaty report along with total size in the continuous build?
    - although it depends on R, and we don't have Clang
- Port test/cpp-unit.sh logic here
  - declare dependencies, could use same pattern as mycpp/build_graph.py
"""

from __future__ import print_function

import os
import sys

from build import ninja_lib
from build.ninja_lib import log, ObjPath
from mycpp import NINJA_subgraph as mycpp_subgraph
from mycpp.NINJA_subgraph import GC_RUNTIME


# CPP bindings and some generated code have implicit dependencies on these headers
ASDL_H = [
    '_gen/asdl/hnode.asdl.h',
    '_gen/core/runtime.asdl.h',
    '_gen/frontend/syntax.asdl.h',
    '_gen/frontend/types.asdl.h',

    # synthetic
    '_gen/frontend/id_kind.asdl.h',
    '_gen/frontend/option.asdl.h',
]

ASDL_CC = [
    '_gen/core/runtime.asdl.cc',
    '_gen/frontend/syntax.asdl.cc',
    '_gen/frontend/id_kind.asdl.cc',

    # NOT generated due to --no-pretty-print-methods
    # '_gen/frontend/types.asdl.cc',
    # '_gen/asdl/hnode.asdl.cc',
    # '_gen/frontend/option.asdl.cc',
]

GENERATED_H = [
    '_gen/frontend/arg_types.h',
    # NOTE: there is no cpp/arith_parse.h

    '_gen/frontend/consts.h',
    '_gen/core/optview.h',  # header only
]

GENERATED_CC = [
    '_gen/bin/osh_eval.mycpp.cc',
    '_gen/frontend/arg_types.cc',
    '_gen/frontend/consts.cc',
    '_gen/osh/arith_parse.cc',
]

# TODO: Clean up this weirdness.
# Some C++ bindings are in mycpp/NINJA_subgraph, and some are here.

from mycpp.NINJA_subgraph import UNIT_TEST_DEPS

NINJA_CPP_BINDINGS = []
for cc_list in UNIT_TEST_DEPS.values():
  NINJA_CPP_BINDINGS.extend(cc_list)

# stuff not in Ninja
MORE_CPP_BINDINGS = [
    'cpp/leaky_frontend_flag_spec.cc',
    'cpp/leaky_frontend_match.cc',
    'cpp/leaky_frontend_tdop.cc',
    'cpp/leaky_osh.cc',
    'cpp/leaky_pgen2.cc',
    'cpp/leaky_pylib.cc',
    'cpp/leaky_stdlib.cc',
    'cpp/leaky_libc.cc',

    # Unused now, but could be brought back to test GC overhead
    #'cpp/dumb_alloc.cc',
]

OSH_EVAL_UNITS = MORE_CPP_BINDINGS + ASDL_CC + GENERATED_CC
OSH_EVAL_UNITS_ALL = OSH_EVAL_UNITS + NINJA_CPP_BINDINGS + GC_RUNTIME

# Add implicit deps
HEADER_DEPS = {}
for cc in NINJA_CPP_BINDINGS + MORE_CPP_BINDINGS + GENERATED_CC:
  if cc not in HEADER_DEPS:
    HEADER_DEPS[cc] = []
  HEADER_DEPS[cc].extend(ASDL_H)
  HEADER_DEPS[cc].extend(GENERATED_H)


def NinjaGraph(ru):
  n = ru.n

  n.comment('Generated by %s' % __name__)
  n.newline()

  # Preprocess one translation unit
  n.rule('preprocess',
         # compile_one detects the _build/preprocessed path
         command='build/ninja-rules-cpp.sh compile_one $compiler $variant $more_cxx_flags $in $out',
         description='PP $compiler $variant $more_cxx_flags $in $out')
  n.newline()

  # Preprocess one translation unit
  n.rule('line_count',
         command='build/ninja-rules-cpp.sh line_count $out $in',
         description='line_count $out $in')
  n.newline()

  # Compile one translation unit
  n.rule('compile_one',
         command='build/ninja-rules-cpp.sh compile_one $compiler $variant $more_cxx_flags $in $out $out.d',
         depfile='$out.d',
         # no prefix since the compiler is the first arg
         description='$compiler $variant $more_cxx_flags $in $out')
  n.newline()

  # Link objects together
  n.rule('link',
         command='build/ninja-rules-cpp.sh link $compiler $variant $out $in',
         description='LINK $compiler $variant $out $in')
  n.newline()

  # 1 input and 2 outputs
  n.rule('strip',
         command='build/ninja-rules-cpp.sh strip_ $in $out',
         description='STRIP $in $out')
  n.newline()

  binaries = []

  n.newline()

  COMPILERS_VARIANTS = ninja_lib.COMPILERS_VARIANTS + [
      # note: these could be clang too
      ('cxx', 'alloclog'),
      ('cxx', 'dumballoc'),
      ('cxx', 'uftrace'),

      # leave out tcmalloc since it requires system libs to be installed
      # 'tcmalloc'
      #('cxx', 'tcmalloc')
  ]

  for compiler, variant in COMPILERS_VARIANTS:

    # TODO: make consistent with compile_vars, link_vars
    ninja_vars = [('compiler', compiler), ('variant', variant), ('more_cxx_flags', "''")]

    #
    # See how much input we're feeding to the compiler.  Test C++ template
    # explosion, e.g. <unordered_map>
    #
    # Limit to {dbg,opt} so we don't generate useless rules.  Invoked by
    # metrics/source-code.sh
    #

    if variant in ('dbg', 'opt'):
      preprocessed = []
      for src in OSH_EVAL_UNITS_ALL:
        # e.g. _build/obj/dbg/posix.o
        rel_path, _ = os.path.splitext(src)

        pre = '_build/preprocessed/%s-%s/%s.cc' % (compiler, variant, rel_path)
        preprocessed.append(pre)

        n.build(pre, 'preprocess', [src], variables=ninja_vars,
                implicit=HEADER_DEPS.get(src, []))
        n.newline()

      n.build('_build/preprocessed/%s-%s.txt' % (compiler, variant),
              'line_count', preprocessed, variables=ninja_vars)
      n.newline()

    #
    # SEPARATE: Compile objects
    #

    for src in OSH_EVAL_UNITS:
      # e.g. _build/obj/dbg/posix.o
      rel_path, _ = os.path.splitext(src)

      obj = '_build/obj/%s-%s/%s.o' % (compiler, variant, rel_path)

      n.build(obj, 'compile_one', [src], variables=ninja_vars,
              # even though compile_one has .d, we still need these implicit deps
              # for generated headers
              implicit=HEADER_DEPS.get(src, []))
      n.newline()

    bin_separate = '_bin/%s-%s/osh_eval' % (compiler, variant)
    binaries.append(bin_separate)

    #
    # SEPARATE: Link objects into binary
    #

    objects = [ObjPath(src, compiler, variant) for src in OSH_EVAL_UNITS_ALL]
    link_vars = [('compiler', compiler), ('variant', variant)]  # no CXX flags
    n.build(bin_separate, 'link', objects, variables=link_vars)
    n.newline()

    # Strip the .opt binary
    if variant == 'opt':
      b = bin_separate
      stripped = b + '.stripped'
      symbols = b + '.symbols'
      n.build([stripped, symbols], 'strip', [b])
      n.newline()

      binaries.append(stripped)

  n.default(['_bin/cxx-dbg/osh_eval'])

  # All groups
  n.build(['osh-eval-all'], 'phony', binaries)


def TarballManifest():
  names = []

  # Text
  names.extend([
    'LICENSE.txt',
    'README-native.txt',
    ])

  # Code we know about
  names.extend(OSH_EVAL_UNITS_ALL + GENERATED_H + ASDL_H)

  from glob import glob
  names.extend(glob('mycpp/*.h'))

  # TODO: crawl headers
  names.extend(glob('cpp/*.h'))

  # TODO: Put these in Ninja.
  names.extend(glob('_gen/frontend/*.h'))
  names.extend(glob('_gen/oil_lang/*.h'))

  # ONLY the headers
  names.extend(glob('prebuilt/*/*.h'))

  # Build scripts
  names.extend([
    'build/common.sh',
    'build/native.sh',
    'build/ninja-rules-cpp.sh',
    'mycpp/common.sh',

    # Generated
    '_build/oil-native.sh',
    ])

  for name in names:
    print(name)


def ShellFunctions(f, argv0):
  """
  Generate a shell script that invokes the same function that build.ninja does
  """
  print('''\
#!/usr/bin/env bash
#
# _build/oil-native.sh - generated by %s
#
# Usage
#   _build/oil-native COMPILER? VARIANT? SKIP_REBUILD?
#
#   COMPILER: 'cxx' for system compiler, or 'clang' [default cxx]
#   VARIANT: 'dbg' or 'opt' [default dbg]
#   SKIP_REBUILD: if non-empty, checks if the output exists before building
#
# Could run with /bin/sh, but use bash for now, bceause dash has bad errors messages!
#!/bin/sh

. build/ninja-rules-cpp.sh

main() {
  ### Compile oil-native into _bin/$compiler-$variant-sh/ (not with ninja)

  local compiler=${1:-cxx}   # default is system compiler
  local variant=${2:-opt}    # default is optimized build
  local skip_rebuild=${3:-}  # if the output exists, skip build'

''' % (argv0), file=f)

  out = '_bin/$compiler-$variant-sh/osh_eval'
  print('  local out=%s' % out, file=f)

  print('''\
  if test -n "$skip_rebuild" && test -f "$out"; then
    echo
    echo "$0: SKIPPING build because $out exists"
    echo
    return
  fi

  echo
  echo "$0: Building oil-native: $out"
  echo

  mkdir -p "_build/obj/$compiler-$variant-sh" "_bin/$compiler-$variant-sh"
''', file=f)

  objects = []
  for src in OSH_EVAL_UNITS_ALL:
    # e.g. _build/obj/dbg/posix.o
    base_name, _ = os.path.splitext(os.path.basename(src))

    obj_quoted = '"_build/obj/$compiler-$variant-sh/%s.o"' % base_name
    objects.append(obj_quoted)

    print("  echo 'CXX %s'" % src, file=f)
    print('  compile_one "$compiler" "$variant" "" \\', file=f)
    print('    %s %s' % (src, obj_quoted), file=f)

  print('', file=f)

  print('  echo "LINK $out"', file=f)
  # note: can't have spaces in filenames
  print('  link "$compiler" "$variant" "$out" \\', file=f)
  # put each object on its own line, and indent by 4
  print('    %s' % (' \\\n    '.join(objects)), file=f)
  print('', file=f)

  # Strip opt binary
  # TODO: provide a way for the user to get symbols?

  print('''\
  if test "$variant" = opt; then
    strip -o "$out.stripped" "$out"
  fi
}

main "$@"
''', file=f)
