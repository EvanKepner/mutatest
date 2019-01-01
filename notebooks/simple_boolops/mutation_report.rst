Mutatest diagnostic summary
===========================
Source location: /home/zassoc/Github/m/notebooks/simple_boolops/andor
Test commands: ['pytest']
Mode: sd
Excluded files: ['__init__.py']
N locations input: 10
Random seed: None

Random sample details
---------------------
Total locations mutated: 2
Total locations identified: 2
Location sample coverage: 100.00 %


Running time details
--------------------
Clean trial 1 run time: 0:00:00.302568
Clean trial 2 run time: 0:00:00.304157
Mutation trials total run time: 0:00:00.610900

Overall mutation trial summary
==============================
SURVIVED: 2
TOTAL RUNS: 2
RUN DATETIME: 2019-01-01 17:51:11.776091


Mutations by result status
==========================


SURVIVED
--------
/home/zassoc/Github/m/notebooks/simple_boolops/andor/run.py: (l: 5, c: 11) - mutation from <class '_ast.And'> to <class '_ast.Or'>
/home/zassoc/Github/m/notebooks/simple_boolops/andor/run.py: (l: 8, c: 11) - mutation from <class '_ast.LShift'> to <class '_ast.RShift'>