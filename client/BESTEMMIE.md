Bestemmie
=========

Few useful notes about rare and time-consuming quirks which were hard to spot
and led to some original blasphemic performances:

* `glBufferData()` works weird with arrays of `PyOpenGL` wrapped types such as
  `GL.GLuint`, `GL.GLfloat`, etc. Use `numpy.array([...], numpy.float32)` or
  `numpy.array([...], numpy.uint32)` as buffer data containers.

* `glDrawElements()` behaves unexpectedly if the last argument (indices pointer
  offset) is a integer. `PyOpenGL` accepts it silently, but it does not work as
  it would in C. Use `None` or `ctypes.c_void_p()`.

* `glDrawElements()` or `glDrawArrays()` silently segfault if no vertex
  attribute pointer is set up. Ensure there's *ALWAYS* a call to
  `glVertexAttribPointer()` if you have a `glEnableVertexAttribArray()`.

* `glPolygonMode()` accepts only `GL_FRONT_AND_BACK` as `mode` argument.

* `glGetProgramiv()` returns the number of uniforms in the shader program,
  information for which can be queried by calling `glGetActiveUniform()`,
  passing it an index (0 < i < number of uniforms). The actual *uniform
  locations* are **NOT** the indices in that range, and should be queried
  separately by calling `glGetUniformLocation()`, passing it the uniform name
  returned by `glGetActiveUniform()`. Yay!
