
import csv # for csv file reading
import sys # for argument fetching
import StringIO # some function needs a file but you only have a string? this is for you
import re # regex search

def main():
    if len(sys.argv) < 3:
        print "Missing file arg"
        print "Usage: python test_tree.py $csvfile $treefile"
        return

    csv_f = sys.argv[1]
    tree_f = sys.argv[2]
    with open(csv_f, 'rb') as csvfile: # file exists, let's parse it
        firstLine = csvfile.readline() # skip first line
        # some of the csv files have empty lines/comment lines that start with %
        # skip those
        while firstLine.isspace() or firstLine.startswith("%"):
            firstLine = csvfile.readline()

        rest = firstLine + csvfile.read() # read the rest of the file
        rest = rest.replace(",", " ") # replace commas by spaces, so that all expected csv files can be read the same way
        
        reader = csv.DictReader(StringIO.StringIO(rest), delimiter=' ', skipinitialspace=True)
        
        examples = [row for row in reader]
        
        # let's read the tree and test it
        TestTreeForExamples(tree_f, examples)

def TestTreeForExamples(tree_file, examples):
    with open(tree_file, 'rb') as f:
        text = f.read().splitlines()
        tree = ReadTree(text)
        
        match = 0
        for i in range(len(examples)):
            e = examples[i]
            c = TreeDecisionForExample(tree, e)
            print "Example " + str(i) + ": " + str(c)

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

def TreeDecisionForExample(tree, example):
    if type(tree) is str: # child node case
        return tree
    
    attr = tree['Attribute']
    v = example[attr]

    for (vk, subtree) in tree['Values']:
        if v == vk: # handle discrete attributes
            return TreeDecisionForExample(subtree, example)
        else: # handle numeric attributes
            try:
                v = float(v)
                if vk.startswith(">"):
                    vk = float(vk[1:])
                    if v > vk:
                        return TreeDecisionForExample(subtree, example)
                elif vk.startswith("<="):
                    vk = float(vk[2:])
                    if v <= vk:
                        return TreeDecisionForExample(subtree, example)

            except ValueError:
                pass # just ignore, not a numeric attribute
            
    assert "TreeDecisionForExample: invalid tree, did not find value " + example[idx] + " in attribute " + attr

if __name__ == "__main__":
    main()
