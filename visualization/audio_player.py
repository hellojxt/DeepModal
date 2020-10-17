import numpy as np
import os,time,random,sys,math,pyaudio,multiprocessing
import matplotlib.pyplot as plt
from scipy import signal
import scipy.interpolate as interpolate

BITRATE=44100
BUFFERSIZE=1024
BUFFERTIME = 10
NUM = BITRATE*BUFFERTIME//BUFFERSIZE

def osc_process(buffer, pipe):
    buffer = np.frombuffer(buffer.get_obj(), dtype=np.float32)
    while True:
        amp,freq,c,index = pipe.recv()
        amp,freq,c = map(np.array, [amp,freq,c])
        N = len(amp)
        print(amp, freq)
        print('modes_num:{}'.format(N))
        print('max amp:{}'.format(amp.max()))
        t = 0.
        frame = np.arange(BUFFERSIZE).astype(np.float)
        while t < 2 :
            data = np.zeros_like(frame)
            for i in range(N):
                damp = np.exp(-0.5*c[i]*frame/BITRATE)
                sin = np.sin(freq[i]*2*math.pi*frame/BITRATE)
                data += amp[i]*damp*sin

            t += BUFFERSIZE*1.0 / BITRATE
            buffer[index*BUFFERSIZE:(index+1)*BUFFERSIZE] += data.astype(np.float32)
            index = (index + 1) % NUM
            frame += BUFFERSIZE


class Player(object):
    def __init__(self, buffertime = 10):
        self.buffer = multiprocessing.Array(
                        'f',
                        np.zeros(NUM*BUFFERSIZE,dtype=np.float32)
                        )
        self.index = 0
        self.np_buffer = np.frombuffer(self.buffer.get_obj(),dtype=np.float32)
        self.start()
        self.pipe = multiprocessing.Pipe()
        self.osc = multiprocessing.Process(target=osc_process, 
                                args=(self.buffer, self.pipe[1])).start()
    def start(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=pyaudio.paFloat32,channels=1,rate=BITRATE,output=True,
                 stream_callback=self.callback)
        
    def callback(self, in_data, frame_count, time_info, status):
        #print(frame_count)
        self.np_buffer[self.index*BUFFERSIZE:(self.index+1)*BUFFERSIZE] *= 0
        self.index = (self.index + 1) % NUM
        return (self.np_buffer[self.index*BUFFERSIZE:(self.index+1)*BUFFERSIZE], 
                pyaudio.paContinue
                )

    def play(self, amp, freq, c):
        self.pipe[0].send([amp,freq,c,(self.index + 3) % NUM])

    def close(self):
        self.stream.close()
        self.pa.terminate()

        
if __name__ == "__main__":
    player = Player()
    while True:
        input()
        player.play([0.01]*10,[440]*10,[5]*10)
