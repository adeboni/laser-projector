#ifndef CALIBRATION_H
#define CALIBRATION_H

#include "Laser.h"
#include "Gpio.h"

#define MODE_END_CAL        -1
#define MODE_OFFSET          0
#define MODE_DISTORTION      1
#define MODE_CLIPPING_TOP    2
#define MODE_CLIPPING_BOTTOM 3
#define MODE_WARP_TOP        4
#define MODE_WARP_BOTTOM     5

void offsetAlignment();
void distortionAlignment();
void clippingTopAlignment();
void clippingBottomAlignment();
void warpTopAlignment();
void warpBottomAlignment();
void beginCalibration();
void checkButtons();

#endif
