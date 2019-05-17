import asyncio
import RPi.GPIO as GPIO
import socketio
import time


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


class Table(object):
    
    def __init__(self, coilA1, coilA2, coilB1, coilB2, delay=.001):
        self.coil_A_1_pin = coilA1
        self.coil_A_2_pin = coilA2
        self.coil_B_1_pin = coilB1
        self.coil_B_2_pin = coilB2
        self.delay = delay
        self.position = 0
        #
        # adjust if different
        self.StepCount = 8
        self.Seq = [
            [0,1,0,0],
            [0,1,0,1],
            [0,0,0,1],
            [1,0,0,1],
            [1,0,0,0],
            [1,0,1,0],
            [0,0,1,0],
            [0,1,1,0],
        ]
        #
        GPIO.setup(self.coil_A_1_pin, GPIO.OUT)
        GPIO.setup(self.coil_A_2_pin, GPIO.OUT)
        GPIO.setup(self.coil_B_1_pin, GPIO.OUT)
        GPIO.setup(self.coil_B_2_pin, GPIO.OUT)
        
    def setStep(self, w1, w2, w3, w4):
        GPIO.output(self.coil_A_1_pin, w1)
        GPIO.output(self.coil_A_2_pin, w2)
        GPIO.output(self.coil_B_1_pin, w3)
        GPIO.output(self.coil_B_2_pin, w4)

    async def forward(self, steps=None, angle=None):
        if steps is None:
            steps = self.get_steps(angle)
        self.position += steps
        for i in range(steps):
            for j in range(self.StepCount):
                self.setStep(
                    self.Seq[j][0], 
                    self.Seq[j][1], 
                    self.Seq[j][2], 
                    self.Seq[j][3]
                )
                time.sleep(self.delay)
                await asyncio.sleep(0)
        self.setStep(0,0,0,0)

    async def backward(self, steps=None, angle=None):
        if steps is None:
            steps = self.get_steps(angle)
        self.position -= steps
        for i in range(steps):
            for j in reversed(range(self.StepCount)):
                self.setStep(
                    self.Seq[j][0], 
                    self.Seq[j][1], 
                    self.Seq[j][2], 
                    self.Seq[j][3]
                )
                time.sleep(self.delay)
                await asyncio.sleep(0)
        self.setStep(0,0,0,0)
        
    async def reset(self):
        if self.position > 0:
            await self.backward(self.position)
        elif self.position < 0:
            await self.forward(self.position)
        self.position = 0
        
    def get_steps(self, angle):
        print('steps: %s' % int(angle/360.0 * 518))
        return int(angle/360.0 * 518)  # last num is full 360 step count


#coil_A_1_pin = 4 # gray - 2
#coil_A_2_pin = 17 # white - 4
#coil_B_1_pin = 23 # green - 1
#coil_B_2_pin = 24 # brown - 3

sio = socketio.AsyncClient()
tables = {
    1: Table(4, 17, 23, 24),
    2: Table(20, 12, 21, 16),
}

@sio.on('connect')
def on_connect():
	print('connect')

@sio.on('message')
def on_message(data):
    print('message')

@sio.on('reset')
async def on_reset(data):
    print('reset')
    await asyncio.wait([tbl.reset() for tbl in tables.values()])
        
@sio.on('turn')
async def on_turn(data):
    print('turn')
    await tables.get(data['table']).forward(angle=90)
#    if data:
#        print(data)
#        tbl = tables.get(data['table'])
#        if tbl:
#            await tbl.forward(angle=data['turn'])
            
async def start_server():
    await sio.connect('http://10.10.36.246:8080')
    await sio.wait()
            
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server())
