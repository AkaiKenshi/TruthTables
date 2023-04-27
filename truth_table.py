import numpy as np
from typing import Callable
from prettytable import PrettyTable
import re

ACTIONS_PATTERN = r"[¬∧∨↔→]"
LETTER_PATTERN = r"([a-zA-Z])"
KEY_PATTERN = r"\[U[0-9]{1,}\]"
NOT_PATTERN = fr"(¬({KEY_PATTERN}))"
AND_PATTERN = fr"(({KEY_PATTERN}).?∧.?({KEY_PATTERN}))"
OR_PATTERN = fr"(({KEY_PATTERN}).?∨.?({KEY_PATTERN}))"
CONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?→.?({KEY_PATTERN}))"
BICONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?↔.?({KEY_PATTERN}))"
EQUIVALENCE_PATTERN = fr"(({KEY_PATTERN}).?≡.?({KEY_PATTERN}))"
ARGUMENT_PATTERN = fr"⊢.?({KEY_PATTERN})"
ARGUMENT_CONDITION_PATTERN = fr"({KEY_PATTERN}),"
PARENTHESES_PATTERN = fr"(\(((?:[^()])*)\))"


#ACTIONS_PATTERN = r"[\!\|&]|<>|->"
#LETTER_PATTERN = r"([a-zA-Z])"
#KEY_PATTERN = r"\[U[0-9]{1,}\]"
#NOT_PATTERN = fr"(\!({KEY_PATTERN}))"
#AND_PATTERN = fr"(({KEY_PATTERN}).?&.?({KEY_PATTERN}))"
#OR_PATTERN = fr"(({KEY_PATTERN}).?\|.?({KEY_PATTERN}))"
#CONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?->.?({KEY_PATTERN}))"
#BICONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?<>.?({KEY_PATTERN}))"
#EQUIVALENCE_PATTERN = fr"(({KEY_PATTERN}).?=.?({KEY_PATTERN}))"
#ARGUMENT_PATTERN = fr"\+.?({KEY_PATTERN})"
#ARGUMENT_CONDITION_PATTERN = fr"({KEY_PATTERN}),"
#PARENTHESES_PATTERN = fr"(\(((?!.*[(]).*?)\))"


table = {}
keys = {}
ignore_keys = []


def assign_key(key: str, prepositions: str):
    # creates and manages a new key
    new_key = ""
    if key in keys.values():
        index = list(keys.values()).index(key)
        new_key = list(keys.keys())[index]
    else: 
        new_key = f"[U{len(keys)}]"
        keys[new_key] = key
    prepositions = prepositions.replace(key, new_key)

    return prepositions, new_key


def reverse_key(val_to_replace: str):
    # Reverses the keying processes
    for key in reversed(keys):
        val = keys[key]
        val_to_replace = val_to_replace.replace(key, val)
    return val_to_replace

def generate_truth_table(keys: list):
    truth_dict = {}  # creates a dictionary for the truth table

    for i in range(len(keys)):
        input_values = []  # creates an array for each truth value

        num_of_values = 2 ** len(keys)
        offset = 2 ** (i + 1)
        nums = np.linspace(0, num_of_values - 1, num_of_values)
        truth_dict[keys[i]] = nums % offset < offset/2

    return truth_dict


def find_letter_prepositions(prepositions: str):
    # searches for the letters in prepositions
    matches = list(set(re.findall(LETTER_PATTERN, prepositions)))
    matches.sort()  # sorts the list in alphabetical order
    new_keys = []

    for match in matches:
        prepositions, key = assign_key(match, prepositions)  # creates the key
        new_keys.append(key)

    # generation of the first table
    table.update(generate_truth_table(new_keys))
    return prepositions


def find_negations(prepositions: str):
    # searches for the negations
    matches = list(set(re.findall(NOT_PATTERN, prepositions)))

    for match in matches:
        prepositions, new_key = assign_key(match[0], prepositions)
        table[new_key] = ~table[match[1]]
    return prepositions


def find_compound_propositions(pattern: str, prepositions: str, proposition_handler: Callable):
    matches = list(set(re.findall(pattern, prepositions)))  # find the pattern

    for match in matches:
        prepositions, new_key = assign_key(match[0], prepositions)
        table[new_key] = proposition_handler(table[match[1]], table[match[2]])

    return prepositions


def find_conjunction(prepositions: str):
    return find_compound_propositions(AND_PATTERN, prepositions, lambda a, b: a & b)


def find_disjunction(prepositions: str):
    return find_compound_propositions(OR_PATTERN, prepositions, lambda a, b: a | b)


def find_conditionals(prepositions: str):
    return find_compound_propositions(CONDITIONAL_PATTERN, prepositions, lambda a, b: ~ (a & ~ b))


def find_biconditionals(prepositions: str):
    return find_compound_propositions(BICONDITIONAL_PATTERN, prepositions, lambda a, b: a == b)


def find_parentheses(prepositions: str):
    matches = list(set(re.findall(PARENTHESES_PATTERN, prepositions)))
    there_was_a_match = False
    for match in matches:
        there_was_a_match = True
        new_match = work_with_operators(match[1]).replace(" ", "")
        prepositions = prepositions.replace(match[1], new_match)
        prepositions, new_key = assign_key(f"({new_match})", prepositions)
        table[new_key] = table[new_match]
        ignore_keys.append(new_key)

    return prepositions, there_was_a_match


def find_equivalencies(preposition: str):
    match = re.findall(EQUIVALENCE_PATTERN, preposition)[0]

    return np.array_equiv(table[match[1]], table[match[2]])


def find_argument(prepositions: str):
    argument = re.findall(ARGUMENT_PATTERN, prepositions)[0]
    conditions = re.findall(ARGUMENT_CONDITION_PATTERN, prepositions)

    final_condition = table[conditions[0]]
    for condition in conditions:
        final_condition = final_condition & table[condition]

    index_true = np.where(final_condition)
    arguments_list = table[argument][index_true]

    if (not all(x == arguments_list[0] for x in arguments_list)):
        return "Fallacy"

    return "Tautology" if (arguments_list[0]) else "Contradiction"


def work_with_operators(prepositions):
    while re.search(ACTIONS_PATTERN, prepositions):
        prepositions, there_was_a_match = find_parentheses(prepositions)
        if there_was_a_match:
            continue
        prepositions = find_negations(prepositions)
        prepositions = find_conjunction(prepositions)
        prepositions = find_disjunction(prepositions)
        prepositions = find_conditionals(prepositions)
        prepositions = find_biconditionals(prepositions)
    return prepositions


prepositions = find_letter_prepositions(input("input: "))
prepositions = work_with_operators(prepositions)

print_table = PrettyTable()


sorted_table = dict(sorted(table.items(), key=lambda x: len(reverse_key(str(x[0])))))

for key,val in sorted_table.items():
    if (key not in ignore_keys):
        print_table.add_column(reverse_key(key), val)

print(print_table)

if (re.search(EQUIVALENCE_PATTERN, prepositions)):
    print("is equivalent:", find_equivalencies(prepositions))

elif (re.search(ARGUMENT_PATTERN, prepositions)):
    print(find_argument(prepositions))
