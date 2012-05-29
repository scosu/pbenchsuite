#!/usr/bin/python2

import data_loader
import plot_utils
import matplotlib.pyplot as plt




##
# @brief This function is called from the plot script, so for a own plotter you
# have to implement this
#
# @param pathes List of pathes you should use for plotting
# @param storedir Path to the direcory the results have to be stored, you are
# free to create subdirs there.
def plot_pathes(pathes, storedir):
	# For easy data loading, you could use the data_loader utilities
	loader = data_loader.loader()
	# You really should reduce the benchmarks loaded by defining only_benchs
	# which will cause the loader to load only xyz data
	loader.load_pathes(pathes, only_benchs=['xyz'])
	data = loader.get_data()
	# Also have a look to get_filtered_data for data filtered by arguments/monitors

	# Somehow reformat data to be able to plot it
	# You can use plot_utils to plot to mathplotlib
	# The following call will not succeed because the data is not correctly
	# formated for plot_bar_chart. See plot_utils.py for information about
	# the format
	# Alternative: plot_line_chart(data)
	plot_utils.plot_bar_chart(data)
	# After this call the plot can be found in matplotlib's main plot
	plt.show()
