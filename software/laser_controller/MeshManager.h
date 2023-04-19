#ifndef MESHMANAGER_H
#define MESHMANAGER_H

#include <ArduinoJson.h>
#include "Basics.h"
#include "Gpio.h"

typedef struct {
  int numNodes;
  int numTriangles;
  int nodes[300][3];
  int triangles[100][3];
} Mesh;

class MeshManager {
public:
  static Mesh loadMesh(const char *filename);
  static void printMesh(Mesh mesh);
  static bool isFaceHidden(const int (*n)[2], const uint8_t index, const Mesh& m);
  static void mergeLines(const int set1Len, const int (*set1)[4], const int set2Len, const int (*set2)[4], int (*outputSet)[4]);
  static void orderLines(const int numLines, const int (*lines)[4], int (*orderedLines)[4]);
  static void processMesh(const int (*n)[2], const Mesh& m, int &numEdgeLines, int (*edgeLines)[4], int &numInteriorLines, int (*interiorLines)[4]);
};

#endif
