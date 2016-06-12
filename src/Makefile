CFLAGS := $(CFLAGS) `pkg-config --cflags sdl2 glew` -O0 -g
LDFLAGS := $(LDFLAGS) `pkg-config --libs sdl2 glew` -framework OpenGL -framework Accelerate
OBJS = main.o matlib.o

all: demo

demo: $(OBJS)
	$(CC) $(LDFLAGS) $(OBJS) -o $@

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -rfv *.o demo
