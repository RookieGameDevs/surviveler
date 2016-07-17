#include "error.h"
#include <stdio.h>
#include <stdlib.h>

#define MAX_ERR_COUNT 1000

static char *traceback[MAX_ERR_COUNT];
static long traceback_len = 0;

void
error_push(char *errmsg)
{
	if (traceback_len < MAX_ERR_COUNT) {
		traceback[traceback_len++] = errmsg;
	}
	else {
		fprintf(stderr, "%s\n", errmsg);
		free(errmsg);
		fprintf(stderr, "error traceback stack depth exceeded, aborting\n");
		abort();
	}
}

void
error_print_tb(void)
{
	for (long i = traceback_len - 1; i >= 0; i--)
		fprintf(stderr, "%s\n", traceback[i]);
}

void
error_clear(void)
{
	for (; traceback_len > 0; --traceback_len)
		free(traceback[traceback_len]);
}
