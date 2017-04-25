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

scoring_interval = 30.0

sleep_phases_numeric_codes = {
    "SLEEP-S0": 6,
    "SLEEP-REM": 5,
    "SLEEP-S1": 4,
    "SLEEP-S2": 3,
    "SLEEP-S3": 2,
}


if len(sys.argv) < 2:
    print "Interactive mode"
    interactive_mode = True
    root_path = raw_input("Path to the data directory: ")
else:
    root_path = sys.argv[1]


channels_to_extract_str = ""
try:
    with open(os.path.join(root_path, 'channels.txt')) as fh:
        channels_to_extract_str = fh.readline().rstrip("\r\n")
except IOError:
    print "Cannot find the channels.txt file."
    exit(-1)
channels_to_extract = channels_to_extract_str.split(",")


for basepath in sorted(glob.glob(os.path.join(root_path, "63432*"))):

    boxy_file = os.path.join(basepath, "NIRS/data.txt")
    if not os.path.isfile(boxy_file):
        raise ValueError("Boxy file not found: %s" % boxy_file)

    output_filename = boxy_file.replace(".txt", "") + "_with_hypnogram.txt"

    print (" Processing %s " % boxy_file).center(100, "-")

    # open the two files
    bf = open(boxy_file, 'r')
    output_fh = open(output_filename, 'wb')

    scoring_filename = os.path.join(basepath, "EEG/sleep_scoring.txt")

    time_delta = None
    try:
        with open(os.path.join(basepath, "time_delta.txt"), 'r') as time_delta_fh:
            time_delta = float(time_delta_fh.readline().rstrip("\r\n"))
        print "The time delta is %.2f" % time_delta
    except:
        print "Time delta file not found"
        try:
            time_delta = float(raw_input("Enter the time delta t_EEG - t_NIRS: "))
        except ValueError:
            print "Could not interpret the time delta value."
            exit(-1)




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
    skipped_columns = ["time", "group", "step", "mark", "flag", "aux-1", "aux-2", "aux-3", "aux-4"]



    # change here to select some signals only
    selected_fields = [field for field in channels_to_extract if field not in skipped_columns]
    selected_signals = {field: bf_data[field][:] for field in selected_fields}


    n_signals = len(selected_fields)
    data_time_duration = round(len(selected_signals[selected_fields[0]]) / b_update_rate)  # freq * n_points



    scoring_phases = []
    scoring_onsets = []
    found_phases = set()
    onset_times_by_phase = {}
    sleep_phase_signal = np.full(len(selected_signals[selected_fields[0]]), -100, dtype=np.int)

    with open(scoring_filename, 'r') as fh:
        i = 0
        old_end = None
        end_index = None
        for line in fh:
            phase = line.rstrip("\r\n")

            # (seconds) beginning time of the sleep phase - corrected for NIRS
            onset_time = scoring_interval * i - time_delta
            end_time = onset_time + scoring_interval
            onset_index = int(round(onset_time * b_update_rate))

            if end_index is not None:
                old_end = end_index

            end_index = onset_index + int(round(scoring_interval * b_update_rate))

            i += 1

            print "Phase %s from %.1f to %.1f (NIRS time, seconds) [%d %d]" % (phase, onset_time, end_time, onset_index, end_index)


            if old_end is not None and onset_index - old_end > 1:
                print "Warning! The previous phase ended at %d, the current starts at %d" % (old_end, onset_index)


            if onset_time < 0 and end_time > 0:
                print "This phase is partly contained in the NIRS recording (beginning)"
                onset_index = 0
            elif onset_index < len(selected_signals[selected_fields[0]]) and \
                            end_index > len(selected_signals[selected_fields[0]]):
                print "This phase is partly contained in the NIRS recording (end)"
                end_index = len(selected_signals[selected_fields[0]]) - 1
            elif end_time < 0 or onset_index >= len(selected_signals[selected_fields[0]]):
                print "This phase is completely out of the NIRS recording, skipping it"
                continue


            for index in range(onset_index, end_index):
                sleep_phase_signal[index] = sleep_phases_numeric_codes[phase]



    print "Writing the %d signals %s." % (n_signals, ",".join(selected_fields))

    output_fh.write(",".join(['hypnogram'] + selected_fields) + "\n")

    for line in range(len(selected_signals[selected_fields[0]])):
        datastring = '%d,' % sleep_phase_signal[line]
        for field in selected_fields:
            datastring += "%.3f," % selected_signals[field][line]
        output_fh.write(datastring[:-1] + "\n")

    print "Written %d lines" % line

    bf.close()
    output_fh.close()
    logging.info("Done writing the file %s. Success." % output_filename)
    print "".center(100, "-")

