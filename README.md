# Architectures for quantum interconnects (ARQUIN)
A compiler for distributed QC.

## Installation
To install the `arquin` package and its requirements, enter the following
commands into your terminal:

```
python3 -m venv your_virtual_env
source your_virtual_env/bin/activate
pip install -r requirements.txt
pip install -e .
```

## How to run checks
When developing `arquin` it is useful to run the formatter and type checker before making a pull request.
To do this you can run all of the checks with `./check/all`.

## Qubit Partition
- [x] Read distribution.
- [x] Assign module qubits and build local circuits
- [x] Local compile and combine
- [ ] Global communication. A*?
- [ ] Load imbalance for qubits

## DEBUG
- [ ] Make sure partition and topological op node have the same order
