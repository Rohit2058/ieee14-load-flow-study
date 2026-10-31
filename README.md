# IEEE 14-Bus Load Flow and Short Circuit Study

Load flow (Newton-Raphson) and IEC 60909 three-phase short circuit
analysis of the IEEE 14-bus system using Python and pandapower.

## Run
    pip install pandapower matplotlib pandas
    python ieee14_study.py

## Outputs
Tables and charts are saved in the `results` folder.

## Assumptions
Short circuit data is assumed (grid 5000 MVA, generator Xd'' = 0.2 pu).
