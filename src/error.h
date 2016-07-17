#pragma once

#include "strutils.h"

#define err(msg) error_push(string_fmt("%s:%d\n\t%s", __func__, __LINE__, msg))

#define errf(fmt, ...) error_push(string_fmt("%s:%d\n\t" fmt, __func__, __LINE__, __VA_ARGS__))

void
error_push(char *errmsg);

void
error_print_tb(void);

void
error_clear(void);
