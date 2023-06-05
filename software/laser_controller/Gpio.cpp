#include "Gpio.h"

extern ADC *adc;
SerialTransfer uartTransfer;
uint8_t previousButtons = 0;

struct {
  char line1[41];
  char line2[41];
} txStruct;

struct {
  uint8_t nes;
} rxStruct;

Gpio::Gpio() {
  for (int i = 0; i < 4; i++)
    pinMode(_ledPins[i], OUTPUT);
  for (int i = 0; i < 6; i++)
    pinMode(_cvPins[i], INPUT);

  Serial6.begin(115200);
  uartTransfer.begin(Serial6);
}

void Gpio::setLEDs(uint8_t value) {
  for (int i = 0; i < 4; i++) {
    digitalWrite(_ledPins[i], value & 1);
    value /= 2;
  }
}

uint8_t Gpio::getMode() {
  return adc->analogRead(_modePin, ADC_1) >> 6;
}

int Gpio::getCV(uint8_t index, int min, int max) {
  int res = map(getCV(index), 0, 1023, min, max);

  if (_cvTargets[index] != -1 && abs(res - _cvTargets[index]) < _cvTargetDeltas[index])
    clearCVTarget(index);

  if (_cvTargets[index] == -1)
    return res;
  else
    return _cvTargets[index];
}

int Gpio::getCV(uint8_t index) {
  return adc->analogRead(_cvPins[index], ADC_1);
}

void Gpio::setCVTarget(uint8_t index, int value, int delta) {
  _cvTargets[index] = value;
  _cvTargetDeltas[index] = delta;
}

void Gpio::clearCVTarget(uint8_t index) {
  _cvTargets[index] = -1;
}

void Gpio::displayError(uint8_t value) {
  while (true) {
    setLEDs(value);
    delay(500);
    setLEDs(0);
    delay(500);
  }
}

bool Gpio::readUart() {
  if (uartTransfer.available()) {
    previousButtons = rxStruct.nes;
    uartTransfer.rxObj(rxStruct);
    return true;
  }
  return false;
}

void Gpio::sendUart(const char *line1, const char *line2) {
  sprintf(txStruct.line1, line1);
  sprintf(txStruct.line2, line2);
  uartTransfer.sendDatum(txStruct);
}

bool Gpio::isButtonPressed(uint8_t button) {
  return bitRead(rxStruct.nes, button) == 0;
}

bool Gpio::isButtonReleased(uint8_t button) {
  return bitRead(previousButtons, button) == 0 && 
         bitRead(rxStruct.nes, button) == 1;
}

void Gpio::printButtons() {
  if (isButtonPressed(NES_A)) Serial.print("A ");
  if (isButtonPressed(NES_B)) Serial.print("B ");
  if (isButtonPressed(NES_SELECT)) Serial.print("SELECT ");
  if (isButtonPressed(NES_START)) Serial.print("START ");
  if (isButtonPressed(NES_UP)) Serial.print("UP ");
  if (isButtonPressed(NES_DOWN)) Serial.print("DOWN ");
  if (isButtonPressed(NES_LEFT)) Serial.print("LEFT ");
  if (isButtonPressed(NES_RIGHT)) Serial.print("RIGHT ");
  Serial.println();
}
