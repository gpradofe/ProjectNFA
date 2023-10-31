import csv
import re

# Class for representing a Non-deterministic Finite Automaton (NFA)
class NFA:
    def __init__(self, name="N1"):
        self.name = name
        self.transitions = []  # List to store NFA transitions
        self.state_counter = 0  # Counter for generating unique state names
        self.states = set()  # Set of NFA states
        self.alphabet = set()  # Set of input alphabet symbols
        self.start_state = self.new_state()  # Start state of the NFA
        self.final_states = set()  # Set of accept (final) states in the NFA

    def new_state(self):
        # Generate a new unique state name
        state = f"q{self.state_counter}"
        self.state_counter += 1
        self.states.add(state)
        return state

    def add_transition(self, start, input_symbol, end):
        # Add a transition to the NFA
        self.transitions.append((start, input_symbol, end))
        if input_symbol != "∼":  # Epsilon transitions are not part of the alphabet
            self.alphabet.add(input_symbol)

    def build_nfa_from_regex(self, regex):
        # Build an NFA from a regular expression
        start, end = self.parse_sub_regex(regex, 0, len(regex))
        self.final_states.add(end)
        return start, end

    def parse_sub_regex(self, regex, start_index, end_index):
        # Parse a sub-regex and generate corresponding NFA states and transitions
        start_state = self.new_state()
        current_state = start_state

        index = start_index
        while index < end_index:
            char = regex[index]

            if char == '(':
                # Find the matching closing parenthesis
                brace_count, sub_end = 1, index + 1
                while brace_count > 0 and sub_end < end_index:
                    if regex[sub_end] == '(':
                        brace_count += 1
                    elif regex[sub_end] == ')':
                        brace_count -= 1
                    sub_end += 1

                # Recursively process the contents of the parentheses
                sub_start, sub_end_state = self.parse_sub_regex(regex, index + 1, sub_end - 1)
                self.add_transition(current_state, "∼", sub_start)
                current_state = sub_end_state
                index = sub_end  # Skip past the closing parenthesis

            elif char == '*':
                # Handle Kleene star (zero or more repetitions)
                loop_start = self.new_state()
                loop_end = self.new_state()
                self.add_transition(current_state, "∼", loop_start)
                self.add_transition(loop_start, "∼", loop_end)
                self.add_transition(loop_end, "∼", loop_start)
                current_state = loop_end

            elif char == 'U':
                # Handle union operator (alternation)
                next_start, next_end = self.parse_sub_regex(regex, index + 1, end_index)
                union_start = self.new_state()
                union_end = self.new_state()
                self.add_transition(union_start, "∼", start_state)
                self.add_transition(union_start, "∼", next_start)
                self.add_transition(current_state, "∼", union_end)
                self.add_transition(next_end, "∼", union_end)
                current_state = union_end
                break  # Union operation splits the processing flow

            else:
                # Regular character, create a transition
                next_state = self.new_state()
                self.add_transition(current_state, char, next_state)
                current_state = next_state

            index += 1

        return start_state, current_state

    def write_to_csv(self, filename_suffix='REGEX_TO_NFA'):
        # Write NFA to a CSV file
        output_filename = f"{filename_suffix}_{self.name}.csv"
        with open(output_filename, 'w', newline='') as file:
            writer = csv.writer(file)

            writer.writerow([f'{filename_suffix} {self.name},,,'])
            
            # States including accept states, marked with an asterisk
            states_with_asterisk = {f"*{state}" if state in self.final_states else state for state in self.states}
            writer.writerow(sorted(states_with_asterisk) + [''] * (4 - len(states_with_asterisk)))

            # Alphabet
            writer.writerow(sorted(self.alphabet) + [''] * (3 - len(self.alphabet)))

            # Start state
            writer.writerow([self.start_state] + [''] * 3)

            # Accept states, marked with an asterisk
            writer.writerow(sorted({f"*{state}" for state in self.final_states}) + [''] * (4 - len(self.final_states)))

            # Transitions
            for start, input_symbol, end in self.transitions:
                marked_start = f"*{start}" if start in self.final_states else start
                marked_end = f"*{end}" if end in self.final_states else end
                writer.writerow([marked_start, input_symbol, marked_end, ''])

        print(f"{filename_suffix} {self.name} saved to {output_filename}")

if __name__ == "__main__":
    print("Please enter a regular expression using standard regex symbols:")
    regex = input("Regex: ")
    
    # Basic validation for regex input
    try:
        re.compile(regex)
    except re.error:
        print("Invalid regular expression.")
    else:
        nfa_converter = NFA()
        nfa_converter.build_nfa_from_regex(regex)

        print("\nPlease enter the name of the output file (without extension):")
        filename = input("Filename: ")
        # Ensuring filename is valid and appending a default extension if not provided
        filename = re.sub(r'[^a-zA-Z0-9_\-]', '_', filename)  # Replacing invalid characters
        if not filename.endswith('.csv'):
            filename += '.csv'

        nfa_converter.write_to_csv(filename_suffix=filename)
