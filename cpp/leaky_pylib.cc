// pylib_os_path.cc

#include "leaky_pylib.h"

#include <sys/stat.h>

namespace os_path {

Str* rstrip_slashes(Str* s) {
  // Strip all the rightmost slashes, but not if it's ALL slashes
  int n = len(s);
  if (n == 0) {
    return s;
  }

  int new_len = n;
  for (int i = n - 1; i >= 0; i--) {
    char c = s->data_[i];
    if (c == '/') {
      new_len--;
    } else {
      break;
    }
  }

  if (new_len == 0) {  // it was all slashes, don't strip
    return s;
  }

  // TODO: use mylib2.h API instead
  char* buf = static_cast<char*>(malloc(new_len + 1));
  memcpy(buf, s->data_, new_len);
  buf[new_len] = '\0';
  return new Str(buf, new_len);
}

}  // namespace os_path

namespace path_stat {

bool exists(Str* path) {
  mylib::Str0 path0(path);
  struct stat st;
  if (::stat(path0.Get(), &st) < 0) {
    return false;
  } else {
    return true;
  }
}

}  // namespace path_stat