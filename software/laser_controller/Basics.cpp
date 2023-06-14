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

int ABS(int x) {
  return x < 0 ? -x : x;
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

Matrix8 Matrix8::invert(const Matrix8& mat) {
  Matrix8 res;
  int perm[8];
  Matrix8 lum = decompose(mat, perm);
  float x[8];
  
  for (int i = 0; i < 8; i++) {
    for (int j = 0; j < 8; j++)
      x[j] = i == perm[j] ? 1.0 : 0.0;

    for (int k = 0; k < 8; k++) {
      float sum = x[k];
      for (int w = 0; w < k; w++)
        sum -= lum.m[k][w] * x[w];
      x[k] = sum;
    }
    
    x[7] /= lum.m[7][7];
    for (int k = 6; k >= 0; k--) {
      float sum = x[k];
      for (int w = k + 1; w < 8; w++)
        sum -= lum.m[k][w] * x[w];
      x[k] = sum / lum.m[k][k];
    }
    
    for (int j = 0; j < 8; j++)
      res.m[j][i] = x[j];
  }
  return res;
}

Matrix8 Matrix8::decompose(const Matrix8& mat, int* perm) {
  Matrix8 res;
  memcpy(res.m, mat.m, sizeof(float)*64);
  for (int i = 0; i < 8; i++)
    perm[i] = i;

  for (int j = 0; j < 7; j++) {
    float colMax = abs(res.m[j][j]);
    int pRow = j;

    for (int i = j + 1; i < 8; i++) {
      if (abs(res.m[i][j]) > colMax) {
        colMax = abs(res.m[i][j]);
        pRow = i;
      }
    }

    if (pRow != j) {
      for (int k = 0; k < 8; k++) {
        float temp = res.m[pRow][k];
        res.m[pRow][k] = res.m[j][k];
        res.m[j][k] = temp;
      }

      float temp = perm[pRow];
      perm[pRow] = perm[j];
      perm[j] = temp;
    }

    if (res.m[j][j] == 0.0) {
      int goodRow = -1;

      for (int row = j + 1; row < 8; row++)
        if (res.m[row][j] != 0.0)
          goodRow = row;
      
      if (goodRow == -1)
        return res;
      
      for (int k = 0; k < 8; k++) {
        float temp = res.m[goodRow][k];
        res.m[goodRow][k] = res.m[j][k];
        res.m[j][k] = temp;
      }

      float temp = perm[goodRow];
      perm[goodRow] = perm[j];
      perm[j] = temp;
    }

    for (int i = j + 1; i < 8; i++) {
      res.m[i][j] /= res.m[j][j];
      for (int k = j + 1; k < 8; k++)
        res.m[i][k] -= res.m[i][j] * res.m[j][k];
    }
  }

  return res;
}

void Matrix8::print(const Matrix8& mat) {
  for (int i = 0; i < 8; i++) {
    for (int j = 0; j < 8; j++) {
      Serial.print(mat.m[i][j]);
      Serial.print(", ");
    }
    Serial.println();
  }
  Serial.println();
}
