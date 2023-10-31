import csv
from collections import defaultdict, deque

class NFAToDFAConverter:
    def __init__(self, filename: str):
        self.filename = filename
        self.nfa_transitions = defaultdict(list)
        self.start_state = None
        self.accept_states = set()

    def epsilon_closure(self, states):
        stack = list(states)
        closure = set(states)

        while stack:
            state = stack.pop()
            for next_state in self.nfa_transitions.get((state, '~'), []):
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure

    def nfa_to_dfa(self):
        dfa = defaultdict(list)
        dfa_start_state = '+'.join(sorted(self.epsilon_closure([self.start_state])))
        dfa_accept_states = set()
        unmarked_states = [dfa_start_state]
        dfa_states = {dfa_start_state}

        while unmarked_states:
            current_dfa_state = unmarked_states.pop()
            nfa_states = set(current_dfa_state.split('+'))

            for symbol in set(sym for state, sym in self.nfa_transitions if sym != '~'):
                next_states = set()
                for state in nfa_states:
                    for closure_state in self.epsilon_closure([state]):
                        for next_state in self.nfa_transitions.get((closure_state, symbol), []):
                            next_states |= self.epsilon_closure([next_state])

                if next_states:
                    next_dfa_state = '+'.join(sorted(next_states))
                    dfa[(current_dfa_state, symbol)] = [next_dfa_state]

                    if next_dfa_state not in dfa_states:
                        dfa_states.add(next_dfa_state)
                        unmarked_states.append(next_dfa_state)

        for dfa_state in dfa_states:
            if any(state in self.accept_states for state in dfa_state.split('+')):
                dfa_accept_states.add('*' + dfa_state)

        return dfa, dfa_start_state, dfa_accept_states

    def read_nfa_from_file(self):
        with open(self.filename) as file:
            reader = csv.reader(file, delimiter=',')
            for line_number, line in enumerate(reader):
                if line_number == 3:
                    self.start_state = line[0].strip('*')
                elif line_number > 4:
                    state, symbol, next_state = line[0].strip('*'), line[1] or '~', line[2].strip('*')
                    self.nfa_transitions[(state, symbol)].append(next_state)

                    if '*' in line[0] or '*' in line[2]:
                        self.accept_states.add(next_state)
                        if '*' in line[0]:
                            self.accept_states.add(state)

    def write_dfa_to_file(self, dfa, start_state, accept_states, filename_suffix='Minimized'):
        output_filename = f"{filename_suffix}_{self.filename}"
        with open(output_filename, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow([f'{filename_suffix} DFA,,,'])
            states = sorted({state for state, _ in dfa} | {next_state for _, next_states in dfa.items() for next_state in next_states})
            writer.writerow(states + [''] * (4 - len(states)))
            alphabet = sorted({symbol for _, symbol in dfa})
            writer.writerow(alphabet + [''] * (3 - len(alphabet)))
            writer.writerow([start_state] + [''] * 3)
            writer.writerow(sorted(accept_states) + [''] * (4 - len(accept_states)))

            for (state, symbol), next_states in dfa.items():
                for next_state in next_states:
                    marked_state = '*' + state if '*' + state in accept_states else state
                    marked_next_state = '*' + next_state if '*' + next_state in accept_states else next_state
                    writer.writerow([marked_state, symbol, marked_next_state, ''])

        print(f"{filename_suffix} DFA saved to {output_filename}")

    def convert_and_export(self):
        self.read_nfa_from_file()
        dfa, dfa_start_state, dfa_accept_states = self.nfa_to_dfa()
        self.write_dfa_to_file(dfa, dfa_start_state, dfa_accept_states, 'Original')

        return dfa, dfa_start_state, dfa_accept_states

class DFAMinimizer:
    def __init__(self, dfa, start_state, accept_states):
        self.dfa = dfa
        self.start_state = start_state
        self.accept_states = accept_states

    def get_reachable_states(self):
        """Returns the set of states that are reachable from the start state."""
        reachable_states = set()
        queue = deque([self.start_state])

        while queue:
            state = queue.popleft()
            reachable_states.add(state)
            for symbol in set(symbol for _, symbol in self.dfa.keys()):
                next_states = self.dfa.get((state, symbol), [])
                for next_state in next_states:
                    if next_state not in reachable_states:
                        queue.append(next_state)

        return reachable_states

    def minimize(self):
        # Step 1: Remove unreachable states
        reachable_states = self.get_reachable_states()
        self.dfa = {k: v for k, v in self.dfa.items() if k[0] in reachable_states}

        # Step 2: Partition states into equivalence classes
        # Initial partition (accept states and non-accept states)
        accept_states = {state for state in reachable_states if '*' + state in self.accept_states}
        non_accept_states = reachable_states - accept_states
        partitions = [accept_states, non_accept_states]

        while True:
            new_partitions = []
            for p in partitions:
                subsets = self.partition(p, partitions)
                new_partitions.extend(subsets)

            if len(new_partitions) == len(partitions):
                break
            partitions = new_partitions

        # Step 3: Construct minimized DFA
        # Using representative state names from each partition
        minimized_dfa = defaultdict(list)
        representative_states = {min(p): p for p in partitions}
        state_mapping = {state: min(partition) for partition in partitions for state in partition}
        
        for (state, symbol), next_states in self.dfa.items():
            from_state = state_mapping[state]
            for next_state in next_states:
                to_state = state_mapping[next_state]
                if to_state not in minimized_dfa[(from_state, symbol)]:
                    minimized_dfa[(from_state, symbol)].append(to_state)

        # Determining new start and accept states
        new_start_state = state_mapping[self.start_state]
        new_accept_states = {state_mapping[state.replace('*', '')] for state in self.accept_states if state.replace('*', '') in state_mapping}

        return minimized_dfa, new_start_state, new_accept_states, representative_states

    def partition(self, states, partitions):
        """Refines the partition of states based on their transitions."""
        if not states:
            return []

        # Dictionary to keep subsets of the partition based on transitions
        subsets = defaultdict(set)
        for state in states:
            subset_key = tuple(sorted((symbol, self.find_partition(next_state, partitions)) 
                                      for symbol in set(symbol for _, symbol in self.dfa.keys()) 
                                      for next_state in self.dfa.get((state, symbol), [])))
            subsets[subset_key].add(state)

        return list(subsets.values())

    def find_partition(self, state, partitions):
        """Finds the partition index for a given state."""
        for idx, partition in enumerate(partitions):
            if state in partition:
                return idx
        return None
    def write_minimized_dfa_to_file(self, minimized_dfa, minimized_start_state, minimized_accept_states, filename):
        output_filename = f"Minimized_{filename}"
        with open(output_filename, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow(['Minimized DFA,,,'])
            
            # Extract states and mark accept states with an asterisk
            states = sorted({state for state, _ in minimized_dfa.keys()} | {state for _, states in minimized_dfa.items() for state in states})
            marked_states = ['*' + state if state in minimized_accept_states else state for state in states]
            writer.writerow(marked_states + [''] * (4 - len(marked_states)))

            alphabet = sorted({symbol for _, symbol in minimized_dfa})
            writer.writerow(alphabet + [''] * (3 - len(alphabet)))

            # Mark start state if it's an accept state
            start_state_marked = '*' + minimized_start_state if minimized_start_state in minimized_accept_states else minimized_start_state
            writer.writerow([start_state_marked] + [''] * 3)

            # Write the accept states
            marked_accept_states = sorted('*' + state for state in minimized_accept_states)
            writer.writerow(marked_accept_states + [''] * (4 - len(marked_accept_states)))

            for (state, symbol), next_states in minimized_dfa.items():
                for next_state in next_states:
                    marked_state = '*' + state if state in minimized_accept_states else state
                    marked_next_state = '*' + next_state if next_state in minimized_accept_states else next_state
                    writer.writerow([marked_state, symbol, marked_next_state, ''])

        print(f"Minimized DFA saved to {output_filename}")

def main():
    filename = input("Enter the filename of the NFA: ")
    converter = NFAToDFAConverter(filename)
    dfa, dfa_start_state, dfa_accept_states = converter.convert_and_export()
    try:
        minimizer = DFAMinimizer(dfa, dfa_start_state, dfa_accept_states)
        minimized_dfa, minimized_dfa_start_state, minimized_dfa_accept_states, _ = minimizer.minimize()
        minimizer.write_minimized_dfa_to_file(minimized_dfa, minimized_dfa_start_state, minimized_dfa_accept_states, filename)
    except:
        print("Error: The NFA is already minimized.")
if __name__ == "__main__":
    main()