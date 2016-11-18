package surviveler

// FIXME: the generate file required 2 modifications, that's why
// a space has been added between // and go:generate, so as to not
// trigger a file generation when running 'go generate':
// - generated file name was d2.vec2_stack.go (should not include the package)
// - generated file didn't contain the import statement leading to the inclusion
//   of d2 package.
// - Stack items should be values, not pointers. go-gencon doesn't support that
//   yet.
//
// go:generate go-gencon -type d2.Vec2 -cont Stack -name VecStack
