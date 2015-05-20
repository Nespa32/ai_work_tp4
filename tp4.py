
import math # for math.log
import csv # for csv file reading
import sys # for argument fetching
import StringIO # some function needs a file but you only have a string? this is for you
from sets import Set
import copy # for deep copy

def main():
    # need to take in a csv file, let's see if it's given to us
    if len(sys.argv) < 2:
        print "Missing file arg"
        print "Usage: python tp4.py $csvfile"
        sys.exit(1)

    fileStr = sys.argv[1]
    with open(fileStr, 'rb') as csvfile: # file exists, let's parse it
        firstLine = csvfile.readline() # skip first line
        # some of the csv files have empty lines/comment lines that start with %
        # skip those
        while firstLine.isspace() or firstLine.startswith("%"):
            firstLine = csvfile.readline()

        rest = csvfile.read() # read the rest of the file
        
        # let's parse the header in the first line, which has the fields
        header_reader = csv.reader(StringIO.StringIO(firstLine), skipinitialspace=True)
        for header in header_reader:
            fields = header

        # let's check if the csv format is by spaces or by commas
        # because following a single format is too hard for everyone
        delimit = ',' if ',' in rest else ' '
        spamreader = csv.reader(StringIO.StringIO(rest), delimiter=delimit, skipinitialspace=True)
        
        # assemble the test cases
        examples = []
        for row in spamreader:
            examples.append(row)

        # assemble the attributes, they're the header fields
        attributes = []
        for i in range(len(fields)):
            f = fields[i]
            if f == 'ID': # skip ID field, unique value per row <no bueno> for pattern finding
                continue
            elif f == fields[-1]: # skip goal field (which should be always the last)
                goalValues = GetValuesForFieldIndex(i, examples) # fill discrete goal values (can be yes/no, can be more)
                continue
            
            attribute = { }
            attribute['Index'] = i
            attribute['Name'] = f
            attribute['Values'] = GetValuesForFieldIndex(i, examples)
            attributes.append(attribute)

        # let's do some magic and construct the decision tree
        tree = DecisionTreeLearning(examples, attributes, [], goalValues)
        
        # woah, magic
        # let's print the tree
        PrintTree(tree)
    
def DecisionTreeLearning(examples, attributes, parent_examples, goalValues):
    if len(examples) == 0:
        return PluralityValue(parent_examples)
    elif all(ex[-1] == examples[0][-1] for ex in examples):
        return examples[0][-1] + " " + str(len(examples))
    elif len(attributes) == 0:
        return PluralityValue(examples)

    # choose the most important attribute
    max_info_gain = 0
    for attr in attributes:
        at = copy.deepcopy(attr) # attribute can be changed by Importance, due to numeric value split check
        info_gain = Importance(at, examples)
        if info_gain > max_info_gain:
            (max_info_gain, a) = (info_gain, at)
        
    if 'Numeric' in a:
        for e in examples:
            if float(e[a['Index']]) > a['Numeric']:
                e[a['Index']] = ">" + str(a['Numeric'])
            else:
                e[a['Index']] = "<" + str(a['Numeric'])

        # change the attributes' values to our new discrete type
        a['Values'] = [">" + str(a['Numeric']), "<" + str(a['Numeric'])]
    
    tree = { } # must have root test A
    tree['Attribute'] = a['Name']
    tree['Values'] = []
    
    # for potential values of our attribute
    for v in a['Values']:
        examples_for_value = [e for e in examples if e[a['Index']] == v]
        # equivalent to attributes - a
        other_attributes = [attr for attr in attributes if attr['Name'] != a['Name']]
        subtree = DecisionTreeLearning(examples_for_value, other_attributes, examples, goalValues)
        tree['Values'].append((v, subtree)) # adds branch to tree with label(a = v)
    
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

# returns the importance of an attribute for information on the examples
# value between 0 and 1
# can change attribute a due to numeric value split check
def Importance(a, examples):
    return GetEntropyForExamples(examples) - GetRemainderEntropy(a, examples)

# takes in examples, checks the probability for each possible goal value, gives us the entropy
# value between 0 and 1
def GetEntropyForExamples(examples):
    l = float(len(examples))
    if l == 0.0:
        return 0.0

    en = 0.0
    values = GetValuesForFieldIndex(len(examples[0]) - 1,  examples)
    for v in values:
        pv = sum([1 for e in examples if e[-1] == v]) / l # can never be 0 since at least one entry has to exist for this value
        en += -(pv * math.log(pv))
            
    return en

def IsFloatString(value):
  try:
    float(value)
    return True
  except ValueError:
    return False
    
# takes in an attribute and an example list, checks how much entropy there would be splitting by attribute
# if attribute values are numeric, a split point will be found
# can change attribute a due to numeric value split check
def GetRemainderEntropy(a, examples):
    # is it an attribute where all values are integers?
    # if yes, let's try to find the best split point
    if all([IsFloatString(v) for v in a['Values']]):
        values = sorted([float(v) for v in a['Values']])
        bestEn = 1
        for v in values:
            # need new copy, don't want to wreck the original examples
            examples_copy = copy.deepcopy(examples)
            attr = copy.deepcopy(a)
            idx = attr['Index']
            
            for e in examples_copy:
                if float(e[idx]) > v:
                    e[idx] = ">" + str(v)
                else:
                    e[idx] = "<" + str(v)

            attr['Values'] = [">" + str(v), "<" + str(v)]
        
            en = 0.0
            # handle attributes with discrete values
            for vk in attr['Values']:
                relevantExamples = [e for e in examples_copy if e[idx] == vk]
                en += len(relevantExamples) / float(len(examples_copy)) * GetEntropyForExamples(relevantExamples)
                
            if en < bestEn:
                (bestEn, bestSplitValue) = (en, v)
        
        # inform the caller that this attribute can be split with this value
        a['Numeric'] = bestSplitValue
        return bestEn
        
    # handle attributes with discrete values
    en = 0.0
    for vk in a['Values']:
        relevantExamples = [e for e in examples if e[a['Index']] == vk]
        en += len(relevantExamples) / float(len(examples)) * GetEntropyForExamples(relevantExamples)

    return en

# returns unique values the field/attribute can have
def GetValuesForFieldIndex(field_index, examples):
    return list(Set([e[field_index] for e in examples]))

def PrintTree(tree, depth=0):
    attr = tree['Attribute']
    list = tree['Values']
    print "  " * depth + "<" + attr + ">"
    for (vk, subtree) in list:
        if type(subtree) is str:
            print "  " * depth + "  " + vk + ": " + subtree
        else:
            print "  " * depth + "  " + vk + ":"
            PrintTree(subtree, depth + 2)

if __name__ == "__main__":
    main()
