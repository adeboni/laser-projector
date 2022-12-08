#include "AudioProcessor.h"

extern ADC *adc;

DMAMEM static volatile uint16_t __attribute__((aligned(32))) dma_adc_buff1[FFT_SAMPLES];
DMAMEM static volatile uint16_t __attribute__((aligned(32))) dma_adc_buff2[FFT_SAMPLES];
AnalogBufferDMA abdma(dma_adc_buff1, FFT_SAMPLES, dma_adc_buff2, FFT_SAMPLES);

void AudioProcessor::begin() {
  pinMode(A2, INPUT);
  adc->adc0->setResolution(10);
  adc->adc0->setConversionSpeed(ADC_CONVERSION_SPEED::MED_SPEED);
  adc->adc0->setSamplingSpeed(ADC_SAMPLING_SPEED::VERY_LOW_SPEED);
  abdma.init(adc, ADC_0);
  adc->adc0->startContinuous(A2);
  _fft = new arduinoFFT();
}

bool AudioProcessor::updateFFT() {
  if (!abdma.interrupted()) return false;

  volatile uint16_t *pbuffer = abdma.bufferLastISRFilled();
  volatile uint16_t *end_pbuffer = pbuffer + abdma.bufferCountLastISRFilled();
  if ((uint32_t)pbuffer >= 0x20200000u) arm_dcache_delete((void*)pbuffer, sizeof(dma_adc_buff1));

  int i = 0;
  while (pbuffer < end_pbuffer) {
    _vReal[i] = (int)(*pbuffer);
    _vImag[i] = 0;
    i++;
    pbuffer++;
  }

  _fft->DCRemoval();
  _fft->Windowing(_vReal, FFT_SAMPLES, FFT_WIN_TYP_HAMMING, FFT_FORWARD);
  _fft->Compute(_vReal, _vImag, FFT_SAMPLES, FFT_FORWARD);
  _fft->ComplexToMagnitude(_vReal, _vImag, FFT_SAMPLES);

  for (int i = FFT_SKIP_BINS; i < FFT_DISPLAY_BINS; i++) {
    long fVal = 0;
    for (int j = 0; j < _samplesPerBin; j++)
      fVal += (long)_vReal[i * _samplesPerBin + j];
    fVal = constrain(fVal / _samplesPerBin, 0, 2048);
    if (bands[i - FFT_SKIP_BINS] > 0) bands[i - FFT_SKIP_BINS] -= decay;
    if (fVal > bands[i - FFT_SKIP_BINS]) bands[i - FFT_SKIP_BINS] = fVal;
  }

  abdma.clearInterrupt();
  return true;
}
