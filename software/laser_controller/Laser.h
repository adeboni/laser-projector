#ifndef LASER_H
#define LASER_H

#include "Arduino.h"
#include "Basics.h"
#include <SPI.h>

#define PWM_FREQ 375000
#define DEFAULT_QUALITY 32
#define DEFAULT_TOGGLE_DELAY 500
#define DEFAULT_LINE_DELAY 200
#define DEFAULT_END_DELAY 100
#define DEFAULT_X_DISTORTION 54
#define DEFAULT_Y_DISTORTION 0.95

class Laser {
public:
  Laser(uint8_t redPin, uint8_t greenPin, uint8_t bluePin, uint8_t dacPin);
  void sendTo(int x, int y);
  void drawLine(int x1, int y1, int x2, int y2);
  void setColorHSL(unsigned int hue, unsigned int saturation, unsigned int lightness);
  void setColorRGB(uint8_t red, uint8_t green, uint8_t blue);
  void off();
  void on();

  // defines the granularity of the line interpolation. 64 means that each line is split into steps of 64 pixels in the longer direction.
  // setting smaller values will slow down the rendering but will cause more linearity in the galvo movement,
  // setting bigger values will cause faster rendering, but lines will not be straight anymore.
  void setQuality(float quality);
  void setDistortionFactors(int x, float y);
  void setMirroring(bool x, bool y, bool xy);
  void setScale(float scaleX, float scaleY);
  void setOffset(int offsetX, int offsetY);
  void setClipArea(int x1, int y1, int x2, int y2, int x3, int y3, int x4, int y4);
  void setClipAreaTop(int x1, int y1, int x2, int y2);
  void setClipAreaBottom(int x3, int y3, int x4, int y4);
  void setDelays(int toggleDelay, int lineEndDelay, int endDelay);

  void getQuality(float& quality);
  void getDistortionFactors(int& x, float& y);
  void getMirroring(bool& x, bool& y, bool& xy);
  void getScale(float& scaleX, float& scaleY);
  void getOffset(int& offsetX, int& offsetY);
  void getClipArea(int& x1, int& y1, int& x2, int& y2, int& x3, int& y3, int& x4, int& y4);
  void getDelays(int& toggleDelay, int& lineEndDelay, int& endDelay);

  void setEnable3D(bool flag) { _enable3D = flag; }
  void setMatrix(const Matrix4& matrix) { _matrix = matrix; }
  void setZDist(int dist) { _zDist = dist; }

private:
  uint8_t _redPin, _greenPin, _bluePin, _dacPin;
  float _quality = DEFAULT_QUALITY;
  Color _color;
  int _laserOn = false;

  int _sentX = 0;
  int _sentY = 0;
  int _x = 0; 
  int _y = 0;
  int _oldX = 0;
  int _oldY = 0;

  bool _mirrorX = false;
  bool _mirrorY = false;
  bool _mirrorXY = false;
  
  float _scaleX = 1;
  float _scaleY = 1;
  int _offsetX = 0;
  int _offsetY = 0;

  int _clipPoly[8] = {0, 0, 4095, 0, 4095, 4095, 0, 4095};

  int _toggleDelay = DEFAULT_TOGGLE_DELAY;
  int _lineEndDelay = DEFAULT_LINE_DELAY;
  int _endDelay = DEFAULT_END_DELAY;

  bool _enable3D = false;
  Matrix4 _matrix;
  int _zDist = 10000;

  int _xDistortionFactor = DEFAULT_X_DISTORTION;
  float _yDistortionFactor = DEFAULT_Y_DISTORTION;

  bool clipLine(int& x1, int& y1, int& x2, int& y2);
  void sendToRaw(int x, int y);
  void writeDAC(int x, int y);
  
  unsigned int h2rgb(unsigned int v1, unsigned int v2, unsigned int hue);
};

#endif
