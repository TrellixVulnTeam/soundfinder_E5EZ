from audio.python_receiver.receiver import Receiver
from audio.python_receiver.audio import SoundFinder 
from imaging.videoCaptureClass import VideoCapture
from imaging.haarCascadeWArduino import angle_calculation
from multiprocessing import Process, Value, Array

videoCapture = VideoCapture()
def imagingFunc(array):
    array_private = [-1,-1,-1]
    while True:
        array_private = [-1,-1,-1]
        verifiedPeople = videoCapture.run()
        i=0
        for person in verifiedPeople:
            array_private[i] = angle_calculation(person.x)
            print(f"{person} with angle {angle_calculation(person.x)}")
            i=i+1     
        i = 0   
        for angle in array_private:
            array[i] = array_private[i]
            i = i + 1

def audioFunc(sf):
    while True:
        angle = sf.next_angle()  # get next/current angle
        print(f"audio angle: {angle}")

if __name__ == "__main__":

     # sampling & correlation settings
    source_use_file = False   # use device or file
    source = "COM4" if not source_use_file else r"audio\python_receiver\data\sample_gen_example1_32kHz_800Hz_0.0001ms.txt"
    sampling_rate = 32        # kHz  -  MUST MATCH ESP
    frame_size = 768         # #samples  -  MUST MATCH ESP
    mic_distance = 250        # mm  -  MUST MATCH SETUP
    average_delays = 5        # rolling average on sample delay (set to 0 for none)
    normalize_signal = True   # normalize before correlation
    filter_on = True          # butterworth bandpass filter
    filter_lowcut = 400.0     # Hz
    filter_highcut = 1400.0   # Hz
    filter_order = 10         # filter order
    #repeat = True             # sample forever or only once
    graph_samples = True      # generate plot (takes more time)
    angle_edge_calib = 25  #25 # observed incident angle edge (to calibrate, update with incident angle with sound source at edge; 0 for no fine-tuning; usually between 15-45)
    angle_middle_calib = 90   # observed incident angle middle (should be 90)
    frame_length = frame_size / (sampling_rate * 1000)  # sec

    r = Receiver(source, use_file=source_use_file)
    sf = SoundFinder(r, sampling_rate, frame_size, mic_distance, normalize_signal, [filter_lowcut, filter_highcut, filter_order], average_delays, [angle_middle_calib, angle_edge_calib], False, graph_samples)


    arr = Array('d', [-1,-1,-1])
    p1 = Process(target=imagingFunc, args=(arr,))
    #p2 = Process(target=audioFunc, args=(sf,))
    p1.start()
    #p2.start()
    #p1.join()
    #p2.join()

    while True:
        angle = sf.next_angle()  # get next/current angle
        print(f"audio angle: {angle}")
        for person in arr:
            print(person)

