MESH format specification v1.0
==============================

The MESH is a binary format suitable for storing 3D mesh data in an
OpenGL-friendly way, in order to provide an easy and fast loading and serve as
target format to which assets are converted from different other formats
(COLLADA, 3DS, X3D, ecc), mainly used for data exchange.


General structure
-----------------

The data within a `.mesh` file is stored in contigous sections as following:

  |Section        |Size            |Offset                          |
  |---------------|----------------|--------------------------------|
  |Header         |13              |0                               |
  |Vertex data    |`vcount * vsize`|13                              |
  |Index data     |`icount * 4`    |13 + `vdata`                    |
  |Joint data     |`jcount * 66`   |13 + `vdata` + `idata`          |
  |Animation data |`acount * asize`|13 + `vdata` + `idata` + `jdata`|
  |Strings        |variable        |13 + `vdata` + `idata` + `adata`|

Data sections are tightly-packed with no padding between them.

*NOTE*: All data is stored in little-endian format.


Header
------
The header has fixed size and must be always present, thus, the minimum size of
a `.mesh` file is defined by the header size. The actual structure is defined as
following:

|Field            |Type        |Size|Offset|
|-----------------|------------|----|------|
|Version          |unsigned int|1   |0     |
|Format           |unsigned int|2   |1     |
|Vertex count     |unsigned int|4   |3     |
|Index count      |unsigned int|4   |7     |
|Joint count      |unsigned int|1   |11    |
|Animations count |unsigned int|1   |12    |

### Version
MESH version, expressed as `(MINOR,MAJOR)` nibbles.

### Format
Format of single vertex data entry. Each bit of the field indicates the
availability of given vertex attribute. The field is described as following:

|Bit|Vertex attribute         |
|---|-------------------------|
|0  |Position, always present |
|1  |Normal vector            |
|2  |Texture coordinate (UV)  |
|3  |Joint data               |
|4  |Unused                   |
|5  |Unused                   |
|6  |Unused                   |
|7  |Unused                   |

### Vertex count
Number of entries in vertex data section.

### Index count
Number of indices in index data section.

### Joint count
Number of joints in the joint data section.


Vertex data
-----------
Vertex data is located right after the header and is laid out in consecutive
entries, one per vertex. Entries have different sizes and structure, which is
defined by the format. The full vertex entry looks as follow:

|Attribute    |Type        |Size|Count|Offset|
|-------------|------------|----|-----|------|
|Position     |float       |4   |3    |0     |
|Normal       |float       |4   |3    |12    |
|UV           |float       |4   |2    |24    |
|Joint0 ID    |unsigned int|1   |1    |30    |
|Joint1 ID    |unsigned int|1   |1    |31    |
|Joint2 ID    |unsigned int|1   |1    |32    |
|Joint3 ID    |unsigned int|1   |1    |33    |
|Joint0 weight|unsigned int|1   |1    |34    |
|Joint1 weight|unsigned int|1   |1    |35    |
|Joint2 weight|unsigned int|1   |1    |36    |
|Joint3 weight|unsigned int|1   |1    |37    |

*NOTE*: All attributes except `Position` are optional and the vertex entry size
is dependent on which attributes are stored.

### Position
Vertex coordinate as `(X,Y,Z)` tuple.
This attribute is always present, having format bit 0 unset is an error.

### Normal
Vertex normal vector as `(X,Y,Z)` tuple.

### UV
Texture mapping coordinate as `(U,V)` tuple.

### JointN ID
Identifier of the N-th joint to which the vertex is attached.

### JointN weight
Weight of the N-th joint for given vertex.


Joint data
----------
Joint data is located right after index data and has the following entry
structure:

|Field    |Type        |Size |Count |Offset |
|---------|------------|-----|------|-------|
|Joint ID |unsigned int|1    |1     |0      |
|Parent ID|unsigned int|1    |1     |1      |
|Transform|float       |4    |16    |2      |

### Parent ID
Index of the parent joint entry. ID value `255` is reserved and stands for "no
parent", e.g root joint.

### Transform
4x4 row-major matrix which transforms a vertex from model space into joint
space.


Animation data
--------------
This section contains data about animations, each of which is defined as a
fixed-size header followed by a variable number of keyframes (poses). The header
is structured as following:

|Field     |Type        |Size |Count       |Offset |
|----------|------------|-----|------------|-------|
|Name      |unsigned int|4    |1           |0      |
|Duration  |float       |4    |1           |4      |
|Speed     |float       |4    |1           |8      |
|Pose count|unsigned int|4    |1           |12     |
|Timestamps|float       |4    |`Pose count`|16     |

### Name
Index in string constants section of the animation name string.

### Duration
Animation duration in ticks.

### Speed
Animation speed in ticks per second.

### Pose count
Number of skeleton poses in the animation.

### Timestamps
Pose timestamps as absolute tick values in the animation timeline.

## Skeleton poses
The actual animation is made up of skeleton poses. A skeleton pose is a full set
of poses of its joints for the given timestamp. Skeleton poses are contiguos and
follow the chronological order of the animation timeline, thus, skeleton pose 0
will correspond to timestamp at index 0. Since a single skeleton pose is
actually made up of pose entries for all of its joints, the number of entries is
given by `Joint count`, and the size of whole skeleton pose data for the entire
animation is given by `Joint count` * `Pose count` * `Pose entry size`. A single
joint pose entry is structured as following:

|Field     |Type        |Size |Count |Offset |
|----------|------------|-----|------|-------|
|Joint ID  |unsigned int|4    |1     |0      |
|Position  |float       |4    |3     |4      |
|Rotation  |float       |4    |4     |16     |
|Scale     |float       |4    |3     |32     |

### Joint ID
Identifier of the joint to which the pose refers.

### Position
Position of the joint at given time expressed as `(X,Y,Z`) tuple.

### Scale
Scale of the joint at given time expressed as `(Xs,Ys,Zs)` tuple.

### Rotation
Rotation of the joint at given time expressed as rotation quaternion
`(W,X,Y,Z)`.


Strings
-------
String constants referenced in other sections as a sequence of C-style
`NUL`-terminated series of bytes.
