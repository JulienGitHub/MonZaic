import os
import sys
from PIL import Image
from time import time, sleep
import glob
import time
from multiprocessing import Process, Queue

sourceToMozaicSize = Image

#size of the loaded pixels in the mozaic
pixelSize = 50

def PutXLPixel(data, results, xsPixelsArray, sourceToMozaicSize, totalPix):
	while True:
		try:
			x, y = data.get(True)
			if x == -1:
				break
			rect = (x * pixelSize, y * pixelSize, (x + 1) * pixelSize, (y + 1) * pixelSize)
			subDataOri = sourceToMozaicSize.crop(rect)
			subData = subDataOri.resize((1, 1), Image.ANTIALIAS)

			best_index = None
			min = 2147483647 #max of 32bit int
			current_index = 0
			for xsPixel in xsPixelsArray:
				color_distance = ((subData.getdata()[0][0] - xsPixel[0])**2 + (subData.getdata()[0][1] - xsPixel[1])**2 + (subData.getdata()[0][2] - xsPixel[2])**2)
				if color_distance < min:
					min = color_distance
					best_index = current_index
				current_index += 1
			results.put((best_index, rect))
		except:
			pass
	results.put((-1, (0, 0)))

def composeMozaic(file, xlPixelsArray, xsPixelsArray):
	sleep(5) #in case it is locked by os during copy
	start_time = time.time()
	sourceImg = Image.open(file)
	
	#mozaic is [zoomValue] times bigger than input
	zoomValue = 20
	global sourceToMozaicSize
	sourceToMozaicSize = sourceImg.resize((sourceImg.size[0] * zoomValue, sourceImg.size[1] * zoomValue), Image.ANTIALIAS)
	mosaic = Image.new(sourceImg.mode, (sourceImg.size[0] * zoomValue, sourceImg.size[1] * zoomValue))

	nbBigPixelsWidth = int(mosaic.size[0] / pixelSize)
	nbBigPixelsHeight = int(mosaic.size[1] / pixelSize)

	nbProcesses = 4
	data = Queue(nbProcesses)	
	results = Queue()
	
	for n in range(nbProcesses):
		Process(target=PutXLPixel, args=(data, results, xsPixelsArray, sourceToMozaicSize, nbBigPixelsWidth*nbBigPixelsHeight)).start()

	for x in range(nbBigPixelsWidth):	
		for y in range(nbBigPixelsHeight):
			data.put((x, y))
	for n in range(nbProcesses):
		data.put((-1, -1))

	active_processes = nbProcesses
	while True:
		xlIndex, rect = results.get(True)
		if xlIndex == -1:
			active_processes -= 1
			if active_processes <= 0:
				break
		else:
			mosaic.paste(xlPixelsArray[xlIndex], rect)
	
	#create the output name
	outputFile = file.replace("input", "output")
	print("Saving Mozaic to " + outputFile)
	mosaic.save(outputFile)
	print(outputFile + " saved")
	print("--- %s seconds ---" % (time.time() - start_time))

def StartMosaicThread(inputDirectory, pixelsDirectory):
	#loading the pictures to compose the mozaics
	xlPixelsArray = []
	xsPixelsArray = []

	files = glob.glob(pixelsDirectory+"\*")
	count = 0
	for file in files:
		img = Image.open(file)
		print("Loading " + str(count+1) + "/" + str(len(files)) + " - " + file, end="\r", flush=True)
		#let's take only the top part of the card, not the half bottom text
		img = img.crop((180, 30, 840, 690))
		xlPixelsArray.append(img.resize((int(pixelSize), int(pixelSize)), Image.ANTIALIAS).convert('RGB'))
		pixel = img.resize((1, 1), Image.ANTIALIAS).convert('RGB').getdata()[0]		
		xsPixelsArray.append(pixel)
		count += 1
	print()
	print(str(len(xsPixelsArray)) + " Pixels Loaded")

	while True:
		#find all the png files in the input directory
		for file in glob.glob(inputDirectory+"\*.png"):
			composeMozaic(file, xlPixelsArray, xsPixelsArray)
			#delete the input image
			os.remove(file)
		#sleep 5 seconds before looking again
		sleep(5)

if __name__ == '__main__':
	#Calling the loop which takes in the png from the input directory
	StartMosaicThread("input", "data")
