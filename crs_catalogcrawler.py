import re
import requests
import cPickle as pickle
import string
import network_operations as netops
import csv

# load pickled course catalog file
try:
	courseCatalog = pickle.load(open("course_catalog.p", "rb")) 
except Exception as e:
	courseCatalog = {}
	for letter in string.ascii_lowercase:
		courseCatalog[letter] = {}
	pickle.dump(courseCatalog, open("courseCatalog.p", "wb"))
	# Failed to load course catalog file so create a new one

try:
	classScheds = pickle.load(open("class_scheds.p", "rb"))
except Exception as e:
	# Class Sched Structure:
	# [ Class Code | Class | Credits | Schedule | | Instructor | Remarks
	#   Enlisting Unit | Available / Total Slots | Demand | Restrictions ]
	# Parsing the Schedule
	# Samples:
	# T 4:30-6:30PM lec Archi 1; Th 4:30-6:30PM lec Archi 104A <-- just split("; ")
	# TTh 8AM-12:30PM lab Archi 1
	# TBA
	classScheds = {}
	pickle.dump(classScheds, open("class_scheds.p", "wb"))

# Parses sched and returns dict of days
def parseSchedDay(text):
	dayDict = ["M", "T", "W", "Th", "F", "S"]
	returnDays = []
	i = 0
	while i < len(dayDict):
		# print text
		# print returnDays
		day = dayDict[i]
		if text.find(day) == 0:
			if day == "T":
				if text.find("h") == 1:
					# print "TRUEEE"
					# go to next day
					i = i + 1
				else:
					# print "FALSE"
					returnDays.append(day)
					text = text[len(day)::]
			else:
				returnDays.append(day)
				text = text[len(day)::]
		else:
			i = i + 1
	return returnDays

# Processes the retrieved HTML catalog files
def page_process():
	for letter in string.ascii_lowercase:
		fileName = "Course Catalog/catalog_%s.txt"%(letter)
		currentFile = open(fileName, "r")
		searchLines = currentFile.readlines()

		# Find start of table
		blockStartOdd = "<tr class=\"tr_odd\">"
		blockStartEven = "<tr class=\"tr_even\">"
		blockEnd = "</tbody></table>"

		i = 0
		startFound = False
		while True and (i < len(searchLines)):
			if (searchLines[i].find(blockStartOdd) != -1) or (searchLines[i].find(blockStartEven) != -1):
				startFound = True
				sl_index = 4
				offset = 0
				courseCode = searchLines[i + 1]
				courseTitle = searchLines[i + 2]

				# print "courseCode:%s\ncourseTitle:%s\ncourseDesc:%s\nofferingUnit:%s\n" % (courseCode, courseTitle, courseDesc, offeringUnit)

				# do regex
				codeMatch = re.search(".*>(?P<course_code>.*)<.*", courseCode)
				titleMatch = re.search(".*>(?P<course_title>.*)<.*", courseTitle)
				if titleMatch:
					pass
				else:
					titleMatch = re.search(".*>(?P<course_title>.*)", courseTitle)
					offset = 1
				courseDesc = searchLines[i + 3 + offset]
				descMatch = re.search(".*>(?P<course_desc>.*)<.*", courseDesc)
				unitMatch = None
				while True:
					offeringUnit = searchLines[i + sl_index + offset]
					unitMatch = re.search(".*>(?P<offering_unit>.*)<.*", offeringUnit)
					if unitMatch:
						print "Found offering unit with no problems"
						#proceed without problem
						break
					else:
						print "sl_index: %d" % (sl_index)
						sl_index = sl_index + 1
				# add to courseCatalog
				newCourse = {}
				courseCode = codeMatch.group("course_code")
				newCourse["title"] = titleMatch.group("course_title")
				if descMatch:
					newCourse["desc"] = descMatch.group("course_desc")
				else:
					print courseDesc
					newCourse["desc"] = None
				newCourse["offeringUnit"] = unitMatch.group("offering_unit")

				if not courseCode in courseCatalog[letter].keys():
					courseCatalog[letter][courseCode] = newCourse
					print "Added: %s/%s"%(letter, courseCode)

				i = i + sl_index + 2 + offset
				# if start of block is found
			elif startFound:
				if searchLines[i].find(blockEnd) != -1:
					# End of table is found
					break
				else:
					i = i + 1
			else: 
				i = i + 1

		pickle.dump(courseCatalog, open("courseCatalog.p", "wb"))
		currentFile.close()

