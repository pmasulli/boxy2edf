import numpy as np
#import matplotlib.pyplot as plt
import os
import math
import scipy.signal
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import logging
import sys
import glob


logging.basicConfig(level=logging.INFO)

interactive_mode = False


def compute_average_spectrum(filename):
    data = np.genfromtxt(filename, delimiter=' ')
    fh = []

    dt = 1/12.5

    freq_bins = 33
    spectra = np.zeros((data.shape[0],freq_bins))
    freqs = np.zeros((1, freq_bins))

    for segment_index in range(data.shape[0]):
        segment = data[segment_index]
        freqs = scipy.signal.welch(segment, fs=1/dt, nfft=64, nperseg=64, noverlap=0, detrend=lambda x: x)[0]
        spectra[segment_index,] = \
            10*np.log10(scipy.signal.welch(segment, fs=1/dt, nfft=64, nperseg=64, noverlap=0, detrend=lambda x: x)[1])

    avg_spectrum = np.mean(spectra, 0)
    sd_spectrum = np.std(spectra, 0)

    conf_spectrum_top = avg_spectrum + 1.96*sd_spectrum/np.sqrt(data.shape[0])
    conf_spectrum_bottom = avg_spectrum - 1.96*sd_spectrum/np.sqrt(data.shape[0])

    return freqs, avg_spectrum, conf_spectrum_bottom, conf_spectrum_top


def compute_median_mad(array, axis=0):
    median = np.median(array, axis=axis)
    mad = np.median(np.abs(array - median), axis=axis)
    return median, mad


def plot_spectrum(spectrum_data, label, color):
    freqs = spectrum_data[0]
    spectrum = spectrum_data[1]
    conf_spectrum_bottom = spectrum_data[2]
    conf_spectrum_top = spectrum_data[3]
    plt.plot(freqs, spectrum, label=label, color=color, ls='-', lw=1)
    plt.plot(freqs, conf_spectrum_bottom, color=color, ls='--', lw=1)
    plt.plot(freqs, conf_spectrum_top, color=color, ls='--', lw=1)


def ptp_amplitude(signals):
    return np.max(signals, axis=1) - np.min(signals, axis=1)

spectra_groups_to_compare = {
    '6_A': '%s_%s_6_A',
    '8_A': '%s_%s_6_A',
    '6_B': '%s_%s_6_A',
    '8_B': '%s_%s_6_A',
    '6_CD': '%s_%s_6_A',
    '8_CD': '%s_%s_6_A',
}


detector_groups = {
    '6_A': ['SLEEP-%s-A-DC2', 'SLEEP-%s-A-DC4', 'SLEEP-%s-A-DC10', 'SLEEP-%s-A-DC6', 'SLEEP-%s-A-DC15', 'SLEEP-%s-A-DC8'],
    '8_A': ['SLEEP-%s-A-DC1', 'SLEEP-%s-A-DC3', 'SLEEP-%s-A-DC9', 'SLEEP-%s-A-DC5', 'SLEEP-%s-A-DC16', 'SLEEP-%s-A-DC7'],
    '6_B': ['SLEEP-%s-B-DC1', 'SLEEP-%s-B-DC3', 'SLEEP-%s-B-DC16', 'SLEEP-%s-B-DC9', 'SLEEP-%s-B-DC11', 'SLEEP-%s-B-DC13'],
    '8_B': ['SLEEP-%s-B-DC2', 'SLEEP-%s-B-DC4', 'SLEEP-%s-B-DC15', 'SLEEP-%s-B-DC10', 'SLEEP-%s-B-DC12', 'SLEEP-%s-B-DC14'],
    '6_CD': ['SLEEP-%s-C-DC6', 'SLEEP-%s-C-DC1', 'SLEEP-%s-D-DC6', 'SLEEP-%s-D-DC1'],
    '8_CD': ['SLEEP-%s-C-DC5', 'SLEEP-%s-C-DC2', 'SLEEP-%s-D-DC5', 'SLEEP-%s-D-DC2']
}

colors = ['b', 'g', 'r', 'c', 'm']
colors2 = ['lightblue', 'lightgreen', 'lightcoral', 'aqua', 'thistle']

basepaths = glob.glob("/Users/paolo/neuroheuristic/research_projects/201610_NIRS_EEG/201611_6subjects/segments/6*")

