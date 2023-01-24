#include "Laser.h"

Laser::Laser(uint8_t redPin, uint8_t greenPin, uint8_t bluePin, uint8_t xDacIndex, uint8_t yDacIndex) {
  _redPin = redPin;
  _greenPin = greenPin;
  _bluePin = bluePin;
  pinMode(redPin, OUTPUT);
  pinMode(greenPin, OUTPUT);
  pinMode(bluePin, OUTPUT);
  analogWriteFrequency(redPin, PWM_FREQ);
  analogWriteFrequency(greenPin, PWM_FREQ);
  analogWriteFrequency(bluePin, PWM_FREQ);
  off();
	
  _xDacIndex = xDacIndex;
  _yDacIndex = yDacIndex;
}

void Laser::setQuality(int quality) {
  _quality = FROM_FLOAT(1.0 / quality);
}

void Laser::setMirroring(bool x, bool y, bool xy) {
  _mirrorX = x;
  _mirrorY = y;
  _mirrorXY = xy;
}

void Laser::setScale(float scaleX, float scaleY) { 
  _scaleX = FROM_FLOAT(scaleX);
  _scaleY = FROM_FLOAT(scaleY);
}

void Laser::setOffset(long offsetX, long offsetY) { 
  _offsetX = offsetX;
  _offsetY = offsetY;
}

void Laser::setClipArea(long xMin, long yMin, long xMax, long yMax) {
  _clipXMin = xMin;
  _clipYMin = yMin;
  _clipXMax = xMin;
  _clipYMax = yMin;
}

void Laser::setDistortionFactors(long x, float y) {
  _xDistortionFactor = x;
  _yDistortionFactor = FROM_FLOAT(y);
}

void Laser::writeDAC(long x, long y) {
  //apply distortion corrections
  x = (((x - 2048) * COS(ABS(y - 2048) / _xDistortionFactor)) >> 14) + 2048;
  y = TO_INT((y - 2048) * _yDistortionFactor) + 2048;

  int x1 = constrain((int)x, 0, 4095);
  int y1 = constrain((int)y, 0, 4095);

  if (_mirrorXY) SWAP(x1, y1);
  if (_mirrorX)  x1 = 4095 - x1;
  if (_mirrorY)  y1 = 4095 - y1;

  Wire.beginTransmission(0x48);
  Wire.write(0x30 + _xDacIndex);
  Wire.write((x1 & 4088) >> 4);
  Wire.write((x1 & 15) << 4);
  Wire.endTransmission();

  Wire.beginTransmission(0x48);
  Wire.write(0x30 + _yDacIndex);
  Wire.write((y1 & 4088) >> 4);
  Wire.write((y1 & 15) << 4);
  Wire.endTransmission();
}

const int INSIDE = 0; // 0000
const int LEFT   = 1; // 0001
const int RIGHT  = 2; // 0010
const int BOTTOM = 4; // 0100
const int TOP    = 8; // 1000

int Laser::computeOutCode(long x, long y) {
  int code = INSIDE;
  if      (x < _clipXMin) code |= LEFT;
  else if (x > _clipXMax) code |= RIGHT;
  if      (y < _clipYMin) code |= BOTTOM;
  else if (y > _clipYMax) code |= TOP;
  return code;
}

bool Laser::clipLine(long& x0, long& y0, long& x1, long& y1) {
  int outcode0 = computeOutCode(x0, y0);
  int outcode1 = computeOutCode(x1, y1);
  bool accept = false;
  
  while (true) {
    if (!(outcode0 | outcode1)) { // Bitwise OR is 0. Trivially accept and get out of loop
      accept = true;
      break;
    } else if (outcode0 & outcode1) { // Bitwise AND is not 0. Trivially reject and get out of loop
      break;
    } else {
      // failed both tests, so calculate the line segment to clip
      // from an outside point to an intersection with clip edge
      long x, y;

      // At least one endpoint is outside the clip rectangle; pick it.
      int outcodeOut = outcode0 ? outcode0 : outcode1;

      // Now find the intersection point;
      // use formulas y = y0 + slope * (x - x0), x = x0 + (1 / slope) * (y - y0)
      if (outcodeOut & TOP) {           // point is above the clip rectangle
        x = x0 + (x1 - x0) * float(_clipYMax - y0) / float(y1 - y0);
        y = _clipYMax;
      } else if (outcodeOut & BOTTOM) { // point is below the clip rectangle
        x = x0 + (x1 - x0) * float(_clipYMin - y0) / float(y1 - y0);
        y = _clipYMin;
      } else if (outcodeOut & RIGHT) {  // point is to the right of clip rectangle
        y = y0 + (y1 - y0) * float(_clipXMax - x0) / float(x1 - x0);
        x = _clipXMax;
      } else if (outcodeOut & LEFT) {   // point is to the left of clip rectangle
        y = y0 + (y1 - y0) * float(_clipXMin - x0) / float(x1 - x0);
        x = _clipXMin;
      }

      // Now we move outside point to intersection point to clip and get ready for next pass.
      if (outcodeOut == outcode0) {
        x0 = x;
        y0 = y;
        outcode0 = computeOutCode(x0, y0);
      } else {
        x1 = x;
        y1 = y;
        outcode1 = computeOutCode(x1, y1);
      }
    }
  }
  
  return accept;
}

