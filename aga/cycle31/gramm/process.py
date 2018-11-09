import csv
import subprocess
import sys
import os
import matplotlib.pyplot as plt
import signal
import time

line = ['java'] + ['Benchmark'] + [str(nb)] + [str(64000)] + [str(4)] # command-line launching
print(line)
result = subprocess.check_output(line, universal_newlines=True)

