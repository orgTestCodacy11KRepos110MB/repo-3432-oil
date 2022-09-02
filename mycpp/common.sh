#
# Common functions
#

# Include guard.
test -n "${__MYCPP_COMMON_SH:-}" && return
readonly __MYCPP_COMMON_SH=1

if test -z "${REPO_ROOT:-}"; then
  echo '$REPO_ROOT should be set before sourcing'
  exit 1
fi

source mycpp/common-vars.sh

# Used by cpp/TEST.sh and mycpp/TEST.sh

run-test() {
  local bin=$1
  local compiler=$2
  local variant=$3

  local dir=$REPO_ROOT/_test/$compiler-$variant/cpp

  mkdir -p $dir

  local name=$(basename $bin)
  export LLVM_PROFILE_FILE=$dir/$name.profraw

  local log=$dir/$name.log
  log "RUN $bin > $log"

  set +o errexit
  $bin > $log 2>&1
  local status=$?
  set -o errexit

  if test $status -eq 0; then
    log "OK $bin"
  else
    echo
    cat $log
    echo
    die "FAIL: $bin failed with code $status"
  fi
}

run-with-log-wrapper() {
  local bin=$1
  local log=$2

  mkdir -p $(dirname $log)
  log "RUN $bin > $log"

  set +o errexit
  $bin > $log 2>&1
  local status=$?
  set -o errexit

  if test $status -eq 0; then
    log "OK $bin"
  else
    echo
    cat $log
    echo
    die "FAIL: $bin failed with code $status"
  fi
}

maybe-our-python3() {
  ### Run a command line with Python 3

  # Use Python 3.10 from deps/from-tar if available.  Otherwise use the sytsem
  # python3.

  local py3_ours='../oil_DEPS/python3'
  if test -f $py3_ours; then
    echo "*** Running $py3_ours $@" >& 2
    $py3_ours "$@"
  else
    # Use system copy
    python3 "$@"
  fi
}

