import numpy as np
from typing import Callable
from prettytable import PrettyTable
import re

#regular expressions to find patterns inside of a string 
ACTIONS_PATTERN = r"[¬∧∨↔→]"  #this searches wether any of this characters exists inside a string 
LETTER_PATTERN = r"([a-zA-Z])" #this searches for letters to be replaced as variables 
KEY_PATTERN = r"\[U[0-9]{1,}\]" #this searches for the key [Ux] where x is any number
NOT_PATTERN = fr"(¬({KEY_PATTERN}))" # this searches for ¬[Ux]
AND_PATTERN = fr"(({KEY_PATTERN}).?∧.?({KEY_PATTERN}))" # this searches for [Ux] ∧ [Ux]
OR_PATTERN = fr"(({KEY_PATTERN}).?∨.?({KEY_PATTERN}))" # this searches for [Ux] ∨ [Ux]
CONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?→.?({KEY_PATTERN}))" # this searches for [Ux] → [Ux]
BICONDITIONAL_PATTERN = fr"(({KEY_PATTERN}).?↔.?({KEY_PATTERN}))" # this searches for [Ux] ↔ [Ux]
EQUIVALENCE_PATTERN = fr"(({KEY_PATTERN}).?≡.?({KEY_PATTERN}))" # this searches for [Ux] ≡ [Ux]
ARGUMENT_PATTERN = fr"⊢.?({KEY_PATTERN})" # this searches for ⊢[Ux] 
ARGUMENT_CONDITION_PATTERN = fr"({KEY_PATTERN})," # this searches for [Ux],
PARENTHESES_PATTERN = fr"(\(((?:[^()])*)\))" # this searches for the parentheses only if there is no nested parentheses 

#Uncomment the following if you want to use:
#   !  instead of ¬
#   &  instead of ∧
#   |  instead of ∨
#   -> instead of →
#   <> instead of ↔

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


table = {}  #where we store the truth table 
keys = {} #where whe store the keys 
ignore_keys = [] # this exist to avoid duplicate keys created in the parentheses process 


def assign_key(key: str, prepositions: str):
    # creates and manages a new key
    new_key = ""
    #first we check to se if the value is in the table 
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
        prepositions, new_key = assign_key(match[0], prepositions) # replaces the negation for the key in the preposition 
        table[new_key] = ~table[match[1]]  # adds the truth table to the dictionary
    return prepositions


def find_compound_propositions(pattern: str, prepositions: str, proposition_handler: Callable):
    matches = list(set(re.findall(pattern, prepositions)))  # find the pattern that was given

    for match in matches: #for each match we do the 
        prepositions, new_key = assign_key(match[0], prepositions) # replaces the key in the preposition  
        table[new_key] = proposition_handler(table[match[1]], table[match[2]]) # adds the truth table to the dictionary

    return prepositions


def find_conjunction(prepositions: str): # searches for the and operation and works with it
    return find_compound_propositions(AND_PATTERN, prepositions, lambda a, b: a & b) 


def find_disjunction(prepositions: str): # searches for the or operation and works with it
    return find_compound_propositions(OR_PATTERN, prepositions, lambda a, b: a | b)


def find_conditionals(prepositions: str): # searches for the conditional operation and works with it
    return find_compound_propositions(CONDITIONAL_PATTERN, prepositions, lambda a, b: ~ (a & ~ b))


def find_biconditionals(prepositions: str): # searches for the biconditional operation and works with it
    return find_compound_propositions(BICONDITIONAL_PATTERN, prepositions, lambda a, b: a == b)


def find_parentheses(prepositions: str): 
    # searches for the an parentheses that doesn't have a nested parentheses 
    # ( ) ✓ / ( ( ) ) X
    matches = list(set(re.findall(PARENTHESES_PATTERN, prepositions)))
    there_was_a_match = False 
    for match in matches:
        there_was_a_match = True 

        new_match = work_with_operators(match[1]).replace(" ", "") #creates a smaller preposition to work with 
        prepositions = prepositions.replace(match[1], new_match) #replaces the old match for the new match 
         # the new match looks like [Ux] so we add parenthesis and replace it for a new key 
        prepositions, new_key = assign_key(f"({new_match})", prepositions) 
        table[new_key] = table[new_match] #since the last step didn't generate a change we add the new match table as the table for this one
        ignore_keys.append(new_key) # since it's a duplicate truth table we ignore it 

    return prepositions, there_was_a_match


def find_equivalencies(preposition: str):
    match = re.findall(EQUIVALENCE_PATTERN, preposition)[0] # finds if the equivalence  

    return np.array_equiv(table[match[1]], table[match[2]]) # returns wether is equivalent or not


def find_argument(prepositions: str):
    argument = re.findall(ARGUMENT_PATTERN, prepositions)[0] # finds the argument 
    conditions = re.findall(ARGUMENT_CONDITION_PATTERN, prepositions) # finds the arguments conditions 

    final_condition = table[conditions[0]] #sets the default value for final condition
    for condition in conditions:
        final_condition = final_condition & table[condition] # checks for where all conditions are True

    index_true = np.where(final_condition) # finds the indexes where all conditions are True
    arguments_list = table[argument][index_true] #gets the list of arguments where all conditions where True

    if (not all(x == arguments_list[0] for x in arguments_list)): #checks to see if not all arguments are the same  
        return "Fallacy"

    return "Tautology" if (arguments_list[0]) else "Contradiction" #Since all arguments are the same we return the first one 

#the order of operations 
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

#this set off the logic 
prepositions = find_letter_prepositions(input("input: "))
prepositions = work_with_operators(prepositions)

#generates the pretty table 
print_table = PrettyTable()

sorted_table = dict(sorted(table.items(), key=lambda x: len(reverse_key(str(x[0]))))) 
for key,val in sorted_table.items():
    if (key not in ignore_keys):
        print_table.add_column(reverse_key(key), val)

print(print_table)

#checks if it needs equivalence or argument
if (re.search(EQUIVALENCE_PATTERN, prepositions)):
    print("is equivalent:", find_equivalencies(prepositions))

elif (re.search(ARGUMENT_PATTERN, prepositions)):
    print(find_argument(prepositions))
