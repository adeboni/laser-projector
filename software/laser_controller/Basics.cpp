#include "Basics.h"

float SIN(unsigned int angle) {
  return sinf(angle * 0.0174533);
}

float COS(unsigned int angle) {
  return cosf(angle * 0.0174533);
}

void SWAP(int &x, int &y) {
  int z = x; x = y; y = z;
}

Matrix4 Matrix4::multiply(const Matrix4 &mat1, const Matrix4 &mat2) {
  Matrix4 mat;
  for (unsigned char c=0; c<4; c++)
    for (unsigned char r=0; r<4; r++)
      mat.m[c][r] = mat1.m[0][r] * mat2.m[c][0] +
                    mat1.m[1][r] * mat2.m[c][1] +
                    mat1.m[2][r] * mat2.m[c][2] +
                    mat1.m[3][r] * mat2.m[c][3];
  return mat;
}

Matrix4 Matrix4::rotateX(const unsigned int angle) {
  Matrix4 mat;
  mat.m[1][1] =  COS(angle);
  mat.m[1][2] =  SIN(angle);
  mat.m[2][1] = -SIN(angle);
  mat.m[2][2] =  COS(angle);
  return mat;
}

Matrix4 Matrix4::rotateY(const unsigned int angle) {
  Matrix4 mat;
  mat.m[0][0] =  COS(angle);
  mat.m[0][2] = -SIN(angle);
  mat.m[2][0] =  SIN(angle);
  mat.m[2][2] =  COS(angle);
  return mat;
}

Matrix4 Matrix4::rotateZ(const unsigned int angle) {
  Matrix4 mat;
  mat.m[0][0] =  COS(angle);
  mat.m[0][1] =  SIN(angle);
  mat.m[1][0] = -SIN(angle);
  mat.m[1][1] =  COS(angle);
  return mat;
}

Matrix4 Matrix4::translate(const int x, const int y, const int z) {
  Matrix4 mat;
  mat.m[3][0] = x;
  mat.m[3][1] = y;
  mat.m[3][2] = z;
  return mat;
}

Matrix4 Matrix4::scale(const float ratio) {
  Matrix4 mat;
  mat.m[0][0] *= ratio;
  mat.m[1][1] *= ratio;
  mat.m[2][2] *= ratio;
  return mat;
}

Vector3 Matrix4::applyMatrix(const Matrix4& matrix, const Vector3& in) {
  Vector3 out;
  
  out.x = (matrix.m[0][0] * in.x +
           matrix.m[1][0] * in.y +
           matrix.m[2][0] * in.z +
           matrix.m[3][0]);
  
  out.y = (matrix.m[0][1] * in.x +
           matrix.m[1][1] * in.y +
           matrix.m[2][1] * in.z +
           matrix.m[3][1]);
  
  out.z = (matrix.m[0][2] * in.x +
           matrix.m[1][2] * in.y +
           matrix.m[2][2] * in.z +
           matrix.m[3][2]);

  return out;
}
