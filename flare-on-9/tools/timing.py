# Python version compatibility module for timing
# defines generic 'clock' symbol in both this module and time

import time

if hasattr(time, 'perf_counter'):
	clock = time.perf_counter
elif hasattr(time, 'clock'):
	clock = time.clock
else:
	clock = time.time

setattr(time, 'clock', clock)

