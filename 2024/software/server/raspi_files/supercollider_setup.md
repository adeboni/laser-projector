sudo apt-get update
sudo apt-get upgrade
sudo apt-get install libsamplerate0-dev libsndfile1-dev libasound2-dev libavahi-client-dev libreadline-dev libfftw3-dev libudev-dev libncurses5-dev cmake git audacity portaudio19-dev

cd ~
git clone --recurse-submodules https://github.com/supercollider/supercollider.git
cd supercollider
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DSUPERNOVA=OFF -DSC_ED=OFF -DSC_EL=OFF -DSC_VIM=ON -DNATIVE=ON -DSC_IDE=OFF -DNO_X11=ON -DSC_QT=OFF -DAUDIOAPI=portaudio ..
cmake --build . --config Release --target all -- -j3
sudo cmake --build . --config Release --target install
sudo ldconfig
