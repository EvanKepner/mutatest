Mutatest diagnostic summary
===========================
 - Source location: /home/zassoc/Github/m/mutatest
 - Test commands: ['pytest']
 - Mode: s
 - Excluded files: ['__init__.py']
 - N locations input: 10
 - Random seed: None

Random sample details
---------------------
 - Total locations mutated: 10
 - Total locations identified: 41
 - Location sample coverage: 24.39 %


Running time details
--------------------
 - Clean trial 1 run time: 0:00:06.572731
 - Clean trial 2 run time: 0:00:06.522394
 - Mutation trials total run time: 0:03:37.774504

Overall mutation trial summary
==============================
 - DETECTED: 25
 - SURVIVED: 7
 - TOTAL RUNS: 32
 - RUN DATETIME: 2019-01-03 19:13:50.001784


Mutations by result status
==========================


SURVIVED
--------
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 253, c: 15) - mutation from <class '_ast.Eq'> to <class '_ast.GtE'>
 - /home/zassoc/Github/m/mutatest/cli.py: (l: 119, c: 31) - mutation from <class '_ast.Mult'> to <class '_ast.Add'>
 - /home/zassoc/Github/m/mutatest/transformers.py: (l: 81, c: 15) - mutation from <class '_ast.Gt'> to <class '_ast.LtE'>
 - /home/zassoc/Github/m/mutatest/cache.py: (l: 118, c: 9) - mutation from <class '_ast.Eq'> to <class '_ast.LtE'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 261, c: 15) - mutation from <class '_ast.And'> to <class '_ast.Or'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 265, c: 15) - mutation from <class '_ast.Eq'> to <class '_ast.Lt'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 170, c: 11) - mutation from <class '_ast.LtE'> to <class '_ast.Lt'>


DETECTED
--------
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 253, c: 15) - mutation from <class '_ast.Eq'> to <class '_ast.Gt'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 253, c: 15) - mutation from <class '_ast.Eq'> to <class '_ast.Lt'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.Mod'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.Sub'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.Add'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.Div'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.Pow'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 89, c: 54) - mutation from <class '_ast.Mult'> to <class '_ast.FloorDiv'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 33, c: 50) - mutation from <class '_ast.Eq'> to <class '_ast.LtE'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 33, c: 50) - mutation from <class '_ast.Eq'> to <class '_ast.NotEq'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 33, c: 50) - mutation from <class '_ast.Eq'> to <class '_ast.Lt'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 33, c: 50) - mutation from <class '_ast.Eq'> to <class '_ast.GtE'>
 - /home/zassoc/Github/m/mutatest/report.py: (l: 33, c: 50) - mutation from <class '_ast.Eq'> to <class '_ast.Gt'>
 - /home/zassoc/Github/m/mutatest/cache.py: (l: 118, c: 9) - mutation from <class '_ast.Eq'> to <class '_ast.NotEq'>
 - /home/zassoc/Github/m/mutatest/cache.py: (l: 118, c: 9) - mutation from <class '_ast.Eq'> to <class '_ast.Gt'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.Mult'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.Mod'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.Add'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.FloorDiv'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.Pow'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 274, c: 22) - mutation from <class '_ast.Sub'> to <class '_ast.Div'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 170, c: 11) - mutation from <class '_ast.LtE'> to <class '_ast.Eq'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 170, c: 11) - mutation from <class '_ast.LtE'> to <class '_ast.GtE'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 170, c: 11) - mutation from <class '_ast.LtE'> to <class '_ast.Gt'>
 - /home/zassoc/Github/m/mutatest/controller.py: (l: 170, c: 11) - mutation from <class '_ast.LtE'> to <class '_ast.NotEq'>