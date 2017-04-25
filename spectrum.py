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

    # if write_segments_to_file:
    #     for channel in range(data.shape[0]):
    #         fh.append(open(filename.split(".")[0]+"_"+str(channel + 1)+"_segments.txt", 'w'))

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


def plot_spectrum(spectrum_data, label, color):
    freqs = spectrum_data[0]
    spectrum = spectrum_data[1]
    conf_spectrum_bottom = spectrum_data[2]
    conf_spectrum_top = spectrum_data[3]
    plt.plot(freqs, spectrum, label=label, color=color, ls='-', lw=1)
    plt.plot(freqs, conf_spectrum_bottom, color=color, ls='--', lw=1)
    plt.plot(freqs, conf_spectrum_top, color=color, ls='--', lw=1)

segment_groups_to_compare = {
    'B9-690': ['SLEEP-S0-B-DC9','SLEEP-S1-B-DC9','SLEEP-S2-B-DC9','SLEEP-S3-B-DC9','SLEEP-REM-B-DC9'],
    'B10-830': ['SLEEP-S0-B-DC10','SLEEP-S1-B-DC10','SLEEP-S2-B-DC10','SLEEP-S3-B-DC10','SLEEP-REM-B-DC10'],
    'B1-690': ['SLEEP-S0-B-DC1','SLEEP-S1-B-DC1','SLEEP-S2-B-DC1','SLEEP-S3-B-DC1','SLEEP-REM-B-DC1'],
    'B2-830': ['SLEEP-S0-B-DC2', 'SLEEP-S1-B-DC2', 'SLEEP-S2-B-DC2', 'SLEEP-S3-B-DC2', 'SLEEP-REM-B-DC2'],
    'A5-830': ['SLEEP-S0-A-DC5', 'SLEEP-S1-A-DC5', 'SLEEP-S2-A-DC5', 'SLEEP-S3-A-DC5', 'SLEEP-REM-A-DC5'],
    'A6-690': ['SLEEP-S0-A-DC6', 'SLEEP-S1-A-DC6', 'SLEEP-S2-A-DC6', 'SLEEP-S3-A-DC6', 'SLEEP-REM-A-DC6'],
    'A1-830': ['SLEEP-S0-A-DC1', 'SLEEP-S1-A-DC1', 'SLEEP-S2-A-DC1', 'SLEEP-S3-A-DC1', 'SLEEP-REM-A-DC1'],
    'A2-690': ['SLEEP-S0-A-DC2', 'SLEEP-S1-A-DC2', 'SLEEP-S2-A-DC2', 'SLEEP-S3-A-DC2', 'SLEEP-REM-A-DC2'],
}


colors = ['b', 'g', 'r', 'c', 'm']
colors2 = ['lightblue', 'lightgreen', 'lightcoral', 'aqua', 'thistle']

basepaths = glob.glob("/Users/paolo/neuroheuristic/research_projects/201610_NIRS_EEG/201611_6subjects/segments/6*")

# basepath = "/Volumes/Data1/data/nirs/2016_eeg_nirs/62872/NIRS/"

for basepath in basepaths:
    print (" Plotting spectra for %s " % basepath.split("/")[-1]).center(80, "-")
    for (group_comparison_name, group_elements) in segment_groups_to_compare.iteritems():
        print "Making plot for group comparison %s" % group_comparison_name
        plt.clf()
        i = 0
        for group in group_elements:
            if not os.path.isfile(os.path.join(basepath, 'segments-%s.txt' % group)):
                logging.info("Group %s not present" % group)
                continue
            print "Computing spectrum for group %s" % group
            spectrum = compute_average_spectrum(os.path.join(basepath, 'segments-%s.txt' % group))
            plot_spectrum(spectrum, group, colors[i])
            i += 1
        plt.legend(loc='upper right')
        plt.title(basepath.split("/")[-1] + " " + group_comparison_name)
        plt.ylim((-10, 90))
        # plt.show()
        plot_file = os.path.join(basepath, basepath.split("/")[-1] + "_" + group_comparison_name + ".pdf")
        plt.savefig(plot_file, format='pdf')
        logging.info("Saved the plot in the file %s" % plot_file)




