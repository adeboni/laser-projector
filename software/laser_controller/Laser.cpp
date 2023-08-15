#include "Laser.h"

Laser::Laser(uint8_t redPin, uint8_t greenPin, uint8_t bluePin, uint8_t dacPin) {
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
	
  _dacPin = dacPin;
  pinMode(dacPin, OUTPUT);
  digitalWrite(dacPin, HIGH);
  calculateHomography();
}

void Laser::setQuality(float quality) {
  _quality = quality;
}

void Laser::getQuality(float& quality) {
  quality = _quality;
}

void Laser::setDelays(int toggleDelay, int dacDelay) {
  if (toggleDelay >= 0) _toggleDelay = toggleDelay;
  if (dacDelay >= 0) _dacDelay = dacDelay;
}

void Laser::getDelays(int& toggleDelay, int& dacDelay) {
  toggleDelay = _toggleDelay;
  dacDelay = _dacDelay;
}

void Laser::setMirroring(bool x, bool y, bool xy) {
  _mirrorX = x;
  _mirrorY = y;
  _mirrorXY = xy;
}

void Laser::getMirroring(bool& x, bool& y, bool& xy) {
  x = _mirrorX;
  y = _mirrorY;
  xy = _mirrorXY;
}

void Laser::setScale(float scaleX, float scaleY) { 
  _scaleX = scaleX;
  _scaleY = scaleY;
}

void Laser::getScale(float& scaleX, float& scaleY) {
  scaleX = _scaleX;
  scaleY = _scaleY;
}

void Laser::setOffset(int offsetX, int offsetY) { 
  _offsetX = offsetX;
  _offsetY = offsetY;
}

void Laser::getOffset(int& offsetX, int& offsetY) {
  offsetX = _offsetX;
  offsetY = _offsetY;
}

void Laser::setClipArea(int x1, int y1, int x2, int y2, int x3, int y3, int x4, int y4) {
  _clipPoly[0] = x1;
  _clipPoly[1] = y1;
  _clipPoly[2] = x2;
  _clipPoly[3] = y2;
  _clipPoly[4] = x3;
  _clipPoly[5] = y3;
  _clipPoly[6] = x4;
  _clipPoly[7] = y4;
}

void Laser::setClipAreaTop(int x1, int y1, int x2, int y2) {
  _clipPoly[0] = x1;
  _clipPoly[1] = y1;
  _clipPoly[2] = x2;
  _clipPoly[3] = y2;
}

void Laser::setClipAreaBottom(int x3, int y3, int x4, int y4) {
  _clipPoly[4] = x3;
  _clipPoly[5] = y3;
  _clipPoly[6] = x4;
  _clipPoly[7] = y4;
}

void Laser::getClipArea(int& x1, int& y1, int& x2, int& y2, int& x3, int& y3, int& x4, int& y4) {
  x1 = _clipPoly[0];
  y1 = _clipPoly[1];
  x2 = _clipPoly[2];
  y2 = _clipPoly[3];
  x3 = _clipPoly[4];
  y3 = _clipPoly[5];
  x4 = _clipPoly[6];
  y4 = _clipPoly[7];
}

void Laser::setWarpArea(int x1, int y1, int x2, int y2, int x3, int y3, int x4, int y4) {
  _warpPolyDst[0] = x1;
  _warpPolyDst[1] = y1;
  _warpPolyDst[2] = x2;
  _warpPolyDst[3] = y2;
  _warpPolyDst[4] = x3;
  _warpPolyDst[5] = y3;
  _warpPolyDst[6] = x4;
  _warpPolyDst[7] = y4;
  calculateHomography();
}

void Laser::setWarpAreaTop(int x1, int y1, int x2, int y2) {
  _warpPolyDst[0] = x1;
  _warpPolyDst[1] = y1;
  _warpPolyDst[2] = x2;
  _warpPolyDst[3] = y2;
  calculateHomography();
}

void Laser::setWarpAreaBottom(int x3, int y3, int x4, int y4) {
  _warpPolyDst[4] = x3;
  _warpPolyDst[5] = y3;
  _warpPolyDst[6] = x4;
  _warpPolyDst[7] = y4;
  calculateHomography();
}

