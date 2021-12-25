import os
import sys
from argparse import ArgumentParser

projectName = "KonamiUnpacker Version 1.0 (https://github.com/Harmmmm/KonamiUnpacker)"


# Parses integer from byte array
def GetNumber(array, location, size, byteorder="little"):
	length = len(array)

	if location > length or location + size > length:
		print("Out of range!")
		return 0

	bytes = array[location:(location + size)]
	number = int.from_bytes(bytes, byteorder=byteorder, signed=False)

	return number

# Read string from byte array untill null terminator
def GetString(array, location):
	buffer = ""
	max = 255
	length = len(array)
	offset = 0

	while True:
		if location + offset > length or offset >= max:
			break

		char = chr(array[location + offset])

		if char == "\x00":
			break

		buffer += chr(array[location + offset])
		offset += 1

	return buffer

# Writes byte array to file
def BytesToFile(fileName, bytes):
	with open(fileName, "wb") as f:
		f.write(bytes)
		f.close()

# Decompresses buffer (unsure what algorithm it is, it looks a bit like LZ77)
def UnpackArchive(InputBuffer, Cursor, SizePacked, OutputBuffer, SizeUnpacked, TempBuffer):
	tempCursor = 0xFEE
	countPacked = SizePacked
	countUnpacked = SizeUnpacked
	ctrl = 0
	combo = 0
	currentByte = 0
	nextByte = 0

	inp = Cursor
	outp = 0

	while True:
		while True:
			ctrl >>= 1

			if ctrl & 0x100 == 0:
				if countPacked < 1:
					return True

				currentByte = InputBuffer[inp]
				inp += 1
				countPacked -= 1
				ctrl = currentByte & 0xFF | 0xFF00

			if ctrl & 1 == 0:
				break

			if countPacked < 1:
				return True

			currentByte = InputBuffer[inp]
			inp += 1
			countPacked += -1

			if countUnpacked < 1:
				print("UnpackArchive Error 1")
				return False

			OutputBuffer[outp] = currentByte
			outp += 1
			countUnpacked -= 1
			TempBuffer[tempCursor] = currentByte
			tempCursor = tempCursor + 1 & 0xFFF

		if countPacked < 1:
			return True

		currentByte = InputBuffer[inp]

		if countPacked -1 < 1:
			break

		nextByte = InputBuffer[inp + 1]
		inp += 2
		countPacked -= 2

		for i in range((nextByte & 0x0F) + 3):
			combo = TempBuffer[((currentByte & 0xFF) | (nextByte & 0xF0) << 4) + i & 0xFFF]

			if countUnpacked < 1:
				print("UnpackArchive Error 2")
				return False
			
			OutputBuffer[outp] = combo
			outp += 1
			countUnpacked -= 1
			TempBuffer[tempCursor] = combo
			tempCursor = tempCursor + 1 & 0xFFF

	return True


# Read arguments
ap = ArgumentParser()
ap.add_argument("-i",  "--input",  type=str, required=True, help="Input bin file (eg D00_DATA.BIN)")
ap.add_argument("-o",  "--output", type=str, required=True, help="Output folder")
args = ap.parse_args()
filePath = args.input
fileName = os.path.basename(filePath)
outputPath = args.output

# Check arguments
if not os.path.isfile(filePath):
	print("Input bin file not found!")
	sys.exit()

if not os.path.isdir(outputPath):
	print("Output folder not found!")
	sys.exit()

# Throw entire file in memory :)
with open(filePath, "rb") as f:
	b = f.read()

fileSize = len(b)
fileCount = GetNumber(b, fileSize - 4, 4) # For some reason this doesn't match the actual number of files

print(projectName)
print(f" Name: {fileName}\n Size: {fileSize}\n Count: {fileCount}")

# Check magic
magic = b[0:4].decode("ascii")
if magic != "BIND":
	print("ERROR: Wrong filetype!")
	sys.exit()

# Parse file
cur = 4
nr = 0

while True:
	type = chr(b[cur])
	path = GetString(b, cur + 1)

	print(f"{nr} {type}: {path} ", end="")

	# Archive (compressed file)
	if type == "A":
		print("unpacking... ", end="", flush=True)
		cur += len(path) + 2
		sizePacked = GetNumber(b, cur, 4) # data + header
		sizeUnpacked = GetNumber(b, cur + 4, 4, "big")
		sizePacked2 = GetNumber(b, cur + 8, 4, "big") # data only

		# Alloc buffers
		outputBuffer = bytearray(sizeUnpacked)
		tempBuffer = bytearray(4116)

		# Unpack
		if not UnpackArchive(b, cur + 12, sizePacked2, outputBuffer, sizeUnpacked, tempBuffer):
			print("failed! (unpacking)")

		# Save to file
		try:
			dirPath = os.path.join(outputPath, path)
			BytesToFile(dirPath, outputBuffer)
		except Exception as e:
			print(f"failed! ({e})")
			sys.exit()

		print("success!")

		cur += 4 + sizePacked
	# File (not compressed file)
	elif type == "F":
		print("extracting... ", end="", flush=True)
		cur += len(path) + 2
		sizeUnpacked = GetNumber(b, cur, 4)

		# Save to file
		try:
			dirPath = os.path.join(outputPath, path)
			BytesToFile(dirPath, b[cur + 4:cur + 4 + sizeUnpacked])
		except Exception as e:
			print(f"failed! ({e})")
			sys.exit()

		print("success!")

		cur += 4 + sizeUnpacked
	# Directory
	elif type == "D":
		print("creating directory... ", end="", flush=True)
		cur += len(path) + 2
		dirPath = os.path.join(outputPath, path)

		# Create directory
		try:
			if not os.path.isdir(dirPath):
				os.mkdir(dirPath)
		except Exception as e:
			print(f"failed! ({e})")
			sys.exit()

		print("success!")
	else:
		print("Done :)")
		break

	nr += 1