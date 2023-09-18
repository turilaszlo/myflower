import gc, webrepl
from main import *

gc.collect()

uploadData(moistureSensor())
webrepl.start()
accessPoint()
