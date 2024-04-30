s.waitForBoot{ 
    SynthDef(\scifi, { |out = 0, x = 0, y = 0, r = 0, gain = 0.1|
        Out.ar(out, CombC.ar(Mix(SinOsc.ar(LFNoise2.kr(1.dup(4)*0.1,y*800+300,[1,2]*(y*800+300)))*0.01),0.2,[0.13,0.2],x*12+3) * gain.dbamp);
    }).store
}