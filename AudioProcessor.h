#ifndef AUDIOPROCESSOR_H
#define AUDIOPROCESSOR_H

#include "Arduino.h"
#include <ADC.h>
#include <AnalogBufferDMA.h>
#include <arduinoFFT.h>

#define FFT_SAMPLES      1024  //total number of audio samples for the FFT
#define FFT_NUM_BINS     256   //number of FFT bins
#define FFT_DISPLAY_BINS 64    //number of bins to render
#define FFT_SKIP_BINS    2     //skip the first two bins since they overwhelm the rest

class AudioProcessor {
public:
  long decay = 0;
  long bands[FFT_DISPLAY_BINS];
  
  bool updateFFT();
  void begin();

private:
  arduinoFFT *_fft;
  double _vReal[FFT_SAMPLES];
  double _vImag[FFT_SAMPLES];
  const int _samplesPerBin = (FFT_SAMPLES / 2) / FFT_NUM_BINS;
};

#endif