void Laser::sendTo(long xpos, long ypos) {
  if (_enable3D) {
    Vector3 p1 = {FROM_INT(xpos - 2048), FROM_INT(ypos - 2048), 0};
    Vector3 p = Matrix4::applyMatrix(_matrix, p1);
    xpos = (_zDist * p.x) / (_zDist + p.z) + 2048;
    ypos = (_zDist * p.y) / (_zDist + p.z) + 2048;
  }

  long xNew = TO_INT(xpos * _scaleX) + _offsetX;
  long yNew = TO_INT(ypos * _scaleY) + _offsetY; 
  long clipX = xNew;
  long clipY = yNew;
  long oldX = _oldX;
  long oldY = _oldY;
  if (clipLine(oldX, oldY, clipX, clipY)) {
    if (oldX != _oldX || oldY != _oldY)
      sendToRaw(oldX, oldY);
    sendToRaw(clipX, clipY);
  }
  _oldX = xNew;
  _oldY = yNew;
}

void Laser::sendToRaw(long xNew, long yNew) {
  // divide into equal parts, using _quality
  long fdiffx = xNew - _x;
  long fdiffy = yNew - _y;
  long diffx = TO_INT(abs(fdiffx) * _quality); //TODO: adjust quality based on length?
  long diffy = TO_INT(abs(fdiffy) * _quality);

  // use the bigger direction
  if (diffx < diffy) diffx = diffy;     
  fdiffx = FROM_INT(fdiffx) / diffx;
  fdiffy = FROM_INT(fdiffy) / diffx;
  // interpolate in FIXPT
  FIXPT tmpx = 0;
  FIXPT tmpy = 0;
  for (int i = 0; i < diffx - 1; i++) {
    tmpx += fdiffx;
    tmpy += fdiffy;
    writeDAC(_x + TO_INT(tmpx), _y + TO_INT(tmpy));
  }
  
  _x = xNew;
  _y = yNew;
  writeDAC(_x, _y);
}

void Laser::drawLine(long x1, long y1, long x2, long y2) {
  if (_x != x1 || _y != y1) {
    off();
    sendTo(x1, y1);
  }
  on();
  sendTo(x2, y2);
}

unsigned int Laser::h2rgb(unsigned int v1, unsigned int v2, unsigned int hue) {
  if (hue < 60) return v1 * 60 + (v2 - v1) * hue;
  if (hue < 180) return v2 * 60;
  if (hue < 240) return v1 * 60 + (v2 - v1) * (240 - hue);
  return v1 * 60;
}

void Laser::setColorHSL(unsigned int hue, unsigned int saturation, unsigned int lightness) {
  unsigned int red, green, blue;
  unsigned int var1, var2;

  if (hue > 359) hue = hue % 360;
  if (saturation > 100) saturation = 100;
  if (lightness > 100) lightness = 100;

  // algorithm from: http://www.easyrgb.com/index.php?X=MATH&H=19#text19
  if (saturation == 0) {
    red = green = blue = lightness * 255 / 100;
  } else {
    if (lightness < 50) var2 = lightness * (100 + saturation);
    else var2 = ((lightness + saturation) * 100) - (saturation * lightness);
    var1 = lightness * 200 - var2;
    red = h2rgb(var1, var2, (hue < 240) ? hue + 120 : hue - 240) * 255 / 600000;
    green = h2rgb(var1, var2, hue) * 255 / 600000;
    blue = h2rgb(var1, var2, (hue >= 120) ? hue - 120 : hue + 240) * 255 / 600000;
  }
  setColorRGB(red, green, blue);
}

void Laser::setColorRGB(uint8_t red, uint8_t green, uint8_t blue) {
  _color.r = red;
  _color.g = green;
  _color.b = blue;
}

void Laser::on() {
  analogWrite(_redPin, _color.r);
  analogWrite(_greenPin, _color.g);
  analogWrite(_bluePin, _color.b);
}

void Laser::off() {
  analogWrite(_redPin, 0);
  analogWrite(_greenPin, 0);
  analogWrite(_bluePin, 0);
}
