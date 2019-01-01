Mutatest diagnostic summary
===========================
Source location: /home/zassoc/Github/m/notebooks/simple_ifelse/ifelse
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
Clean trial 1 run time: 0:00:00.294269
Clean trial 2 run time: 0:00:00.303665
Mutation trials total run time: 0:00:00.612809

Overall mutation trial summary
==============================
SURVIVED: 2
TOTAL RUNS: 2
RUN DATETIME: 2019-01-01 17:19:32.634579


Mutations by result status
==========================


SURVIVED
--------
/home/zassoc/Github/m/notebooks/simple_ifelse/ifelse/run.py: (l: 5, c: 7) - mutation from <class '_ast.Eq'> to <class '_ast.LtE'>
/home/zassoc/Github/m/notebooks/simple_ifelse/ifelse/run.py: (l: 5, c: 8) - mutation from <class '_ast.Eq'> to <class '_ast.GtE'>