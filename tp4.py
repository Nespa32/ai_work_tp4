
import math # for math.log
import csv # for csv file reading
from sets import Set

# for deep copy
import copy

def DecisionTreeLearning(examples, attributes, parent_examples=[]):
    if len(examples) == 0:
        return PluralityValue(parent_examples)
    # check if all examples have the same classification
    elif all(ex['Classification'] == examples[0]['Classification'] for ex in examples):
        return examples[0]['Classification'] + " " + str(len(examples))
    elif len(attributes) == 0:
        return PluralityValue(examples)

    # choose the most important attribute
    a = []
    m = 0
    for key in attributes:
        x = Importance(attributes[key], examples)
        if x > m:
            m = x
            a = attributes[key]
        
    tree = { } # must have root test A
    tree['Attribute'] = a['Name']
    tree['Values'] = []
    
    # for potential values of A
    for vk in a['Values']:
        exs = [e for e in examples if e[a['Name']] == vk]
        attributes_diff = copy.copy(attributes) # equivalent to attributes - a
        del attributes_diff[a['Name']]
        subtree = DecisionTreeLearning(exs, attributes_diff, examples)
        tree['Values'].append((vk, subtree)) # adds branch to tree with label(a = vk)

    return tree

# returns most common output value among a set of examples
def PluralityValue(examples):
    values = { }
    for ex in examples:
        try:
            values[ex['Classification']] = values[ex['Classification']] + 1
        except KeyError:
            values[ex['Classification']] = 1

    (v, m) = ('', 0)
    for val in values:
        if values[val] > m:
            (v, m) = (val, values[val])
    
    return v

# something about entropy
def Importance(a, examples):
    p = float(len([e for e in examples if e['Classification'] == 'Yes']))
    n = float(len(examples) - p)
    return B(p / (p + n)) - Remainder(a, examples)

# entropy of a Boolean random variable that is true with probability q
def B(q):
    if q == 0.0 or q == 1.0:
        return 0.0

    return -(q * math.log(q, 2) + (1 - q) * math.log(1 - q, 2))

def Remainder(a, examples):
    # attribute a has d different value divides
    # each value divide will divide the examples into partitions
    # pk are positive examples for that value divide, nk are negative examples
    s = 0
    p = float(len([e for e in examples if e['Classification'] == 'Yes']))
    n = float(len(examples) - p)

    for vk in a['Values']:
        (pk, nk) = (0.0, 0.0)
        for e in examples:
            if e[a['Name']] == vk:
                if e['Classification'] == 'Yes':
                    pk += 1
                else:
                    nk += 1

        if pk != 0.0 or nk != 0.0:
            s += (pk + nk) / (p + n) * B(pk / (pk + nk))

    return s

def GetValuesForField(field, examples):
    s = Set()
    for e in examples:
        s.add(e[field])
        
    return list(s)

def PrintTree(tree, depth):
    attr = tree['Attribute']
    list = tree['Values']
    print "  " * depth + "<" + attr + ">"
    for (vk, subtree) in list:
        if type(subtree) is str:
            print "  " * depth + "  " + vk + ": " + subtree
        else:
            print "  " * depth + "  " + vk + ":"
            PrintTree(subtree, depth + 2)
    
    
with open('restaurant.csv', 'rb') as csvfile:
    # hardcoded fields to guide in code
    # last field is 'WillWait' in the csv instead of Classification, but we need a default for the decision tree algorithm
    fields = ['ID', 'Alt', 'Bar', 'Fri', 'Hun', 'Pat', 'Price', 'Rain', 'Res', 'Type', 'Est', 'Classification']
    # spamreader = csv.reader(csvfile, delimiter=' ', skipinitialspace=True)
    spamreader = csv.DictReader(csvfile, delimiter=' ', skipinitialspace=True, fieldnames=fields)
    
    # print spamreader.rows
    # positive examples have row['WillWait'] = Yes
    examples = []
    
    # skip the first iteration with the header values
    itr = iter(spamreader)
    next(itr)
    for row in itr:
        examples.append(row)
        # print row['WillWait']
        # print row
        # print ', '.join(row)
        
    attributes =  { }
    # ['ID', 'Alt', 'Bar', 'Fri', 'Hun', 'Pat', 'Price', 'Rain', 'Res', 'Type', 'Est', 'Classification']
    for f in fields:
        if f == 'ID' or f == 'Classification':
            continue
        
        attributes[f] = { }
        attributes[f]['Name'] = f
        attributes[f]['Values'] = GetValuesForField(f, examples)
        # print attributes[f]

    tree = DecisionTreeLearning(examples, attributes)
    
    PrintTree(tree, 0)
    # print tree
        