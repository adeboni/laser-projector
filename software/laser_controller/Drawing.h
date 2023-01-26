#ifndef DRAWING_H
#define DRAWING_H

#include "Laser.h"

extern Laser lasers[4];

class Drawing {
public:
  static void drawString(String text, int x, int y, float scale = 1);
  static long drawLetter(byte letter, long translateX = 0, long translateY = 0, float scale = 1);
  static long advance(byte letter, float scale = 1);
  static long stringAdvance(String text, float scale = 1);
  static void drawObject(const unsigned short* data, int size, long translateX = 0, long translateY = 0, float scale = 1);
  static void drawObjectRotated3D(const unsigned short* data, int size, long centerX, long centerY, Vector3 rotation);
  static void calcObjectBox(const unsigned short* data, int size, long& centerX, long& centerY, long& width, long& height);
};

#endif
