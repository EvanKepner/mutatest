Mutatest diagnostic summary
===========================
 - Source location: /home/zassoc/Github/m/notebooks/simple_binops/adddiv
 - Test commands: ['pytest']
 - Mode: sd
 - Excluded files: ['__init__.py']
 - N locations input: 10
 - Random seed: None

Random sample details
---------------------
 - Total locations mutated: 4
 - Total locations identified: 4
 - Location sample coverage: 100.00 %


Running time details
--------------------
 - Clean trial 1 run time: 0:00:00.291807
 - Clean trial 2 run time: 0:00:00.294794
 - Mutation trials total run time: 0:00:01.197853

Overall mutation trial summary
==============================
 - SURVIVED: 1
 - DETECTED: 3
 - TOTAL RUNS: 4
 - RUN DATETIME: 2019-01-01 19:24:16.062602


Mutations by result status
==========================


SURVIVED
--------
 - /home/zassoc/Github/m/notebooks/simple_binops/adddiv/run.py: (l: 15, c: 11) - mutation from <class '_ast.Div'> to <class '_ast.Mod'>


DETECTED
--------
 - /home/zassoc/Github/m/notebooks/simple_binops/adddiv/run.py: (l: 6, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Mod'>
 - /home/zassoc/Github/m/notebooks/simple_binops/adddiv/run.py: (l: 6, c: 18) - mutation from <class '_ast.Sub'> to <class '_ast.Div'>
 - /home/zassoc/Github/m/notebooks/simple_binops/adddiv/run.py: (l: 10, c: 11) - mutation from <class '_ast.Add'> to <class '_ast.Div'>