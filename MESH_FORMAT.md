MESH format specification v1.0
==============================

The MESH is a binary format suitable for storing 3D mesh data in an
OpenGL-friendly way, in order to provide an easy and fast loading and serve as
target format to which assets are converted from different other formats
(COLLADA, 3DS, X3D, ecc), mainly used for data exchange.


General structure
-----------------

The data within a `.mesh` file is stored in contigous sections as following:

  |Section    |Size            |Offset          |
  |-----------|----------------|----------------|
  |Header     |12              |0               |
  |Vertex data|`vcount * vsize`|12              |
  |Index data |`icount * 4`    |`vcount * vsize`|

Data sections are tightly-packed with no padding between them.

*NOTE*: All data is stored in little-endian format.


Header
------
The header has fixed size and must be always present, thus, the minimum size of
a `.mesh` file is defined by the header size. The actual structure is defined as
following:

|Field       |Type        |Size|Offset|
|------------|------------|----|------|
|Version     |unsigned int|1   |0     |
|Format      |unsigned int|2   |1     |
|Vertex count|unsigned int|4   |3     |
|Index count |unsigned int|4   |7     |
|Joint count |unsigned int|1   |11    |

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
