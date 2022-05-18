Compiler for distributed QC

```
conda create -n modular python=3.9
conda deactivate && conda activate modular
pip install qiskit numpy matplotlib networkx pylatexenc
```

## Qubit Partition
- [x] Read distribution.
- [x] Assign module qubits and build local circuits
- [x] Local compile and combine
- [ ] Global communication. A*?
- [ ] Load imbalance for qubits

## DEBUG
- [ ] Make sure partition and topological op node have the same order