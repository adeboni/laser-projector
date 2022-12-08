#ifndef BASICS_H
#define BASICS_H

#include "Arduino.h"

typedef long FIXPT;
#define PRES             16384
#define PSHIFT           14
#define PROUNDBIT        (1 << (PSHIFT-1))
#define FROM_FLOAT(a) (long(a*PRES))
#define FROM_INT(a) (a << PSHIFT)
#define TO_INT(a) ((a + PROUNDBIT)>> PSHIFT)

typedef struct {
  uint8_t r, g, b;
} Color;

typedef struct {
  long x, y, z;
} Vector3;

// fixed point identity matrix
struct Matrix4 {
  long m[4][4] = {
      {PRES,    0,    0,    0},
      {   0, PRES,    0,    0},
      {   0,    0, PRES,    0},
      {   0,    0,    0, PRES}
  };
   static Vector3 applyMatrix(const Matrix4& matrix, const Vector3& in);
   static Matrix4 multiply(const Matrix4 &mat1, const Matrix4 &mat2);
   static Matrix4 rotateX(const unsigned int angle); 
   static Matrix4 rotateY(const unsigned int angle);
   static Matrix4 rotateZ(const unsigned int angle);
   static Matrix4 translate(const long x, const long y, const long z);
   static Matrix4 scale(const float ratio);
};


long SIN(unsigned int angle);
long COS(unsigned int angle);
long ABS(long x);
int SWAP(int &x, int &y);

#endif