def catalog_crawl():
	#for index a - z
	baseURL = "https://crs.upd.edu.ph/course_catalog/index/"
	for letter in string.ascii_lowercase:
		indexURL = baseURL + letter
		fileName = "catalog_" + letter + ".txt"
		filePath = "Course Catalog/"
		netops.downloadPage(url=indexURL, fileName=fileName, filePath=filePath)
		print "Done with %s%s" % (filePath, fileName)

# Processes retrieved HTML schedule files
def sched_process():
	for letter in string.ascii_uppercase:
		fileName = "Class Schedules/schedule_%s.txt"%(letter)
		currentFile = open(fileName, "r")
		searchLines = currentFile.readlines()

		blockStart = "<tbody style=\"border-bottom: 1px solid gray\">"
		blockEnd = "</table>"
		endBody = "</tbody>"

		i = 0
		startFound = False
		while True and (i < len(searchLines)):
			# print "i = %d" % i
			if searchLines[i].find(endBody) != -1:
				print "ENTERED END BODY"
				i = i + 1
			elif searchLines[i].find(blockStart) != -1:
				# Find course code
				newClass = {}
				courseCode = searchLines[i + 2]
				className = searchLines[i + 3]
				classUnits = searchLines[i + 4]
				classSched = searchLines[i + 6]
				classSched = classSched.lstrip()
				# print courseCode
				if not startFound and courseCode.find(endBody) != -1:
					break

				codeMatch = re.search(".*>(?P<course_code>.*)<.*", courseCode)
				classMatch = re.search(".*>(?P<class_name>.*)<.*", className)
				unitsMatch = re.search(".*>(?P<class_units>.*)<.*", classUnits)

				newClass["code"] = codeMatch.group("course_code")
				# newClass["class_name"] = classMatch.group("class_name")
				newClass["units"] = unitsMatch.group("class_units")
				newClass["schedule"] = {}
				daysDict = ["M", "T", "W", "Th", "F", "S"]
				for day in daysDict:
					newClass[day] = {}

				# print classSched
				schedMatch = re.search("(?P<class_sched>.*)<br.*", classSched)

				scheds = schedMatch.group("class_sched").split("; ")
				for sched in scheds:
					if sched.strip() == "TBA":
						for day in daysDict:
							schedDay = day
							newClass[schedDay]["time"] = schedParsed[1]
							newClass[schedDay]["type"] = schedParsed[2]
							newClass[schedDay]["bldg"] = schedParsed[3]
							newClass[schedDay]["room"] = schedParsed[4]
					else:
						schedParsed = sched.split(" ")
						schedDay = schedParsed[0]
						# print schedParsed
						if schedParsed[3] == "TBA":
							schedParsed.append("TBA")
						if len(schedParsed) == 4:
							schedParsed.append("TBA")

						for day in parseSchedDay(schedDay):
							newClass[day]["time"] = schedParsed[1]
							newClass[day]["type"] = schedParsed[2]
							newClass[day]["bldg"] = schedParsed[3]
							newClass[day]["room"] = schedParsed[4]


						# if schedDay == "TTh":
						# 	for day in ["T", "Th"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "WF":
						# 	for day in ["W", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MS":
						# 	for day in ["M", "S"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "TWThF":
						# 	for day in ["T", "W", "Th", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MTWThF":
						# 	for day in ["M", "T", "W", "Th", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MTWThTh":
						# 	for day in ["M", "T", "W", "Th", "Th"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MWF":
						# 	for day in ["M", "W", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MW":
						# 	for day in ["M", "W"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "TW":
						# 	for day in ["T", "W"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "TWF":
						# 	for day in ["T", "W", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "TWTh":
						# 	for day in ["T", "W", "Th"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MTh":
						# 	for day in ["M", "Th"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "WTh":
						# 	for day in ["M", "Th"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "ThS":
						# 	for day in ["Th", "S"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MF":
						# 	for day in ["M", "F"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# elif schedDay == "MMMMM":
						# 	for day in ["M"]:
						# 		newClass[day]["time"] = schedParsed[1]
						# 		newClass[day]["type"] = schedParsed[2]
						# 		newClass[day]["bldg"] = schedParsed[3]
						# 		newClass[day]["room"] = schedParsed[4]
						# else:
						# 	# print schedParsed
						# 	newClass[schedDay]["time"] = schedParsed[1]
						# 	newClass[schedDay]["type"] = schedParsed[2]
						# 	newClass[schedDay]["bldg"] = schedParsed[3]
						# 	newClass[schedDay]["room"] = schedParsed[4]
				# T 4:30-6:30PM lec Archi 1; Th 4:30-6:30PM lec Archi 104A <-- just split("; ")


				profIndex = 7
				profs = []
				profs.append(searchLines[i + profIndex])
				while searchLines[i + profIndex + 1].find("</td>") == -1:
					profIndex = profIndex + 1
					profs.append(searchLines[i + [profIndex]])

				profString = ""
				for prof in profs:
					for parsedProf in prof.split("; "):
						# print parsedProf.lstrip()
						profMatch = re.search("(?P<prof_name>.*)(<br.*)?", parsedProf.lstrip())
						profString = profString + profMatch.group("prof_name")
				newClass["instructor"] = profString 


				offeringUnit = searchLines[i + profIndex + 3] #Can be blank!
				checkDissolved = searchLines[i + profIndex + 4]
				# check first if dissolved!
				if checkDissolved.find("DISSOLVED") != -1:
					availableSlots = "DISSOLVED"
					totalSlots = "DISSOLVED"
					newClass["availableSlots"] = "DISSOLVED"
					newClass["totalSlots"] = "DISSOLVED"
					i = i + profIndex + 9
				else:
					availableSlots = searchLines[i + profIndex + 5]
					as_parsed = re.search(".*>(?P<available_slots>.*)<.*", availableSlots)
					totalSlots = searchLines[i + profIndex + 6].lstrip()
					ts_parsed = re.search("(?P<total_slots>\d*).*", totalSlots)
					newClass["totalSlots"] = ts_parsed.group("total_slots")
					newClass["availableSlots"] = as_parsed.group("available_slots")

					i = i + profIndex + 12
				classScheds[classMatch.group("class_name")] = newClass
				print "Added class %s" % (classMatch.group("class_name"))
				startFound = True
			elif startFound:
				if searchLines[i].find(blockEnd) != -1:
					break
				else:
					i = i + 1
			else:
				i = i + 1
		pickle.dump(classScheds, open("class_scheds.p", "wb"))

