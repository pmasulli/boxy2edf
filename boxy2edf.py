#!/usr/bin/pyhon
#
# boxy2edf v0.2
# Copyright 2016 Paolo Masulli - Neuroheuristic Research Group
#
#
# This file is part of boxy2edf.
#
# boxy2edf is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with boxy2edf.  If not, see <http://www.gnu.org/licenses/>.


import struct
import os.path
import sys
import datetime
import logging
import numpy as np

# logging configuration
# logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

interactive_mode = False

if len(sys.argv) < 2:
    print "Interactive mode"
    interactive_mode = True
    boxy_file = raw_input("Path to the boxy file: ")
else:
    boxy_file = sys.argv[1]

if not os.path.isfile(boxy_file):
    raise ValueError("Boxy file not found: %s" % boxy_file)


edf_file = boxy_file.replace(".txt", "")+".edf"

# the boxy signals are decimals. I multiply for the multiply and then round to int
multiplier = 1
digital_min = -100000
digital_max = 100000


EEG_EVENT_CHANNEL = 'EDF Annotations'

# each event data is coded as 20 2-byte "integers" i.e. 40 bytes available -- each TAL has this length
eeg_event_length = 20

BOXY_EVENT_CHANNEL = 'digaux'


def spacepad(string, n, paddingchar=" "):
    string = str(string)
    if len(string) > n:
        raise ValueError(string + ": The string is too long to be space padded as requested.")
    return string + paddingchar * (n - len(string))


# open the two files
bf = open(boxy_file, 'r')
ef = open(edf_file, 'wb')


# read the Boxy file

data_begins_line = data_ends_line = 0
b_update_rate = 0.0
bf_fields = []
bf_data = {}  # each element is a signal/channel, a list of data points

i = 0
for line in bf:
    if '#DATA BEGINS' in line:
        data_begins_line = i
    if '#DATA ENDS' in line:
        data_ends_line = i

    if "Update Rate (Hz)" in line:
        b_update_rate = float(line.split(" ")[0])

    if data_begins_line != 0:
        # if data has begun

        if i == data_begins_line + 1:
            # the field names line
            bf_fields = line.rstrip().split("\t")
            for (field_id, field) in enumerate(bf_fields):
                bf_data[field] = []
            logging.info("There are %d fields" % len(bf_fields))

        if data_ends_line == 0 and i > data_begins_line + 2:
            # if we are in a data line
            data_line = line.rstrip().split("\t")
            # logging.info("There are %d data columns" % len(bf_data[-1]))
            if len(data_line) != len(bf_fields):
                raise ValueError(("We have a problem! There are %d fields, but line %d " +
                                 "in the boxy file has %d points.") % (len(bf_fields), i, len(data_line)))
            for (field_id, v) in enumerate(data_line):
                bf_data[bf_fields[field_id]].append(np.round(float(v), 3))
                # bf_data[bf_fields[field_id]].append(float(v))
    i += 1

print "Data read in the Boxy file".center(100, "-")
print "Data begins at line", data_begins_line, "and ends at", data_ends_line
print "There are", len(bf_data), "columns."
print "Fields:", bf_fields
print "Update rate:", b_update_rate

# columns to skip
skipped_columns = {"time", "group", "step", "mark", "flag", "aux-1", "aux-2", "aux-3", "aux-4", BOXY_EVENT_CHANNEL}

events = []
events_present = 0
event_begun = False  # paolo: to separate events -- each event happens at ONE specific time, not several contiguous
for (t, x) in enumerate(bf_data[BOXY_EVENT_CHANNEL]):
    if x != 0.0 and not event_begun:
        events.append((t, x))
        event_begun = not event_begun

    if x == 0.0 and event_begun:
        event_begun = not event_begun

print "Events (time, code):", events

if len(events) != 0:
    events_present = 1

for f in bf_data.keys():
    if max(bf_data[f]) - min(bf_data[f]) == 0:
        logging.warning("%s almost constant" % f)
        # skipped_columns.add(f)
    else:
        logging.info("Channel %s\t%f\t%f" % (f, min(bf_data[f]), max(bf_data[f])))


