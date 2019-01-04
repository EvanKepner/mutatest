Mutatest diagnostic summary
===========================
 - Source location: /home/zassoc/Github/m/notebooks/simple_ifelse/ifelse
 - Test commands: ['pytest']
 - Mode: sd
 - Excluded files: ['__init__.py']
 - N locations input: 10
 - Random seed: None

Random sample details
---------------------
 - Total locations mutated: 1
 - Total locations identified: 1
 - Location sample coverage: 100.00 %


Running time details
--------------------
 - Clean trial 1 run time: 0:00:00.305396
 - Clean trial 2 run time: 0:00:00.301328
 - Mutation trials total run time: 0:00:00.294219

Overall mutation trial summary
==============================
 - SURVIVED: 1
 - TOTAL RUNS: 1
 - RUN DATETIME: 2019-01-03 18:58:56.058395


Mutations by result status
==========================


SURVIVED
--------
 - /home/zassoc/Github/m/notebooks/simple_ifelse/ifelse/run.py: (l: 5, c: 11) - mutation from <class '_ast.Eq'> to <class '_ast.LtE'>