def sched_crawl():
	baseURL = "https://crs.upd.edu.ph/schedule/120152/"
	for letter in string.ascii_uppercase:
		indexURL = baseURL + letter
		fileName = "schedule_" + letter + ".txt"
		filePath = "Class Schedules/"
		netops.downloadPage(url=indexURL, fileName=fileName, filePath=filePath)
		print "Done with %s%s" % (filePath, fileName)

def exportSchedule():
	classScheds = pickle.load(open("class_scheds.p", "rb"))
	filename = "class_schedules.csv"
	csvfile = open(filename, "wb")
	csvwriter = csv.writer(csvfile, dialect='excel')

	row = ["", "", "", "Monday", "", "", "Tuesday", "", "Wednesday", "", "", "Thursday", "", "", "Friday", "", "", "Saturday"]
	csvwriter.writerow(row)
	row = ["Course", "Instructor", "Estimated Students", "Time", "Building", "Room", "Time", "Building", "Room", "Time", "Building", "Room", "Time", "Building", "Room", "Time", "Building", "Room", "Time", "Building", "Room"]
	for key in classScheds.keys():
		if classScheds[key]["availableSlots"] != "DISSOLVED":
			row = [key, classScheds[key]["instructor"]]

			# getting estimated students
			#if overbooked then total students ++
			if classScheds[key]["availableSlots"] == "OVERBOOKED":
				expectedAmt = classScheds[key]["totalSlots"] + "++"
			else:
				expectedAmt = (int)(classScheds[key]["totalSlots"]) - (int)(classScheds[key]["availableSlots"])
			row.append(expectedAmt)

			for day in ["M", "T", "W", "Th", "F", "S"]:
				if len(classScheds[key][day]) > 0:	#meaning there is class on that day
					row.append(classScheds[key][day]["time"])
					row.append(classScheds[key][day]["bldg"])
					row.append(classScheds[key][day]["room"])
				else:
					for i in range(0, 3):
						row.append("")
			csvwriter.writerow(row)
	csvfile.close()

