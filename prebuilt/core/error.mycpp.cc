// prebuilt/core/error.mycpp.cc: GENERATED by mycpp

#include "prebuilt/core/error.mycpp.h"
// BEGIN mycpp output

#include "mycpp/runtime.h"

GLOBAL_STR(str0, "(");
GLOBAL_STR(str1, ")");
GLOBAL_STR(str2, "_");
GLOBAL_STR(str3, "T");
GLOBAL_STR(str4, "F");
GLOBAL_STR(str5, "<%s %r>");

namespace runtime {  // forward declare


}  // forward declare namespace runtime

namespace runtime {  // declare

extern int NO_SPID;
hnode_asdl::hnode__Record* NewRecord(Str* node_type);
hnode_asdl::hnode__Leaf* NewLeaf(Str* s, hnode_asdl::color_t e_color);
extern Str* TRUE_STR;
extern Str* FALSE_STR;


}  // declare namespace runtime

namespace runtime {  // define

using hnode_asdl::hnode__Record;
using hnode_asdl::hnode__Leaf;
using hnode_asdl::color_t;
using hnode_asdl::color_e;
int NO_SPID = -1;

hnode_asdl::hnode__Record* NewRecord(Str* node_type) {
  StackRoots _roots({&node_type});

  return Alloc<hnode__Record>(node_type, Alloc<List<hnode_asdl::field*>>(), false, str0, str1, Alloc<List<hnode_asdl::hnode_t*>>());
}

hnode_asdl::hnode__Leaf* NewLeaf(Str* s, hnode_asdl::color_t e_color) {
  StackRoots _roots({&s});

  if (s == nullptr) {
    return Alloc<hnode__Leaf>(str2, color_e::OtherConst);
  }
  else {
    return Alloc<hnode__Leaf>(s, e_color);
  }
}
Str* TRUE_STR = str3;
Str* FALSE_STR = str4;

}  // define namespace runtime

namespace error {  // define

int NO_SPID = -1;

Usage::Usage(Str* msg, int span_id) 
    : GC_CLASS_SCANNED(header_, 1, sizeof(Usage)) {
  this->msg = msg;
  this->span_id = span_id;
}

_ErrorWithLocation::_ErrorWithLocation(Str* msg, syntax_asdl::loc_t* location) 
    : GC_CLASS_FIXED(header_, field_mask(), sizeof(_ErrorWithLocation)) {
  this->msg = msg;
  this->location = location;
}

bool _ErrorWithLocation::HasLocation() {
  using syntax_asdl::loc_e;
  if (this->location) {
    return this->location->tag_() != loc_e::Missing;
  }
  else {
    return false;
  }
}

Str* _ErrorWithLocation::UserErrorString() {
  return this->msg;
}

Runtime::Runtime(Str* msg) 
    : GC_CLASS_SCANNED(header_, 1, sizeof(Runtime)) {
  this->msg = msg;
}

Str* Runtime::UserErrorString() {
  return this->msg;
}

Parse::Parse(Str* msg, syntax_asdl::loc_t* location) : _ErrorWithLocation(msg, location) {
}

FailGlob::FailGlob(Str* msg, syntax_asdl::loc_t* location) : _ErrorWithLocation(msg, location) {
}

RedirectEval::RedirectEval(Str* msg, syntax_asdl::loc_t* location) : _ErrorWithLocation(msg, location) {
}

FatalRuntime::FatalRuntime(int exit_status, Str* msg, syntax_asdl::loc_t* location) : _ErrorWithLocation(msg, location) {
  this->exit_status = exit_status;
}

int FatalRuntime::ExitStatus() {
  return this->exit_status;
}

Strict::Strict(Str* msg, syntax_asdl::loc_t* location) : FatalRuntime(1, msg, location) {
}

ErrExit::ErrExit(int exit_status, Str* msg, syntax_asdl::loc_t* location, bool show_code) : FatalRuntime(exit_status, msg, location) {
  this->show_code = show_code;
}

Expr::Expr(Str* msg, syntax_asdl::loc_t* location) : FatalRuntime(3, msg, location) {
}

}  // define namespace error

namespace pyerror {  // define

int NO_SPID = -1;

[[noreturn]] void e_usage(Str* msg, int span_id) {
  StackRoots _roots({&msg});

  throw Alloc<error::Usage>(msg, span_id);
}

[[noreturn]] void e_strict(Str* msg, syntax_asdl::loc_t* location) {
  StackRoots _roots({&msg, &location});

  throw Alloc<error::Strict>(msg, location);
}

[[noreturn]] void p_die(Str* msg, syntax_asdl::loc_t* location) {
  StackRoots _roots({&msg, &location});

  throw Alloc<error::Parse>(msg, location);
}

[[noreturn]] void e_die(Str* msg, syntax_asdl::loc_t* location) {
  StackRoots _roots({&msg, &location});

  throw Alloc<error::FatalRuntime>(1, msg, location);
}

[[noreturn]] void e_die_status(int status, Str* msg, syntax_asdl::loc_t* location) {
  StackRoots _roots({&msg, &location});

  throw Alloc<error::FatalRuntime>(status, msg, location);
}

}  // define namespace pyerror