skipped_columns = list(skipped_columns)


# change here to select some signals only
selected_fields = [field for field in bf_fields if field not in skipped_columns]
selected_signals = {field: bf_data[field][:] for field in selected_fields}


n_signals = len(selected_fields)
data_time_duration = round(len(selected_signals[selected_fields[0]]) / b_update_rate)  # freq * n_points

physical_minimum = {}
physical_maximum = {}

print "Scaling and centering".center(100, "-")

for s in selected_fields:
    # for each signal

    # centering around 0
    logging.info("Channel %s" % s)

    # save physical min and max
    physical_minimum[s] = min(selected_signals[s])
    physical_maximum[s] = max(selected_signals[s])

    mean = sum(selected_signals[s]) / len(selected_signals[s])

    logging.info("Average = %f --- centering the values." % mean)

    i = 0
    while i < len(selected_signals[s]):
        selected_signals[s][i] -= mean
        i += 1
    logging.info("After centering:\t%f\t%f" % (min(selected_signals[s]), max(selected_signals[s])))

    abs_max = max(abs(min(selected_signals[s])), abs(max(selected_signals[s])))
    logging.info("Abs max = %f -- now scaling" % abs_max)

    scaling_factor = 32767.0/abs_max  # the scaling factor to be in the range -32k to 32k

    logging.info("The scaling factor is: %f" % scaling_factor)
    i = 0
    while i < len(selected_signals[s]):
        selected_signals[s][i] = int(round(scaling_factor * selected_signals[s][i]))
        i += 1
    logging.info("After scaling:\t\t%d\t%d" % (min(selected_signals[s]), max(selected_signals[s])))

# ###

print "".center(100, "=")
print "Data to write in the EDF file".center(100, "-")
print "Fields:", selected_fields
print "Writing", len(selected_fields), "fields."
print "Number of data points:", len(selected_signals[selected_fields[0]])
print "Approximate data recording duration: %s" % \
      str(datetime.timedelta(seconds=len(selected_signals[selected_fields[0]]) / b_update_rate))
print "".center(100, "=")

if interactive_mode:
    raw_input("Press Enter to continue...")

date = "01-JAN-2015"
patient_code = "P001"  # local code
patient_sex = "F"  # M/F/X
patient_birthdate = "01-MAR-1951"  # DD-MMM-YYYY
patient_name = "fNIRS_Patient"  # replace spaces w underscores

recording_startdate_short = "01.01.15"  # DD.MM.YY
recording_startdate_long = "01-JAN-2015"  # DD-MMM-YYYY
recording_starttime = "10.00.00"  # HH.MM.SS
investigation_code = "NIRS_001"
responsible_investigator_code = "AV"
equipment_code = "NHRG_IMAGENT"

transducer_type = "NIRS Optode"  # always this constant value, since it's data from Boxy
physical_dimension = "A"  # to be checked...
prefiltering_text = "None"


local_patient_ident = " ".join([patient_code, patient_sex, patient_birthdate, patient_name])
local_recording_ident = " ".join(["Startdate", recording_startdate_long, investigation_code,
                                  responsible_investigator_code, equipment_code])


header = dict()

# 8 ascii : version of this data format (0)
header[0] = spacepad("0", 8)

# 80 ascii : local patient identification (mind item 3 of the additional EDF+ specs)
header[1] = spacepad(local_patient_ident, 80)

# 80 ascii : local recording identification (mind item 4 of the additional EDF+ specs)
header[2] = spacepad(local_recording_ident, 80)

# 8 ascii : startdate of recording (dd.mm.yy) (mind item 2 of the additional EDF+ specs)
header[3] = recording_startdate_short

# 8 ascii : starttime of recording (hh.mm.ss)
header[4] = recording_starttime

# 8 ascii : number of bytes in header record
header[5] = spacepad(str(256 * (n_signals + 1 + events_present)), 8)

# 44 ascii : reserved
header[6] = spacepad("EDF+C", 44)

