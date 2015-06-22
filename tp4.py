
import math # for math.log
import csv # for csv file reading
import sys # for argument fetching
import StringIO # some function needs a file but you only have a string? this is for you
from sets import Set
import copy # for deep copy
from optparse import OptionParser # argument parsing
import re # regex search

def main():
    usage = "usage: python tp4.py $csvfile [options]"
    parser = OptionParser(usage=usage)
    parser.add_option("-t", "--tree_file", dest="tree_file",
                      help="test previously generated tree against test data", metavar="TREE_FILE")

    (options, args) = parser.parse_args()
    # options.tree_file
    
    # need to take in a csv file, let's see if it's given to us
    if len(args) < 1:
        parser.print_help()
        sys.exit(1)

    file = args[0]
    with open(file, 'rb') as csvfile: # file exists, let's parse it
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

        # let's read the tree and test it
        if options.tree_file:
            TestTreeForExamples(options.tree_file, examples, attributes)
        else: # build the tree
            # let's do some magic and construct the decision tree
            tree = DecisionTreeLearning(examples, attributes, [], goalValues)
            
            # woah, magic
            # let's print the tree
            PrintTree(tree)
    
def DecisionTreeLearning(examples, attributes, parent_examples, goalValues):
    if len(examples) == 0:
        return PluralityValue(parent_examples) + " (0)"
    elif all(ex[-1] == examples[0][-1] for ex in examples):
        return examples[0][-1] + " (" + str(len(examples)) + ")"
    elif len(attributes) == 0:
        return PluralityValue(examples) + " (No more attributes to distinguish) (" + str(len(examples)) + ")"

    # choose the most important attribute
    max_info_gain = 0
    for attr in attributes:
        at = copy.deepcopy(attr) # attribute can be changed by Importance, due to numeric value split check
        info_gain = Importance(at, examples)
        if info_gain > max_info_gain:
            (max_info_gain, a) = (info_gain, at)

    # create a tree with root test for attribute a
    tree = { }
    tree['Attribute'] = a['Name']
    tree['Values'] = []
    
    # attribute is numeric, requires special handling
    # we pass the same set of attributes to the subtree in case we need several splits on the same attribute
    if 'Numeric' in a:
        splitValue = a['Numeric']
        # handle examples where attribute > splitValue
        examples_for_value = [e for e in examples if float(e[a['Index']]) > splitValue]
        subtree = DecisionTreeLearning(examples_for_value, attributes, examples, goalValues)
        tree['Values'].append((">" + str(splitValue), subtree)) # adds branch to tree with label(a > v)
        # handle examples where attribute <= splitValue
        examples_for_value = [e for e in examples if float(e[a['Index']]) <= splitValue]
        subtree = DecisionTreeLearning(examples_for_value, attributes, examples, goalValues)
        tree['Values'].append(("<=" + str(splitValue), subtree)) # adds branch to tree with label(a <= v)
    else: # attribute is not numeric, handle each discrete value
        # for potential values of our attribute
        for v in a['Values']:
            examples_for_value = [e for e in examples if e[a['Index']] == v]

            # equivalent to attributes - a
            other_attributes = [attr for attr in attributes if attr['Name'] != a['Name']]
            subtree = DecisionTreeLearning(examples_for_value, other_attributes, examples, goalValues)
            tree['Values'].append((v, subtree)) # adds branch to tree with label(a = v)
    
    return tree

# returns most common goal value among a set of examples
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

def TestTreeForExamples(tree_file, examples, attributes):
    with open(tree_file, 'rb') as f:
        text = f.read().splitlines()
        tree = ReadTree(text)
        
        match = 0
        for i in range(len(examples)):
            e = examples[i]
            c = TreeDecisionForExample(tree, e, attributes)
            print "Example " + str(i) + ": " + str(c)
            
            if e[-1] == c:
                match += 1
                
        print "Correct results: " + str(match) + " out of " + str(len(examples))

def ReadTree(text, depth=1):
    attr_text = text.pop(0)
    m = re.match(r"\s*<(\w+)>", attr_text) # "<Attribute>"
    attr = m.group(1)
    
    # initialize the tree
    tree = { }
    tree['Attribute'] = attr
    tree['Values'] = []
    
    # get the values for this attribute
    while len(text) > 0:
        val_text = text.pop(0)
        m = re.match(r"\s*(.+)\:\s(.+)\s.*", val_text) # "Value: Class (Number)"
        if m: # is a child node
            val = m.group(1) # value
            c = m.group(2) # class
                
            tree['Values'].append((val, c)) # child node with class c
            
        else:
            m = re.match(r"\s*(.+)\:", val_text) # "Value:"
            val = m.group(1) # value
            subtree_text = []
            while len(text) > 0 and text[0].startswith("  " * (depth * 2)):
                subtree_text.append(text.pop(0))

            subtree = ReadTree(subtree_text, depth + 1)
            tree['Values'].append((val, subtree)) # child node with subtree

    return tree

def TreeDecisionForExample(tree, example, attributes):
    if type(tree) is str: # child node case
        return tree
    
    attr = tree['Attribute']
    
    for a in attributes:
        if a['Name'] == attr:
            idx = a['Index']
            v = example[idx]
            for (vk, subtree) in tree['Values']:
                if v == vk: # handle discrete attributes
                    return TreeDecisionForExample(subtree, example, attributes)
                else: # handle numeric attributes
                    try:
                        v = float(v)
                        if vk.startswith(">"):
                            vk = float(vk[1:])
                            if v > vk:
                                return TreeDecisionForExample(subtree, example, attributes)
                        elif vk.startswith("<="):
                            vk = float(vk[2:])
                            if v <= vk:
                                return TreeDecisionForExample(subtree, example, attributes)

                    except ValueError:
                        pass # just ignore, not a numeric attribute
                    
            assert "TreeDecisionForExample: invalid tree, did not find value " + example[idx] + " in attribute " + attr

    assert "TreeDecisionForExample: invalid tree, did not find attribute " + attr

if __name__ == "__main__":
    main()
