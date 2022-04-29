from module.helper_fun import add_flip_edges

class RingModule():
    def __init__(self, num_qubits, offset):
        self.num_qubits = num_qubits
        self.offset = offset
        self.build()
    
    def build(self):
        edges = []
        # Ring
        for qubit in range(self.num_qubits):
            edge = [qubit,(qubit+1)%self.num_qubits]
            edges.append(edge)
        # Bypasses
        # for qubit in range(0,self.num_qubits-1,3):
        #     edge = (qubit, (qubit+2)%self.num_qubits)
        #     edges.append(edge)
        
        self.edges = []
        self.qubits = set()
        for edge in edges:
            edge = [edge[0]+self.offset, edge[1]+self.offset]
            self.edges.append(edge)
            self.qubits.add(edge[0])
            self.qubits.add(edge[1])
        self.edges = add_flip_edges(edges=self.edges)
        self.qubits = list(self.qubits)