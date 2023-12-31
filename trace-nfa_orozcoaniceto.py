import csv
from typing import Dict, List

class NFATracer:
    """A class to trace strings through a Non-deterministic Finite Automaton (NFA) read from a CSV file."""

    def __init__(self, filename: str):
        # Initialize with the CSV file name containing NFA configuration
        self.filename = filename
        self.trans_dict = {}  # Stores transitions as a dictionary
        self.start_state = []  # Keeps track of the initial state(s)
        # Generating output file path, suffixing 'Output' to the filename without its extension
        self.output_file_path = f"{filename.rsplit('.', 1)[0]}Output"

    def read_file(self):
        """Reads the NFA configuration from a CSV file."""
        try:
            # Open and read the CSV file
            with open(self.filename) as file:
                reader = csv.reader(file, delimiter=',')
                for line_number, line in enumerate(reader):
                    # Process different lines based on their line number
                    if line_number == 0:
                        # First line: Write filename to the output file
                        self._write_to_file(f"File: {line[0]}\n")
                    elif line_number == 3:
                        # Fourth line: Record the start state
                        self.start_state.append(line[0])
                    elif line_number > 4:
                        # From sixth line onwards: Capture transition rules
                        key = f"{line[0]}/{line[1]}"
                        self.trans_dict.setdefault(key, []).append(line[2])
        except FileNotFoundError:
            # Handle file not found error
            print(f"Error: The file '{self.filename}' was not found.")
            exit(1)

    def trace_string(self, string: str):
        """Traces a string through the NFA and writes results to the output file."""
        all_paths = []  # Store all paths taken by the string in the NFA
        # Start tracing the NFA
        self._trace_nfa(self.trans_dict, self.start_state, string, [], all_paths)
        # Write all traced paths into the output file
        self._write_paths_to_file(string, all_paths)

    def _trace_nfa(self, trans_dict, prev_states, the_string, current_path, all_paths):
        """Recursively traces a string through the NFA."""
        # Record the current state in the path
        current_path = current_path + [prev_states[-1]]

        # If the string is fully processed, add the path to all_paths
        if not the_string:
            all_paths.append(current_path)
            return

        # Process the next character from the string
        self._process_transitions(prev_states[-1], the_string, trans_dict, current_path, all_paths)

    def _process_transitions(self, prev_state, the_string, trans_dict, current_path, all_paths):
        """Handles transitions for the current state and character."""
        # Track if any transition is found and if it's valid
        transition_found, valid_transition = False, False
        # Create keys for direct and epsilon transitions
        next_state_key = f"{prev_state}/{the_string[0]}"
        epsilon_key = f"{prev_state}/~"

        # Check and process direct transitions
        if next_state_key in trans_dict:
            transition_found = True
            for next_state in trans_dict[next_state_key]:
                self._trace_nfa(trans_dict, [next_state], the_string[1:], current_path, all_paths)
                valid_transition = True

        # Check and process epsilon transitions
        if epsilon_key in trans_dict:
            transition_found = True
            for next_state in trans_dict[epsilon_key]:
                self._trace_nfa(trans_dict, [next_state], the_string, current_path, all_paths)

        # Handle the case when there's no valid transition (trap state)
        if (transition_found and not valid_transition) or (not transition_found):
            all_paths.append(current_path + ['(trap state)'])

    def _write_paths_to_file(self, string, all_paths):
        """Formats and writes the traced paths for a given string to the output file."""
        # Segregate paths into accepted, trap, and rejected
        accepted_paths = [path for path in all_paths if path[-1].startswith('*')]
        trap_paths = [path for path in all_paths if '(trap state)' in path]
        rejected_paths = [path for path in all_paths if path not in accepted_paths and path not in trap_paths]

        with open(self.output_file_path, 'a') as file:
            # Writing details of each path type
            file.write(f"\nTesting String: '{string}'\n")
            file.write("\nPaths:\n")
            file.write("  Rejected Paths:\n")
            for path in rejected_paths:
                file.write(f"    {' -> '.join(path)}\n")
            file.write("  Trap Paths:\n")
            for path in trap_paths:
                file.write(f"    {' -> '.join(path[:-1])} (Trap State)\n")
            file.write("  Accepting Paths:\n")
            for path in accepted_paths:
                file.write(f"    {' -> '.join(path)}\n")

            # Writing a summary of the paths
            file.write(f"\nSummary for '{string}':\n")
            file.write(f"  Total Paths: {len(all_paths)}\n")
            file.write(f"  Accepting Paths: {len(accepted_paths)}\n")
            if accepted_paths:
                file.write("          Paths:\n")
                for path in accepted_paths:
                    file.write(f"                       - {' -> '.join(path)}\n")

    def _write_to_file(self, content: str):
        """Writes arbitrary content to the output file."""
        with open(self.output_file_path, 'a') as file:
            file.write(content)

def main():
    # Prompt for the input file name
    filename = input("Enter the filename: ")
    tracer = NFATracer(filename)
    tracer.read_file()

    # Continuously trace strings until the user decides to exit
    while True:
        test_string = input("Enter a test string (or 'exit' to quit): ")
        if test_string.lower() == 'exit':
            break
        tracer.trace_string(test_string)

if __name__ == "__main__":
    main()
