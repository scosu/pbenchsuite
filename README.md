PBenchSuite
==========

Python Benchmark Suite to automatically benchmark linux systems and especially the linux kernel.

Features
========

* Automatic execution of multiple benchmark suites
* Adjustable number of runs per test instance, different options:
	* Min/Max runs
	* Relative min/max runs: Global modification of min/max runs without setting a fixed min/max runs for all tests (relative_min_runs * test.min_runs)
	* Min/Max runtime in seconds
	* Relative min/max runtime
	* relative_stderr: Define the maximal allowed standard error, depending on the average value of the test
* Automatic warmup runs to exclude measurements with cold caches
* Python monitor interface to record the system state while the benchmark is running
* Easy benchmark interface including requirement checking, installation, pre and post scripts
* JSON output files. Each of them holds all necessary information.
* Gathers system information (CPU, filesystems, modules, kernel, ...)
* Plot all data with a generic plotter
* Possibility to write own benchmarks, benchsuites, monitors and plotters

Usage
=====

This is an usage example for the scheduler benchsuite.

1. Clone this git repository
2. cd pbenchsuite/suite
3. Run './pbenchsuite.py scheduler:test\_run' . pbenchsuite will check for all requirements and print the missing ones. Fix that and try again. Before the first run starts it may take very long (20min) because it installs all benchmarks, generates files, downloads software and so on.
4. Wait for the pbenchsuite to complete. (Depending on the min/max\_runs and so on from the benchsuites/scheduler file, this may take several days)
5. Call './plot.py charts results/test\_run'. This will take a lot of time (possibly several hours) and memory. You only have the results from one testsetup, so change your testsetup and run it with a different runname (test\_run2). Copy the produced data to results and start the plotter with both pathes. You will get much more interesting charts.
6. Now you have more than 4000 charts about results and system state while running the tests.

Contribution
============

If you have any new plotters/benchmarks/benchsuites or feedback, please contact me or create merge requests.