if False:

    for basepath in sorted(basepaths): # for each subject
        for sleep_phase in ['S0', 'S1', 'S2', 'S3', 'REM']:
            for group_name in detector_groups.keys():
                subject_code = basepath.split("/")[-1]
                print (" Grouping data for %s, %s, %s " % (subject_code, sleep_phase, group_name)).center(80, "-")
                group_segments = {}
                segment_indices_outliers = set()
                for pair_name in detector_groups[group_name]:
                    pair_segments_file = os.path.join(basepath, "segments-" + pair_name % sleep_phase + ".txt")
                    if not os.path.isfile(pair_segments_file):
                        print "This phase is not present for this subject, skipping it (%s)." % (pair_name % sleep_phase)
                        pair_segments = None
                        break  # change it into break
                    print "Extracting the segments for the pair %s, (%s)" % ((pair_name % sleep_phase), pair_segments_file)
                    pair_segments = np.genfromtxt(pair_segments_file, delimiter=' ')
                    print "There are %d segments for this phase" % pair_segments.shape[0]
                    group_segments[pair_name] = pair_segments

                    print "Detecting outliers..."
                    variation = np.max(pair_segments, axis=1) - np.min(pair_segments, axis=1)
                    print variation
                    v = compute_median_mad(variation)
                    print v
                    print "There are", np.sum(variation >= 1.1*v[0] + 2 * v[1]), "outliers for the pair %s." % (pair_name % sleep_phase)
                    print list(np.where(variation >= 1.1*v[0] + 2 * v[1])[0])
                    segment_indices_outliers = segment_indices_outliers.union(set(list(np.where(variation >= 1.1*v[0] + 2 * v[1])[0])))
                    # break
                    # segment_indices_outliers.add(variation >= v[0] + 2 * v[1])
                    # signals = signals[variation < v[0] + 2 * v[1]]
                if pair_segments is None:
                    break
                print "For this group there are the following outlier indices to remove: %s" % ",".join([str(x) for x in segment_indices_outliers])
                print "In total %d outliers out of %d segments." % (len(segment_indices_outliers), pair_segments.shape[0])
                for pair_name in group_segments.keys():
                    group_segments[pair_name] = np.delete(group_segments[pair_name], list(segment_indices_outliers), axis=0)
                    print "%d segments remaining" % group_segments[pair_name].shape[0]

                # now that the outliers have been removed
                # normalize

                print " Normalization ".center(60, '-')
                max_ptp_amplitudes = []
                for pair_name in group_segments.keys():
                    max_ptp_amplitude = np.max(ptp_amplitude(group_segments[pair_name]))
                    max_ptp_amplitudes.append(max_ptp_amplitude)
                    print pair_name + "\t" + "\t".join(['%.2f' % x for x in ptp_amplitude(group_segments[pair_name])]) + \
                        "\t\t" + str(max_ptp_amplitude)
                print "After normalization by %.2f:" % max(max_ptp_amplitudes)
                for pair_name in group_segments.keys():
                    max_ptp_amplitude = np.max(ptp_amplitude(group_segments[pair_name]))
                    group_segments[pair_name] = group_segments[pair_name] * max(max_ptp_amplitudes) / max_ptp_amplitude
                    max_ptp_amplitude = np.max(ptp_amplitude(group_segments[pair_name]))
                    print pair_name + "\t" + "\t".join(['%.2f' % x for x in ptp_amplitude(group_segments[pair_name])]) + \
                        "\t\t" + str(max_ptp_amplitude)

                print "Averaging group (sum)"
                group_averaged_segments = np.zeros(group_segments[group_segments.keys()[0]].shape)
                for pair_name in group_segments.keys():
                    group_averaged_segments = group_averaged_segments + group_segments[pair_name]

                output_file = os.path.join(basepath, "../", "%s_%s_%s.txt" % (sleep_phase, subject_code, group_name))
                print "Saving result in: %s, shape = %s" % (output_file, str(group_averaged_segments.shape))
                np.savetxt(output_file, group_averaged_segments, fmt='%.3f')


print "Drawing spectra"

for basepath in sorted(basepaths): # for each subject
    subject_code = basepath.split("/")[-1]
    for location in spectra_groups_to_compare.keys():
        print "Drawing spectra for %s %s..." % (subject_code, location)

        plt.clf()
        i = 0
        for sleep_phase in ['S0', 'S1', 'S2', 'S3', 'REM']:
            group_segments_file = os.path.join(basepath, "../", "%s_%s_%s.txt" % (sleep_phase, subject_code, location))
            if not os.path.isfile(group_segments_file):
                print "File %s not present" % group_segments_file
                continue
            else:
                print "Found %s" % group_segments_file

            spectrum = compute_average_spectrum(group_segments_file)
            plot_spectrum(spectrum, sleep_phase, colors[i])
            i += 1

        plt.legend(loc='upper right')
        plt.title("Subj. %s - location+freq: %s" % (subject_code, location))
        plt.ylim((-10, 90))
        # plt.show()
        plot_file = os.path.join(basepath, "../", ("spectra_%s_%s" % (subject_code, location)) + ".pdf")
        plt.savefig(plot_file, format='pdf')
        print "Saved the plot in the file %s" % plot_file




