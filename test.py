#!/usr/bin/env python3

import sys
import csv

def main():
    filename = sys.argv[1]
    transDict = {}
    name = filename.split(sep='.')[0]
    writeFile = open(name + "Output", 'w')
    with open(filename) as csv_file:
        csvReader = csv.reader(csv_file, delimiter=',')
        lineNumber = 0
        startState = []
        for line in csvReader:
            if lineNumber == 0:
                title = line[0]
                writeFile.write("File: " + title + "\n")
            elif lineNumber == 3:
                startState.append(line[0])
            elif lineNumber > 4:
                key = line[0] + "/" + str(line[1])
                transDict.setdefault(key, []).append(line[2])
            lineNumber += 1


    for string in sys.argv[2:]:
        writeFile.write("Testing String: " + string + "\n")
        all_paths = []
        traceNFA(transDict, startState, string, [], all_paths)

        # Output each path
        for path in all_paths:
            if path[-1].startswith('*'):
                writeFile.write("Accepting path: $" + ",".join(path) + "$\n")
            elif '(trap state)' in path:
                writeFile.write("Trap path: $" + ",".join(path[:-1]) + "$ (incomplete)\n")
            else:
                writeFile.write("Non-accepting path: $" + ",".join(path) + "$\n")

        total_leaves = len(all_paths)
        writeFile.write(f"Total leaves found: {total_leaves}\n")
        writeFile.write(f"Paths to accept: {len([path for path in all_paths if path[-1].startswith('*')])}\n\n")




def traceNFA(transDict, prevStates, theString, currentPath, all_paths, debug=True):
    if debug:
        print(f"Debug: prevStates: {prevStates}, remainingString: {theString}, currentPath: {currentPath}")

    currentPath = currentPath + [prevStates[-1]]

    if not theString:
        all_paths.append(currentPath)
        return

    transition_found = False
    valid_transition_for_next_char = False

    # Check transitions with the next character in the string
    nextStateKey = str(prevStates[-1]) + "/" + theString[0]
    if nextStateKey in transDict:
        transition_found = True
        for nextState in transDict[nextStateKey]:
            traceNFA(transDict, [nextState], theString[1:], currentPath, all_paths, debug)
            valid_transition_for_next_char = True

    # Check epsilon transitions
    epsilonStateKey = str(prevStates[-1]) + "/" + "~"
    if epsilonStateKey in transDict:
        transition_found = True
        for nextState in transDict[epsilonStateKey]:
            traceNFA(transDict, [nextState], theString, currentPath, all_paths, debug)

    # If transitions are found, but none are valid for the next character (including epsilon transitions), it's a trap path
    if transition_found and not valid_transition_for_next_char:
        all_paths.append(currentPath + ['(trap state)'])

    # If no transitions are found and string isn't finished, it's also a trap path
    elif not transition_found:
        all_paths.append(currentPath + ['(trap state)'])



if __name__ == "__main__":
    main()
