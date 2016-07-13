#pragma once

#include <Python.h>  // must be first

char*
strfmt(const char *fmt, ...);

void
raise_pyerror(void);
