# Textual progressbar
# by Olivier R.
# License: MPL 2

import time

class ProgressBar:
    "Textual progressbar"
    
    def __init__ (self, nMin=0, nMax=100, nWidth=78):
        "initiate with minimum nMin to maximum nMax"
        self.nMin = nMin
        self.nMax = nMax
        self.nSpan = nMax - nMin
        self.nWidth = nWidth-9
        self.nAdvance = -1
        self.nCurVal = nMin
        self.startTime = time.time()
        self._update()

    def _update (self):
        fDone = ((self.nCurVal - self.nMin) / self.nSpan)
        nAdvance = int(fDone * self.nWidth)
        if (nAdvance > self.nAdvance):
            self.nAdvance = nAdvance
            print("\r[ {}{}  {}% ] ".format('>'*nAdvance, ' '*(self.nWidth-nAdvance), round(fDone*100)), end="")

    def increment (self, n=1):
        "increment value by n (1 by default)"
        self.nCurVal += n
        self._update()
    
    def done (self):
        "to call when it’s finished"
        print("\r[ task done in {:.1f} s ] ".format(time.time() - self.startTime))
