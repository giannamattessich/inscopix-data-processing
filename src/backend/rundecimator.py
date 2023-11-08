import csv
from datetime import datetime
import pytz

#input file with interleaved runs
inscopixEventsFileUtc = 'day_1-longitudinal_spikes.csv'

#Full prefix for the output files (include path if you don't want them in the project directory)
#leaving this blank will output to current directory
outputPrefix = 'day_1-longitudinal_spikes-aligned-unix'

#Array of behavioral timestamp files denoting each run
behavioralTimestampFilesUtc = ['20230804_kombucha_session1_LOF.csv',
				'20230804_kombucha_session2_tape.csv',
				'20230804_kombucha_session3_LOF.csv']
                         
# UTC time difference
# This manual offset isn't used anymore and is instead gathered from datetime objects
utcOffset = 4.0*60.0*60.0*1000.0  # offset between two files in mSec (4h * 60 m/h * 60 s/m * 1000 ms/s)
utcScale = 1000.0  # scale from inscopix timestamp (in seconds) to behavioral timestamp (in mSec)

######################################################
# DO NOT MODIFY BELOW THIS LINE
######################################################
class Run:
    startTime = 0.0
    endTime = 0.0
    filePrefix = ""
    def __init__(self, startTime, endTime, filePrefix):
        self.startTime = startTime
        self.endTime = endTime
        self.filePrefix = filePrefix

# determine timezone offset
with open(inscopixEventsFileUtc, 'r') as timeseries:
    timeCsv = csv.reader(timeseries)
    for headerRow in timeCsv:
        # discard header
        break

    # Inscopix has correct timestamps, but Camera is set Boston time, but with no UTC offset
    # To correct, we adjust the camera times by the UTC offset of Boston

    # check first timestamp of inscopix events for UTC offset
    for row in timeCsv:
        timestamp = float(row[0])
        dateTime = datetime.fromtimestamp(timestamp, pytz.timezone('America/New_York'))
        utcOffset = 0.0 - ((dateTime.utcoffset().days*24.0*60.0*60.0 + dateTime.utcoffset().seconds) * 1000.0 \
                    + dateTime.utcoffset().microseconds / 1000.0)
        break

    # check last timestamp of inscopix file
    for row in timeCsv:
        pass
    timestamp = float(row[0])
    dateTime = datetime.fromtimestamp(timestamp, pytz.timezone('America/New_York'))
    endUtcOffset = 0.0 - ((dateTime.utcoffset().days * 24.0 * 60.0 * 60.0 + dateTime.utcoffset().seconds) * 1000.0 \
                       + dateTime.utcoffset().microseconds / 1000.0)

    # make sure the offset is the same throughout the file, no DST trickery
    if endUtcOffset != utcOffset:
        print("==================== WARNING! =========================")
        print("UTC offset differs between start and end of Inscopix Events file! \
         Possibly due to crossing Daylight Savings")
        exit(1)

# Get run start and end times from the various behavioral files
runStartTimes = []
for behavioralFile in behavioralTimestampFilesUtc:
    with open(behavioralFile, 'r') as file:
        startTime = float(file.readline())
        for line in file:
            pass
        endTime = float(line)
        runStartTimes.append(Run(startTime, endTime, behavioralFile.split('.')[0]))
# sort runs so lowest start time is first
def sortRunStarts(e):
    return e.startTime
runStartTimes.sort(key=sortRunStarts)

if (len(runStartTimes) < 1):
    print("Must have at least 1 run start time")
    exit(1)

#Gather the data
runs = []
with open(inscopixEventsFileUtc, 'r') as timeseries:
    timeCsv = csv.reader(timeseries)
    # read the first row of the CSV and setup our runs array
    for headerRow in timeCsv:
        for i in range(0, len(runStartTimes)):
            runs.append([headerRow])
        # stop after first row
        break

    # Loop through data now that first row is already read
    for row in timeCsv:
        # Loop through our start times to determine which run it is in
        for i in range(0, len(runStartTimes)):
            time = float(row[0])*utcScale + utcOffset
            # time < current run start must not be in this run
            if time < runStartTimes[i].startTime:
                continue
            # time > current run end must not be in this run
            if time > runStartTimes[i].endTime:
                continue
            # if we made it here, then this is the correct run
            # remove the start time offset from the event time
            row[0] = str((time - runStartTimes[i].startTime)/utcScale)  # remove offset and scale back to seconds
            # append the data to the run
            runs[i].append(row)
            break

# create output csv
for i in range(0, len(runs)):
    # generate the output file name based on run number
    newFileName = outputPrefix + '_run' + str(i+1) + '.csv'
    with open(newFileName, 'w', newline='') as outputFile:
        outputCsv = csv.writer(outputFile)
        # loop through all of the rows of the current run and write it to the new output file
        for row in runs[i]:
            outputCsv.writerow(row)
