#ifndef LASER_H
#define LASER_H

#include "Arduino.h"
#include "Basics.h"
#include <WireIMXRT.h>

#define PWM_FREQ 375000

class Laser {
public:
  Laser(uint8_t redPin, uint8_t greenPin, uint8_t bluePin, uint8_t xDacIndex, uint8_t yDacIndex);
  void sendTo(long x, long y);
  void drawLine(long x1, long y1, long x2, long y2);
  void setColorHSL(unsigned int hue, unsigned int saturation, unsigned int lightness);
  void setColorRGB(uint8_t red, uint8_t green, uint8_t blue);
  void off();
  void on();

  // defines the granularity of the line interpolation. 64 means that each line is split into steps of 64 pixels in the longer direction.
  // setting smaller values will slow down the rendering but will cause more linearity in the galvo movement,
  // setting bigger values will cause faster rendering, but lines will not be straight anymore.
  void setQuality(int quality);
  void setDistortionFactors(long x, float y);
  void setMirroring(bool x, bool y, bool xy);
  void setMasterScale(float scaleX, float scaleY);
  void setMasterOffset(long offsetX, long offsetY);
  void setScale(float scaleX, float scaleY);
  void setOffset(long offsetX, long offsetY);
  void setClipArea(long xMin, long yMin, long xMax, long yMax);

  void setEnable3D(bool flag) { _enable3D = flag; }
  void setMatrix(const Matrix4& matrix) { _matrix = matrix; }
  void setZDist(long dist) { _zDist = dist; }

private:
  uint8_t _redPin, _greenPin, _bluePin;
  uint8_t _xDacIndex, _yDacIndex;
  FIXPT _quality = FROM_FLOAT(1.0 / 32.0);
  Color _color;

  long _x = 0; 
  long _y = 0;
  long _oldX = 0;
  long _oldY = 0;

  bool _mirrorX = false;
  bool _mirrorY = false;
  bool _mirrorXY = false;
  
  FIXPT _scaleX = 1;
  FIXPT _scaleY = 1;
  long _offsetX = 0;
  long _offsetY = 0;

  long _clipXMin = 0;
  long _clipYMin = 0;
  long _clipXMax = 4095;
  long _clipYMax = 4095;

  bool _enable3D = false;
  Matrix4 _matrix;
  long _zDist = 10000;

  long _xDistortionFactor = 54;
  FIXPT _yDistortionFactor = FROM_FLOAT(0.95);

  int computeOutCode(long x, long y);
  bool clipLine(long& x0, long& y0, long& x1, long& y1);
  void sendToRaw(long x, long y);
  void writeDAC(long x, long y);
  
  unsigned int h2rgb(unsigned int v1, unsigned int v2, unsigned int hue);
};

#endif
