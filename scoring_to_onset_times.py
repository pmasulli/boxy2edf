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
import eegtools


def raw_input_default(prompt, default=''):
    ri = raw_input("%s [%s]: " % (prompt, default))
    if not ri:
        return default
    else:
        return ri

# logging configuration
# logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

interactive_mode = False

if len(sys.argv) < 2:
    print "Interactive mode"
    interactive_mode = True
    edf_file = raw_input("Path to the EDF file: ")
else:
    edf_file = sys.argv[1]

if not os.path.isfile(edf_file):
    raise ValueError("EDF file not found: %s" % edf_file)


edf_directory = os.path.split(edf_file)[0]

edf = eegtools.io.edfplus.load_edf(edf_file)

print "Read an EDF file containing %d channels each with %d data points." % (edf.X.shape[0], edf.X.shape[1])
print "The sampling rate is %f, so the file is approximately %s." % \
      (edf.sample_rate, str(datetime.timedelta(seconds=edf.X.shape[1] / edf.sample_rate)))

sampling_rate = edf.sample_rate

print "This script can extract segments of EDF files."
segment_onset_times_str = raw_input("1) Enter the segment start times (in seconds, comma separated): ")

try:
    segment_onset_times = [float(x) for x in segment_onset_times_str.split(",")]
except:
    print "Could not understand the format of segment onset times."

segment_durations_str = raw_input("2) Enter the length of the segments (in seconds) -- either a single value " +
                                  "or a comma-separated list with the same length of the previous one: ")

try:
    segment_durations = [float (x) for x in segment_durations_str.split(",")]
except:
    print "Could not decode the segment lengths."

if len(segment_durations) == 1:
    segment_durations *= len(segment_onset_times)
elif len(segment_durations) != len(segment_onset_times):
    raise ValueError("Please enter either one value for the duration, or the duration of each segment.")


print "3) This EDF file contains the following channels: "
print "\t" + ",".join(edf.chan_lab)


channels_to_extract_str = raw_input("Enter the sub-list of channels to extract, or nothing to extract them all: ")

if not channels_to_extract_str:
    channels_to_extract = edf.chan_lab
else:
    channels_to_extract = channels_to_extract_str.split(',')
    for channel in channels_to_extract:
        if channel not in edf.chan_lab:
            raise ValueError("The channel %s was not recognized." % channel)

print " Ready to extract and save the segments ".center(80, "-")
print "Creating the files -- one per channel"
fhs = {}
for channel in channels_to_extract:
    fhs[channel] = open(os.path.join(edf_directory, "segments-%s.txt" % channel), 'w')

for (segment_index, onset_time) in enumerate(segment_onset_times):
    print (" Segment %d with onset time %f " % (segment_index + 1, onset_time)).center(80, "-")
    time_index_start = onset_time * sampling_rate
    time_index_end = (onset_time + segment_durations[segment_index]) * sampling_rate
    if time_index_end >= edf.X.shape[1]:
        raise ValueError("Cannot extract the segment because it goes outside the recording.")
    print "This segment is %f seconds, i.e. %d points, from %d to %d." % (segment_durations[segment_index],
                                                                          time_index_end - time_index_start,
                                                                          time_index_start, time_index_end)

    print "Writing the segment for the channels:",
    for channel in channels_to_extract:
        fhs[channel].write(
            " ".join("%.2f" % x for x in edf.X[edf.chan_lab.index(channel), time_index_start:time_index_end]) + "\n")
        print channel,
    print

print "Closing the files"
for channel in fhs.keys():
    fhs[channel].close()


