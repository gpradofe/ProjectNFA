import csv
from typing import Dict, List

class NFATracer:
    """A class to trace strings through a Non-deterministic Finite Automaton (NFA) read from a CSV file."""

    def __init__(self, filename: str):
        self.filename = filename
        self.trans_dict = {}  # Dictionary to store transitions
        self.start_state = []  # List to hold the start state(s)
        # Create output file path, appending 'Output' to the base filename
        self.output_file_path = f"{filename.rsplit('.', 1)[0]}Output"

    def read_file(self):
        """Reads the NFA configuration from a CSV file."""
        try:
            with open(self.filename) as file:
                reader = csv.reader(file, delimiter=',')
                for line_number, line in enumerate(reader):
                    if line_number == 0:
                        self._write_to_file(f"File: {line[0]}\n")
                    elif line_number == 3:
                        self.start_state.append(line[0])
                    elif line_number > 4:
                        key = f"{line[0]}/{line[1]}"
                        self.trans_dict.setdefault(key, []).append(line[2])
        except FileNotFoundError:
            print(f"Error: The file '{self.filename}' was not found.")
            exit(1)

    def trace_string(self, string: str):
        """Traces a string through the NFA and writes results to the output file."""
        all_paths = []
        self._trace_nfa(self.trans_dict, self.start_state, string, [], all_paths)
        self._write_paths_to_file(string, all_paths)

    def _trace_nfa(self, trans_dict, prev_states, the_string, current_path, all_paths):
        """Recursively traces a string through the NFA."""
        current_path = current_path + [prev_states[-1]]

        if not the_string:
            all_paths.append(current_path)
            return

        self._process_transitions(prev_states[-1], the_string, trans_dict, current_path, all_paths)

    def _process_transitions(self, prev_state, the_string, trans_dict, current_path, all_paths):
        """Processes transitions for a given state and the current character."""
        transition_found, valid_transition = False, False
        next_state_key = f"{prev_state}/{the_string[0]}"
        epsilon_key = f"{prev_state}/~"

        if next_state_key in trans_dict:
            transition_found = True
            for next_state in trans_dict[next_state_key]:
                self._trace_nfa(trans_dict, [next_state], the_string[1:], current_path, all_paths)
                valid_transition = True

        if epsilon_key in trans_dict:
            transition_found = True
            for next_state in trans_dict[epsilon_key]:
                self._trace_nfa(trans_dict, [next_state], the_string, current_path, all_paths)

        if (transition_found and not valid_transition) or (not transition_found):
            all_paths.append(current_path + ['(trap state)'])

    def _write_paths_to_file(self, string, all_paths):
        """Formats and categorizes paths; writes them to the output file."""
        # Categorizing paths
        accepted_paths = [path for path in all_paths if path[-1].startswith('*')]
        trap_paths = [path for path in all_paths if '(trap state)' in path]
        rejected_paths = [path for path in all_paths if path not in accepted_paths and path not in trap_paths]

        with open(self.output_file_path, 'a') as file:
            file.write(f"\nTesting String: '{string}'\n")
            file.write("\nPaths:\n")

            # Rejected paths
            file.write("  Rejected Paths:\n")
            for path in rejected_paths:
                file.write(f"    {' -> '.join(path)}\n")

            # Trap paths
            file.write("  Trap Paths:\n")
            for path in trap_paths:
                file.write(f"    {' -> '.join(path[:-1])} (Trap State)\n")

            # Accepted paths
            file.write("  Accepting Paths:\n")
            for path in accepted_paths:
                file.write(f"    {' -> '.join(path)}\n")

            # Summary with details of accepting paths
            file.write(f"\nSummary for '{string}':\n")
            file.write(f"  Total Paths: {len(all_paths)}\n")
            file.write(f"  Accepting Paths: {len(accepted_paths)}\n")
            if accepted_paths:
                file.write("          Paths:\n")
                for path in accepted_paths:
                    file.write(f"                       - {' -> '.join(path)}\n")


    def _write_to_file(self, content: str):
        """Writes a string to the output file."""
        with open(self.output_file_path, 'a') as file:
            file.write(content)

def main():
    filename = input("Enter the filename: ")
    tracer = NFATracer(filename)
    tracer.read_file()

    while True:
        test_string = input("Enter a test string (or 'exit' to quit): ")
        if test_string.lower() == 'exit':
            break
        tracer.trace_string(test_string)

if __name__ == "__main__":
    main()
