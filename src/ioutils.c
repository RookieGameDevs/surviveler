#include "ioutils.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>

size_t
file_read(const char *filename, char **r_buf)
{
	assert(filename != NULL);
	assert(r_buf != NULL);

	char *errmsg = NULL;
	size_t size = 0;

	FILE *fp = fopen(filename, "r");
	if (!fp) {
		errmsg = "no such file or directory or not enough rights";
		goto error;
	}

	// read file size
	fseek(fp, 0, SEEK_END);
	size = ftell(fp);
	rewind(fp);

	// allocate a buffer for its contents
	*r_buf = malloc(size + 1);
	if (!*r_buf) {
		errmsg = "could not allocate memory for file contents";
		goto error;
	}

	(*r_buf)[size] = 0;  // NUL-terminator

	// read the file
	if (fread(*r_buf, 1, size, fp) != size) {
		errmsg = "I/O error";
		goto error;
	}

cleanup:
	if (fp)
		fclose(fp);
	return size;

error:
	size = 0;
	fprintf(stderr, "failed to read file '%s': %s\n", filename, errmsg);
	goto cleanup;
}
