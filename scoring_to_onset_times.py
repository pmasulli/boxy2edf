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


# import struct
import os.path
import sys
# import datetime
import logging
# import eegtools


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
    scoring_file = raw_input("Path to the scoring file: ")
else:
    scoring_file = sys.argv[1]

if not os.path.isfile(scoring_file):
    raise ValueError("Scoring file not found: %s" % scoring_file)


directory = os.path.split(scoring_file)[0]

scoring_interval = float(raw_input_default("Enter the length of the scoring interval", '30'))

time_delta = 0
try:
    time_delta = float(raw_input("Enter the time delta t_EEG - t_NIRS: "))
except ValueError:
    print "Could not interpret the time delta value."

scoring_phases = []
scoring_onsets = []
found_phases = set()
onset_times_by_phase = {}


with open(scoring_file, 'r') as fh:
    i = 0
    for line in fh:
        phase = line.rstrip("\r\n")
        onset_time = scoring_interval * i - time_delta
        scoring_phases.append(phase)
        found_phases.add(phase)
        scoring_onsets.append(onset_time)

        if phase in onset_times_by_phase.keys():
            onset_times_by_phase[phase].append(onset_time)
        else:
            onset_times_by_phase[phase] = [onset_time]
        i += 1

print "The following phases have been found: %s" % ', '.join(list(found_phases))

with open(os.path.join(directory, "onset_times.txt"), 'w') as fh:
    for (phase, onset_times) in onset_times_by_phase.iteritems():
        print "%s\t%s" % (phase, ','.join('%.1f' % x for x in onset_times))
        fh.write("%s\t%s\n" % (phase, ','.join('%.1f' % x for x in onset_times)))
