#ifndef MESHLOADER_H
#define MESHLOADER_H

#include <ArduinoJson.h>
#include "Basics.h"
#include "Gpio.h"

typedef struct {
  int numNodes;
  int numTriangles;
  long nodes[300][3];
  int triangles[100][3];
} Mesh;

class MeshLoader {
public:
  static Mesh loadMesh(const char *filename);
  static void printMesh(Mesh mesh);
};

#endif
