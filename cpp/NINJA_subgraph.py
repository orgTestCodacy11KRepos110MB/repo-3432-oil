"""
cpp/NINJA_subgraph.py
"""

from __future__ import print_function

from build import ninja_lib
from build.ninja_lib import log

# Some tests use #ifndef CPP_UNIT_TEST to disable circular dependencies on
# generated code
CPP_UNIT_MATRIX = [
  ('cxx', 'dbg', '-D CPP_UNIT_TEST'),
  ('cxx', 'asan', '-D CPP_UNIT_TEST'),
  ('cxx', 'ubsan', '-D CPP_UNIT_TEST'),
  #('cxx', 'gcevery', '-D CPP_UNIT_TEST'),
  #('cxx', 'rvroot', '-D CPP_UNIT_TEST'),
  ('clang', 'coverage', '-D CPP_UNIT_TEST'),
]

def NinjaGraph(ru):
  ru.comment('Generated by %s' % __name__)

  ru.cc_library(
      '//cpp/leaky_core', 
      srcs = ['cpp/leaky_core.cc'],
      deps = ['//frontend/syntax.asdl'],
  )

  # doesn't run with GC
  ru.cc_binary(
      'cpp/leaky_core_test.cc',
      deps = [
        '//cpp/leaky_core',
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.SMALL_TEST_MATRIX)

  ru.cc_binary(
      'cpp/core_test.cc',
      deps = [
        '//cpp/leaky_core',
        '//cpp/leaky_bindings',  # TODO: it's only leaky_stdlib
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.COMPILERS_VARIANTS)

  ru.cc_binary(
      'cpp/data_race_test.cc',
      deps = [
        '//cpp/leaky_core',
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.SMALL_TEST_MATRIX + [
        ('cxx', 'tsan'),
        ('clang', 'tsan'),
      ])

  # Note: depends on code generated by re2c
  ru.cc_library(
      '//cpp/frontend_match', 
      srcs = [
        'cpp/leaky_frontend_match.cc',
      ],
      deps = [
        '//frontend/syntax.asdl',
        '//frontend/types.asdl',
      ],
  )

  ru.cc_binary(
      'cpp/frontend_match_test.cc',
      deps = [
        '//cpp/frontend_match',
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.COMPILERS_VARIANTS)

  ru.cc_library(
      '//cpp/frontend_flag_spec', 
      srcs = [
        'cpp/leaky_frontend_flag_spec.cc',
      ],
      deps = [
        '//core/runtime.asdl',
        '//frontend/arg_types',  # generated code
      ],
  )

  ru.cc_binary(
      'cpp/leaky_frontend_flag_spec_test.cc',

      deps = [
        '//cpp/frontend_flag_spec',
        '//mycpp/runtime',
        ],
      # special -D CPP_UNIT_TEST
      matrix = CPP_UNIT_MATRIX)

  ru.cc_library(
      '//cpp/leaky_bindings', 
      # TODO: split these into their own libraries
      srcs = [
        'cpp/leaky_frontend_tdop.cc',
        'cpp/leaky_osh.cc',
        'cpp/leaky_pgen2.cc',
        'cpp/leaky_pylib.cc',
        'cpp/leaky_stdlib.cc',
        'cpp/leaky_libc.cc',
      ],
  )

  ru.cc_binary(
      'cpp/leaky_binding_test.cc',
      deps = [
        '//cpp/leaky_bindings',
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.COMPILERS_VARIANTS)

  # Note: there is no cc_library() for qsn.h
  ru.cc_binary(
      'cpp/qsn_test.cc',
      deps = [
        '//mycpp/runtime',
        ],
      matrix = ninja_lib.COMPILERS_VARIANTS)