void Laser::getWarpArea(int& x1, int& y1, int& x2, int& y2, int& x3, int& y3, int& x4, int& y4) {
  x1 = _warpPolyDst[0];
  y1 = _warpPolyDst[1];
  x2 = _warpPolyDst[2];
  y2 = _warpPolyDst[3];
  x3 = _warpPolyDst[4];
  y3 = _warpPolyDst[5];
  x4 = _warpPolyDst[6];
  y4 = _warpPolyDst[7];
}

void Laser::setPreviousPosition(int x, int y) {
  _oldX = x;
  _oldY = y;
}

void Laser::getPreviousPosition(int& x, int& y) {
  x = _oldX;
  y = _oldY;
}

void Laser::setPreviousPositionClipped(int x, int y) {
  _x = x;
  _y = y;
}

void Laser::getPreviousPositionClipped(int& x, int& y) {
  x = _x;
  y = _y;
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

void Laser::setColor(const Color& color) {
  _color = color;
}

void Laser::on() {
  if (!_laserOn && _toggleDelay > 0) delayMicroseconds(_toggleDelay);
  _laserOn = true;
  analogWrite(_redPin, _color.r);
  analogWrite(_greenPin, _color.g);
  analogWrite(_bluePin, _color.b);
}

void Laser::off() {
  if (_laserOn && _toggleDelay > 0) delayMicroseconds(_toggleDelay);
  _laserOn = false;
  analogWrite(_redPin, 0);
  analogWrite(_greenPin, 0);
  analogWrite(_bluePin, 0);
}


void Laser::writeDAC(int x, int y) {
  //warpPerspective(x, y);

  int x1 = constrain(x, 0, 4095);
  int y1 = constrain(y, 0, 4095);

  if (_mirrorXY) SWAP(x1, y1);
  if (_mirrorX)  x1 = 4095 - x1;
  if (_mirrorY)  y1 = 4095 - y1;

  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  digitalWrite(_dacPin, LOW);
  SPI.transfer(0x30 | ((x1 >> 8) & 0x0f));
  SPI.transfer(x1 & 0xff);
  digitalWrite(_dacPin, HIGH);
  SPI.endTransaction();

  SPI.beginTransaction(SPISettings(20000000, MSBFIRST, SPI_MODE0));
  digitalWrite(_dacPin, LOW);
  SPI.transfer(0xb0 | ((y1 >> 8) & 0x0f));
  SPI.transfer(y1 & 0xff);
  digitalWrite(_dacPin, HIGH); 
  SPI.endTransaction();

  if (_dacDelay > 0) delayMicroseconds(_dacDelay);
}

const int INSIDE = 0; // 0000
const int LEFT = 1;   // 0001
const int RIGHT = 2;  // 0010
const int BOTTOM = 4; // 0100
const int TOP = 8;    // 1000

int Laser::computeOutCode(long x, long y) {
  int code = INSIDE;          // initialised as being inside of [[clip window]]

  if (x < _clipXMin)           // to the left of clip window
    code |= LEFT;
  else if (x > _clipXMax)      // to the right of clip window
    code |= RIGHT;
  if (y < _clipYMin)           // below the clip window
    code |= BOTTOM;
  else if (y > _clipYMax)      // above the clip window
    code |= TOP;

  return code;
}

// Cohen–Sutherland clipping algorithm clips a line from
// P0 = (x0, y0) to P1 = (x1, y1) against a rectangle with 
// diagonal from (_clipXMin, _clipYMin) to (_clipXMax, _clipYMax).
bool Laser::clipLine(long& x0, long& y0, long& x1, long& y1) {
  // compute outcodes for P0, P1, and whatever point lies outside the clip rectangle
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

      // Now we move outside point to intersection point to clip
      // and get ready for next pass.
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
/*

bool Laser::clipLine(int& x1, int& y1, int& x2, int& y2) { 
  int dotx = x2 - x1;
  int doty = y2 - y1;
  float tEnteringMax = 0;
  float tLeavingMin = 1;
  
  for (int i = 0; i < 4; i++) {
    int normalx = _clipPoly[i*2+1] - _clipPoly[((i+1)%4)*2+1];
    int normaly = _clipPoly[((i+1)%4)*2] - _clipPoly[i*2];
    int numerator = normalx * (_clipPoly[i*2] - x1) + normaly * (_clipPoly[i*2+1] - y1);
    float denominator = normalx * dotx + normaly * doty;
    float t = denominator == 0 ? numerator : numerator / denominator;
    
    if (denominator >= 0) tEnteringMax = max(t, tEnteringMax);
    else tLeavingMin = min(t, tLeavingMin);
  }
  
  if (tEnteringMax > tLeavingMin) 
    return false;

  x2 = (int)(x1 + dotx * tLeavingMin);
  y2 = (int)(y1 + doty * tLeavingMin);
  x1 = (int)(x1 + dotx * tEnteringMax);
  y1 = (int)(y1 + doty * tEnteringMax);
  return true;
}
*/

void Laser::sendTo(int xpos, int ypos) {
  if (_enable3D) {
    Vector3 p1 = {xpos - 2048, ypos - 2048, 0};
    Vector3 p = Matrix4::applyMatrix(_matrix, p1);
    xpos = (_zDist * p.x) / (_zDist + p.z) + 2048;
    ypos = (_zDist * p.y) / (_zDist + p.z) + 2048;
  }

  int xNew = (int)(xpos * _scaleX) + _offsetX;
  int yNew = (int)(ypos * _scaleY) + _offsetY; 
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

void Laser::sendToRaw(int xNew, int yNew) { 
  // divide into equal parts, using _quality
  float fdiffx = xNew - _x;
  float fdiffy = yNew - _y;
  float diffx = abs(fdiffx) / _quality;
  float diffy = abs(fdiffy) / _quality;

  // use the bigger direction 
  float maxDiff = max(diffx, diffy);
  fdiffx = fdiffx / maxDiff;
  fdiffy = fdiffy / maxDiff;
  
  // interpolate in FIXPT
  float tmpx = 0;
  float tmpy = 0;
  for (int i = 0; i < maxDiff - 1; i++) {
    tmpx += fdiffx;
    tmpy += fdiffy;
    writeDAC(_x + (int)tmpx, _y + (int)tmpy);
  }
  
  _x = xNew;
  _y = yNew;
  writeDAC(_x, _y);
}


void Laser::calculateHomography() {
  Matrix8 coefMat;
  for (int i = 0; i < 4; i++) {
    coefMat.m[2 * i][0] = _warpPolySrc[2 * i];
    coefMat.m[2 * i][1] = _warpPolySrc[2 * i + 1];
    coefMat.m[2 * i][2] = 1;
    coefMat.m[2 * i][3] = 0;
    coefMat.m[2 * i][4] = 0;
    coefMat.m[2 * i][5] = 0;
    coefMat.m[2 * i][6] = -_warpPolyDst[2 * i] * _warpPolySrc[2 * i];
    coefMat.m[2 * i][7] = -_warpPolyDst[2 * i] * _warpPolySrc[2 * i + 1];

    coefMat.m[2 * i + 1][0] = 0;
    coefMat.m[2 * i + 1][1] = 0;
    coefMat.m[2 * i + 1][2] = 0;
    coefMat.m[2 * i + 1][3] = _warpPolySrc[2 * i];
    coefMat.m[2 * i + 1][4] = _warpPolySrc[2 * i + 1];
    coefMat.m[2 * i + 1][5] = 1;
    coefMat.m[2 * i + 1][6] = -_warpPolyDst[2 * i + 1] * _warpPolySrc[2 * i];
    coefMat.m[2 * i + 1][7] = -_warpPolyDst[2 * i + 1] * _warpPolySrc[2 * i + 1];
  }

  Matrix8 invCoefMat = Matrix8::invert(coefMat);

  for (int i = 0; i < 8; i++) {
    _homography[i] = 0;
    for (int j = 0; j < 8; j++)
      _homography[i] += invCoefMat.m[i][j] * _warpPolyDst[j];
  }
  _homography[8] = 1;
}

void Laser::warpPerspective(int& x, int& y) {
  float dst1 = _homography[0] * x + _homography[1] * y + _homography[2];
  float dst2 = _homography[3] * x + _homography[4] * y + _homography[5];
  float dst3 = _homography[6] * x + _homography[7] * y + _homography[8];

  x = (int)(dst1 / dst3);
  y = (int)(dst2 / dst3);
}
