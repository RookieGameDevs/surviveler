#pragma once

#include "strutils.h"

#define err(msg) error_push(string_fmt("%s:%d (%s)\n\t%s", __FILE__, __LINE__, __func__, msg))

#define errf(fmt, ...) error_push(string_fmt("%s:%d (%s)\n\t" fmt, __FILE__, __LINE__, __func__, __VA_ARGS__))

void
error_push(char *errmsg);

void
error_print_tb(void);

void
error_clear(void);

const char*
error_last(void);
