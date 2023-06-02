#ifndef BASICS_H
#define BASICS_H

#include "Arduino.h"

typedef struct {
  uint8_t r, g, b;
} Color;

typedef struct {
  int x, y, z;
} Vector3;

// fixed point identity matrix
struct Matrix4 {
  float m[4][4] = {
      {1, 0, 0, 0},
      {0, 1, 0, 0},
      {0, 0, 1, 0},
      {0, 0, 0, 1}
  };
   static Vector3 applyMatrix(const Matrix4& matrix, const Vector3& in);
   static Matrix4 multiply(const Matrix4 &mat1, const Matrix4 &mat2);
   static Matrix4 rotateX(const unsigned int angle); 
   static Matrix4 rotateY(const unsigned int angle);
   static Matrix4 rotateZ(const unsigned int angle);
   static Matrix4 translate(const int x, const int y, const int z);
   static Matrix4 scale(const float ratio);
};

struct Matrix8 {
  float m[8][8];
  static Matrix8 invert(const Matrix8& mat);
  static Matrix8 decompose(const Matrix8& mat, int* perm);
  static float* helperSolve(const Matrix8& luMat, float* b);
};

struct LaserFrame {
  Vector3 point;
  Color color;
  bool laserOn;
};

struct MasterFrame {
  int numPoints[4] = {0, 0, 0, 0};
  LaserFrame laserFrame[4][1024];
};

float SIN(unsigned int angle);
float COS(unsigned int angle);
void SWAP(int &x, int &y);
void SWAP(float &x, float &y);

#endif
