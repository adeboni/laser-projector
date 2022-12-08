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
  MeshLoader();
  Mesh loadMesh(const char *filename);
  void printMesh(Mesh mesh);
};

#endif
