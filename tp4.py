
import math # for math.log
import csv # for csv file reading
import sys # for argument fetching
import StringIO # some function needs a file but you only have a string? this is for you
from sets import Set

# for deep copy
import copy

def DecisionTreeLearning(examples, attributes, parent_examples=[]):
    if len(examples) == 0:
        return PluralityValue(parent_examples)
    elif all(ex[-1] == examples[0][-1] for ex in examples):
        return examples[0][-1] + " " + str(len(examples))
    elif len(attributes) == 0:
        return PluralityValue(examples)

    # choose the most important attribute
    a = []
    m = -1
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
        exs = [e for e in examples if e[a['Index']] == vk]
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
            values[ex[-1]] = values[ex[-1]] + 1
        except KeyError:
            values[ex[-1]] = 1

    (v, m) = ('', 0)
    for val in values:
        if values[val] > m:
            (v, m) = (val, values[val])
    
    return v

def Importance(a, examples):
    #for vk in a['Values']:
    
    # todo
    p = float(len([e for e in examples if e[-1] == 'Yes' or e[-1] == 'yes']))
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
    s = 1
    p = float(len([e for e in examples if e[-1] == 'Yes' or e[-1] == 'yes']))
    n = float(len(examples) - p)

    x = [v.isdigit() for v in a['Values']]
    if all(x):
        values = sorted([int(v) for v in a['Values']])
        truV = 0 # should it really have a initial value
        for v in values:
            (pk, nk) = (0.0, 0.0)
            x = 0.0
            for e in examples:
                if int(e[a['Index']]) > v:
                    if e[-1] == 'Yes' or e[-1] == 'yes':
                        pk += 1
                    else:
                        nk += 1

            if pk != 0.0 or nk != 0.0:
                x += (pk + nk) / (p + n) * B(pk / (pk + nk))
                
            (pk, nk) = (0.0, 0.0)
            for e in examples:
                if int(e[a['Index']]) <= v:
                    if e[-1] == 'Yes' or e[-1] == 'yes':
                        pk += 1
                    else:
                        nk += 1

            if pk != 0.0 or nk != 0.0:
                x += (pk + nk) / (p + n) * B(pk / (pk + nk))
                
            if x < s:
                s = x
                truV = v

        for e in examples:
            if int(e[a['Index']]) > truV:
                x = ">" + str(truV)
                e[a['Index']] = x
            else:
                x = "<" + str(truV)
                e[a['Index']] = x

        a['Values'] = [">" + str(truV), "<" + str(truV)]
        return s
        
    for vk in a['Values']:
        (pk, nk) = (0.0, 0.0)
        for e in examples:
            if e[a['Index']] == vk:
                if e[-1] == 'Yes' or e[-1] == 'yes':
                    pk += 1
                else:
                    nk += 1

        if pk != 0.0 or nk != 0.0:
            s += (pk + nk) / (p + n) * B(pk / (pk + nk))

    return s

def GetValuesForFieldIndex(fieldIndex, examples):
    s = Set()
    for e in examples:
        s.add(e[fieldIndex])
        
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

if len(sys.argv) < 2:
    print "Missing file arg"
    print "Usage: python tp4.py $csvfile"
    sys.exit(1)

fileStr = sys.argv[1]
with open(fileStr, 'rb') as csvfile:
    firstLine = csvfile.readline() # skip first line
    rest = csvfile.read() # read the rest of the file
    
    header_reader = csv.reader(StringIO.StringIO(firstLine), skipinitialspace=True)
    for header in header_reader:
        fields = header

    # let's check if the csv format is by spaces or by commas
    delimit = ',' if ',' in rest else ' '
    spamreader = csv.reader(StringIO.StringIO(rest), delimiter=delimit, skipinitialspace=True)
    
    examples = []
    for row in spamreader:
        examples.append(row)

    attributes =  { }
    for i in range(len(fields)):
        f = fields[i]
        # skip ID field and classification field (which should be always the last)
        if f == 'ID' or f == fields[-1]:
            continue
        
        attributes[f] = { }
        attributes[f]['Index'] = i
        attributes[f]['Name'] = f
        attributes[f]['Values'] = GetValuesForFieldIndex(i, examples)

    tree = DecisionTreeLearning(examples, attributes)
    
    PrintTree(tree, 0)
