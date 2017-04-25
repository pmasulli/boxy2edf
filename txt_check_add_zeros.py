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
import glob

# logging configuration
# logging.basicConfig(filename='example.log', filemode='w', level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)

interactive_mode = False


def spacepad(string, n, paddingchar=" "):
    string = str(string)
    if len(string) > n:
        raise ValueError(string + ": The string is too long to be space padded as requested.")
    return string + paddingchar * (n - len(string))


# root_path = "/Volumes/Data1/data/nirs/2016_eeg_nirs"

add_zeros = False
sampling_rate = 512

if len(sys.argv) < 2:
    print "Interactive mode"
    interactive_mode = True
    file_orig = raw_input("Path to the file: ")
else:
    file_orig = sys.argv[1]


orig_fh = open(file_orig, 'r')

header_line = orig_fh.readline()

period = 1000.0 / sampling_rate

if add_zeros:
    add_zeros = 'y' == raw_input("add zeros? ")
    lines_to_add = input("Lines to add? ")
    dest_fh = open(file_orig.replace(".txt", "_with_zeros.txt"), 'w')
    dest_fh.write(header_line)

    line_of_zeros = orig_fh.readline()
    dest_fh.write(line_of_zeros)

    line_of_zeros = "\t".join(line_of_zeros.split("\t")[1:])

    i = 1

    print "Adding zeros..."
    for j in range(lines_to_add):
        time = period * i

        line_to_write = "%.4f\t%s" % (time, line_of_zeros)
        dest_fh.write(line_to_write)
        i += 1
    print "Wrote", i, "lines of zeros."

    for line in orig_fh:
        time = period * i
        line_orig = "\t".join(line.split("\t")[1:])
        line_to_write = "%.4f\t%s" % (time, line_orig)
        dest_fh.write(line_to_write)
        i += 1
        if i % 50000 == 0:
            print i, ". . ."


    orig_fh.close()
    dest_fh.close()
    print "Done adding zeros."

if add_zeros:
    file_to_check = file_orig.replace(".txt", "_with_zeros.txt")
else:
    file_to_check = file_orig

fh = open(file_to_check, 'r')

header_line = fh.readline()

trigger_index = header_line.split("\t").index("25")

print "The trigger index is", trigger_index
last_time = 0
line_count = 0
for line in fh:
    data = line.split("\t")
    time = float(data[0])
    trigger_voltage = float(data[trigger_index])
    if trigger_voltage > 0.5:
        print "Trigger at time\t%f\t%f" % (time, trigger_voltage)

    last_time = time
    line_count += 1

print "Num. lines = ", line_count
print "Last time in the file = ", last_time
print "Calculated time = ", (1000 * float(line_count) / sampling_rate)

