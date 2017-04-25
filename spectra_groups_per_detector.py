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

# if len(sys.argv) < 2:
#     print "Interactive mode"
#     interactive_mode = True
#     edf_file = raw_input("Pattern of the segment files to be analysed: ")
# else:
#     edf_file = sys.argv[1]

# if not os.path.isfile(edf_file):
#     raise ValueError("EDF file not found: %s" % edf_file)


def compute_average_spectrum(filename):
    #filename = 's0.txt'
    data = np.genfromtxt(filename, delimiter=' ')
    fh = []

    dt = 1/12.5
    # t = np.arange(0, 7116*dt, dt)
    #nse = np.random.randn(len(t))
    #nse = data[1,]
    #r = np.exp(-t/0.05)
    #cnse = np.convolve(nse, r)*dt
    #cnse = cnse[:len(t)]
    #s = 0.1*np.sin(2*np.pi*t) + cnse

    freq_bins = 33
    spectra = np.zeros((data.shape[0],freq_bins))
    freqs = np.zeros((1, freq_bins))

    # if write_segments_to_file:
    #     for channel in range(data.shape[0]):
    #         fh.append(open(filename.split(".")[0]+"_"+str(channel + 1)+"_segments.txt", 'w'))

    for segment_index in range(data.shape[0]):
        segment = data[segment_index]
        #print segment.tostring()
        #a = plt.psd(segment, 32, 1/dt)
        #print 10*np.log10(scipy.signal.welch(segment, fs=1/dt, nfft=32, nperseg=32, noverlap=0, detrend=lambda x:x)[1])
        #spectra[i,] = 10*np.log10(a[0])
        #print spectra[i,]
        #print "---"
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



#
# s_s0 = compute_average_spectrum("/Volumes/Data1/data/nirs/2016_eeg_nirs/62872/NIRS/segments-SLEEP-S1-A-DC5.txt")
# # s_s1 = compute_spectrum('s1.txt', True)
#
# freqs = s_s0[0]
#
# spectrum_s0 = s_s0[1]
# conf_spectrum_bottom_s0 = s_s0[2]
# conf_spectrum_top_s0 = s_s0[3]
#
#
#
#
# plt.clf()
#
# plot_spectrum(s_s0, 'SLEEP-S1-A-DC5', colors[0])
#

# plt.plot(freqs, spectrum_s1[channel,], label="S1", color=colors2[channel], ls='-', lw=1)
# plt.plot(freqs, conf_spectrum_bottom_s1[channel,], color=colors2[channel], ls='--', lw=1)
# plt.plot(freqs, conf_spectrum_top_s1[channel,], color=colors2[channel], ls='--', lw=1)
#
#
# plt.legend(loc='upper right')
# # plt.title("Ch. "+str(0+1))
# plt.ylim((-10,90))
# #plt.show()
# plt.savefig("ch_%d.pdf" % 0, format='pdf')



#plt.subplot(212)
#plt.psd(s, 32, 1/dt)


#plt.plot(freqs, avg_spectrum, label="Ch. "+str(channel+1))
#plt.legend(loc='upper right')
#plt.title(filename.split(".")[0])
#plt.ylim((-10,90))
#plt.show()



