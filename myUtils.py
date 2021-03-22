from threading import Thread
from multiprocessing import Process, Queue, Value
import cv2
# from queue import Queue
import time


class FrameVideoStream:
    def __init__(self, queueSize=50):
        self.frame=0
        # self.name= window
        self.Q=Queue(maxsize=queueSize)
        self.Process_Q= Queue(maxsize=queueSize) # Process Queue
        self.stop_stream=False

    def start(self):
        t=Thread(target=self.update,args=())
        t2=Thread(target=self.display,args=())
        # p1=Process(target=self.update_proc,args=()) # The new process

        t.daemon=True
        t2.daemon=True
        # p1.daemon=True
        
        t.start()
        t2.start()
        # p1.start()
        return self 

    def get_frame(self, img):
        # print("################got frame#####################")
        self.frame=img

    def update(self):
        try:
            while True:
                print("",end="\r")
                # time.sleep(0.001)
                if self.stop_stream:
                    return
                
                if not self.Q.full():
                    self.Q.put(self.frame)
        except KeyboardInterrupt:
            print(" keyboard interr returning")
            return

    def update_proc(self):
        try:
            while True:
                print("",end="\r")
                if self.stop_stream:
                    return
                if not self.Process_Q.full():
                    self.Process_Q.put(self.frame)
        except KeyboardInterrupt:
            print(" keyboard interr returning")
            return

    # def get_centroid(self):
    #     print(" centroid func")
    #     pass

    def read(self):
        return self.Q.get()

    def read_Proc_Q(self):
        return self.Process_Q.get()

    def more(self):
        return self.Q.qsize() > 0

    def stop(self):
        self.stop_stream = True

    def display(self):
        try:          
            while self.more():
                frame= self.read()
                cv2.imshow("Client Window ", frame)
                # cv2.putText(frame, "Queue Size: {}".format(self.Q.qsize()),(10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)	
                cv2.waitKey(1)
        except KeyboardInterrupt:
            # cv2.destroyAllWindows()
            pass
        finally:
            print("destroy cv2 window")
            # cv2.destroyAllWindows()
            return