# 8 ascii : number of data records (-1 if unknown, obey item 10 of the additional EDF+ specs)
header[7] = spacepad("1", 8)

# 8 ascii : duration of a data record, in seconds
header[8] = spacepad(str(int(data_time_duration)), 8)

# 4 ascii : number of signals (ns) in data record
header[9] = spacepad(str(n_signals + events_present), 4)

# ns * 16 ascii : ns * label (e.g. EEG Fpz-Cz or Body temp) (mind item 9 of the additional EDF+ specs)
header[10] = ""
for field in selected_fields:
    header[10] += spacepad(field, 16)
if events_present:
    header[10] += spacepad(EEG_EVENT_CHANNEL, 16)

# ns * 80 ascii : ns * transducer type (e.g. AgAgCl electrode)
header[11] = ""
for field in selected_fields:
    header[11] += spacepad(transducer_type, 80)
if events_present:
    header[11] += spacepad(EEG_EVENT_CHANNEL, 80)

# ns * 8 ascii : ns * physical dimension (e.g. uV or degreeC)
header[12] = ""
for field in selected_fields:
    header[12] += spacepad(physical_dimension, 8)
if events_present:
    header[12] += spacepad("", 8)

# ns * 8 ascii : ns * physical minimum (e.g. -500 or 34)
header[13] = ""
for field in selected_fields:
    header[13] += spacepad(physical_minimum[field], 8)
if events_present:
    header[13] += spacepad("-1", 8)

# ns * 8 ascii : ns * physical maximum (e.g. 500 or 40)
header[14] = ""
for field in selected_fields:
    header[14] += spacepad(physical_maximum[field], 8)
if events_present:
    header[14] += spacepad("1", 8)

# ns * 8 ascii : ns * digital minimum (e.g. -2048)
header[15] = ""
for field in selected_fields:
    header[15] += spacepad(min(selected_signals[field]), 8)
if events_present:
    header[15] += spacepad("-32768", 8)

# ns * 8 ascii : ns * digital maximum (e.g. 2047)
header[16] = ""
for field in selected_fields:
    header[16] += spacepad(max(selected_signals[field]), 8)
if events_present:
    header[16] += spacepad("32767", 8)

# ns * 80 ascii : ns * prefiltering (e.g. HP:0.1Hz LP:75Hz)
header[17] = ""
for field in selected_fields:
    header[17] += spacepad(prefiltering_text, 80)
if events_present:
    header[17] += spacepad("", 80)


# ns * 8 ascii : ns * nr of samples in each data record
header[18] = ""
for field in selected_fields:
    header[18] += spacepad(str(len(selected_signals[field])), 8)
if events_present:
    header[18] += spacepad(len(events) * eeg_event_length, 8)


# ns * 32 ascii : ns * reserved
header[19] = ""
for field in selected_fields:
    header[19] += spacepad("Reserved for " + field + " signal", 32)
if events_present:
    header[19] += spacepad("", 32)


header_string = ""
for i in header.keys():
    header_string += header[i]

logging.debug(header_string)
logging.info("Header length = %d" % len(header_string))


print "Writing in the file", edf_file
# write the header string
ef.write(header_string)


for s in selected_fields:
    # for each signal
    datastring = ''
    for v in selected_signals[s]:
        try:
            datastring += struct.pack("<h", v)
        except struct.error:
            logging.warning("Ooops tried to pack a number that was too big: %f" % v)
    ef.write(datastring)
    logging.info("Wrote signal %s" % s)

if events_present:
    # write the event channel
    logging.info("Writing the event channel...")
    eventstring = ''
    eventstring += spacepad('+0\x14\x14Recording starts\x14\x00', 2 * eeg_event_length, '\x00')

    for (t, x) in events:
        time = round(t / b_update_rate, 3)  # ?????
        event = spacepad("+"+str(time)+"\x14"+str(x)+"\x14\x00", 2 * eeg_event_length, '\x00')
        eventstring += event
    ef.write(eventstring)

bf.close()
ef.close()
logging.info("Done writing the file %s. Success." % edf_file)
