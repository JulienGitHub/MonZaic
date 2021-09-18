import sys
import os
from PIL import Image, ImageOps
from time import time, sleep
import glob

#size of the loaded pixels in the mozaic
pixelSize = 50

def composeMozaic(file, bigPixelsArray):
	sleep(5) #in case it is locked by os during copy
	sourceImg = Image.open(file)

	#mozaic is zoomValue times bigger than input
	zoomValue = 20
	sourceToMozaicSize = sourceImg.resize((sourceImg.size[0] * zoomValue, sourceImg.size[1] * zoomValue), Image.ANTIALIAS)
	mosaic = Image.new(sourceImg.mode, (sourceImg.size[0] * zoomValue, sourceImg.size[1] * zoomValue))

	nbBigPixelsWidth = int(mosaic.size[0] / pixelSize)
	nbBigPixelsHeight = int(mosaic.size[1] / pixelSize)

	smallPixWidth = int(sourceImg.size[0]/nbBigPixelsWidth)
	smallPixHeight = int(sourceImg.size[1]/nbBigPixelsHeight)
	smallPixelsArray = []
	for bigPixel in bigPixelsArray:
		smallPixelsArray.append(bigPixel.resize((smallPixWidth, smallPixHeight), Image.ANTIALIAS).convert('RGB'))

	for x in range(nbBigPixelsWidth):
		print str(x+1) + "/" + str(nbBigPixelsWidth);
		for y in range(nbBigPixelsHeight):
			rect = (x * pixelSize, y * pixelSize, (x + 1) * pixelSize, (y + 1) * pixelSize)

			subDataOri = sourceToMozaicSize.crop(rect)
			subData = subDataOri.resize((smallPixWidth, smallPixHeight), Image.ANTIALIAS)

			best_index = None
			min = 2147483647 #max of 32bit int
			current_index = 0

			for smallPixel in smallPixelsArray:

				color_distance = 0
				for i in range(len(subData.getdata())):
					color_distance += ((subData.getdata()[i][0] - smallPixel.getdata()[i][0])**2 + (subData.getdata()[i][1] - smallPixel.getdata()[i][1])**2 + (subData.getdata()[i][2] - smallPixel.getdata()[i][2])**2)
					if color_distance > min:
						i = len(subData.getdata());
				if color_distance < min:
					min = color_distance
					best_index = current_index
				current_index += 1
			mosaic.paste(bigPixelsArray[best_index], rect)

	#create the output name
	outputFile = file.replace("input", "output")
	mosaic.save(outputFile)
	print outputFile + " saved"

def StartMosaicThread(inputDirectory, pixelsDirectory):
	#loading the pictures to compose the mozaics
	bigPixelsArray = []
	for file in glob.glob(pixelsDirectory+"\*"):
		img = Image.open(file)
		#let's take only the top part of the card, not the half bottom text
		img = img.crop((180, 30, 840, 690))
		bigPixelsArray.append(img.resize((int(pixelSize), int(pixelSize)), Image.ANTIALIAS).convert('RGB'))
	print "Pixels Loaded"
	while True:
		#find all the png files in the input directory
		for file in glob.glob(inputDirectory+"\*.png"):
			composeMozaic(file, bigPixelsArray)
			#delete the input image
			os.remove(file)
		#sleep 5 seconds before looking again
		sleep(5)
		

if __name__ == '__main__':
	#Calling the loop which takes in the png from the input directory
	StartMosaicThread("input", "data")
