PBenchSuite
==========

Python Benchmark Suite to automatically benchmark linux systems.

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
