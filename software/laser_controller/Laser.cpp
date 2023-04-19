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
}

void Laser::setQuality(float quality) {
  _quality = quality;
}

void Laser::setDelays(int toggleDelay, int lineEndDelay, int endDelay) {
  _toggleDelay = toggleDelay;
  _lineEndDelay = lineEndDelay;
  _endDelay = endDelay;
}

void Laser::setMirroring(bool x, bool y, bool xy) {
  _mirrorX = x;
  _mirrorY = y;
  _mirrorXY = xy;
}

void Laser::setScale(float scaleX, float scaleY) { 
  _scaleX = scaleX;
  _scaleY = scaleY;
}

void Laser::setOffset(int offsetX, int offsetY) { 
  _offsetX = offsetX;
  _offsetY = offsetY;
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

void Laser::setDistortionFactors(int x, float y) {
  _xDistortionFactor = x;
  _yDistortionFactor = y;
}

void Laser::writeDAC(int x, int y) {
  //apply distortion corrections
  //x = ((x - 2048) * COS(ABS(y - 2048) / _xDistortionFactor)) + 2048;
  //y = ((y - 2048) * _yDistortionFactor) + 2048;

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
}

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

void Laser::sendTo(int xpos, int ypos) {
  _sentX = xpos;
  _sentY = ypos;

  if (_enable3D) {
    Vector3 p1 = {xpos - 2048, ypos - 2048, 0};
    Vector3 p = Matrix4::applyMatrix(_matrix, p1);
    xpos = (_zDist * p.x) / (_zDist + p.z) + 2048;
    ypos = (_zDist * p.y) / (_zDist + p.z) + 2048;
  }

  int xNew = (int)(xpos * _scaleX) + _offsetX;
  int yNew = (int)(ypos * _scaleY) + _offsetY; 
  int clipX = xNew;
  int clipY = yNew;
  int oldX = _oldX;
  int oldY = _oldY;
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
  fdiffx = fdiffx / max(diffx, diffy);
  fdiffy = fdiffy / max(diffx, diffy);
  // interpolate in FIXPT
  float tmpx = 0;
  float tmpy = 0;
  for (int i = 0; i < diffx - 1; i++) {
    tmpx += fdiffx;
    tmpy += fdiffy;
    writeDAC(_x + tmpx, _y + tmpy);
  }
  
  _x = xNew;
  _y = yNew;
  writeDAC(_x, _y);

  if (_endDelay > 0) delayMicroseconds(_endDelay);
}

void Laser::drawLine(int x1, int y1, int x2, int y2) {
  if (_sentX != x1 || _sentY != y1) {
    off();
    sendTo(x1, y1);
  } 
  on();
  sendTo(x2, y2);
  if (_lineEndDelay > 0) delayMicroseconds(_lineEndDelay);
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

void Laser::getQuality(float& quality) {
  quality = _quality;
}

void Laser::getDistortionFactors(int& x, float& y) {
  x = _xDistortionFactor;
  y = _yDistortionFactor;
}

void Laser::getMirroring(bool& x, bool& y, bool& xy) {
  x = _mirrorX;
  y = _mirrorY;
  xy = _mirrorXY;
}

void Laser::getScale(float& scaleX, float& scaleY) {
  scaleX = _scaleX;
  scaleY = _scaleY;
}

void Laser::getOffset(int& offsetX, int& offsetY) {
  offsetX = _offsetX;
  offsetY = _offsetY;
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

void Laser::getDelays(int& toggleDelay, int& lineEndDelay, int& endDelay) {
  toggleDelay = _toggleDelay;
  lineEndDelay = _lineEndDelay;
  endDelay = _endDelay;
}
