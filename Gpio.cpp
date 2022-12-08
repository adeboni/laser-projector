#include "Gpio.h"

extern ADC *adc;

Gpio::Gpio() {
  for (int i = 0; i < 4; i++)
    pinMode(_ledPins[i], OUTPUT);
  for (int i = 0; i < 6; i++)
    pinMode(_cvPins[i], INPUT);
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
  return map(getCV(index), 0, 1023, min, max);
}

int Gpio::getCV(uint8_t index) {
  return adc->analogRead(_cvPins[index], ADC_1);
}

void Gpio::displayError(uint8_t value) {
  while (true) {
    setLEDs(value);
    delay(500);
    setLEDs(0);
    delay(500);
  }
}
