import sys
from collections import defaultdict
from nltk.stem import PorterStemmer
import re

ps = PorterStemmer()

stopwords=defaultdict(int)                                          #Create stopwords list
with open('stopwords.txt','r') as f:
    for line in f:
        line= line.strip()
        stopwords[line]=1

# Regular Expression to remove URLs
regExp1 = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.DOTALL)
# Regular Expression to remove CSS
regExp2 = re.compile(r'{\|(.*?)\|}',re.DOTALL)
# Regular Expression to remove {{cite **}} or {{vcite **}}
regExp3 = re.compile(r'{{v?cite(.*?)}}',re.DOTALL)
# Regular Expression to remove Punctuation
regExp4 = re.compile(r'[.,;_?()"/\']',re.DOTALL)
# Regular Expression to remove [[file:]]
regExp5 = re.compile(r'\[\[file:(.*?)\]\]',re.DOTALL)
# Regular Expression to remove Brackets and other meta characters from title
regExp6 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/?]",re.DOTALL)
# Regular Expression to remove <..> tags from text
regExp10 = re.compile(r'<(.*?)>',re.DOTALL)
# Regular Expression to remove junk from text
regExp11 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/?]",re.DOTALL)

def cleanText(text):
    '''
    Use the Regular Expressions stored to remove unnecessary things from text for tokenizing
    '''
    text = text.lower()
    text = regExp1.sub('',text)
    text = regExp2.sub('',text)
    text = regExp3.sub('',text)
    text = regExp4.sub(' ',text)
    text = regExp5.sub('',text)
    text = regExp10.sub('',text)
    text = re.sub(r'[^\x00-\x7F]+',' ', text)
    return text

docNameMap = defaultdict(int)

def readDocToName(path):
    global docNameMap
    with open(path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            docID,t = line.split("#")
            t = t.split(":")[0:-1]
            name = ' '.join(t)
            docNameMap[docID]=name

def getName(docID):
    # print(docID," ",docNameMap[docID])
    return docNameMap[docID]

def read_file(testfile):
    with open(testfile, 'r') as file:
        queries = file.readlines()
    return queries


def write_file(outputs, path_to_output):
    '''outputs should be a list of lists.
        len(outputs) = number of queries
        Each element in outputs should be a list of titles corresponding to a particular query.'''
    with open(path_to_output, 'w') as file:
        for output in outputs:
            for line in output:
                file.write(line.strip() + '\n')
            file.write('\n')

invertedIndex = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
def readIndexFromFile(path_to_index):
    global invertedIndex
    with open(path_to_index, "r") as f:
        data = f.readlines()
        for line in data:
            word,rest = line.split("=")
            doc_list = rest.split(",")
            for d in doc_list:
                docID, rest1 = d.split(":")
                num = rest1.split("#")
                for i in num:
                    # print(i)
                    category = i[0]
                    freq = i[1:]
                    # print(word+" "+docID+" "+category+" "+freq)
                    invertedIndex[word][docID][category]=int(freq)


def parseQuery(query):
    q = query
    
    # try:
    isField = False
    if ":" in query and ("title" in query or "ref" in query or "category" in query or "body" in query or "link" in query or "infobox" in query):
        d = dict()
        d["title"] = "t"
        d["ref"] = "r"
        d["body"] = "b"
        d["category"] = "c"
        d["link"] = "l"
        d["infobox"] = "i"
        isField = True
        query = query.split()
        parsed_query = []
        for q in query:
            if q[-1]=='\n':
                q = q[0:-1]
            if ":" in q:
                c,w = q.split(":")
                w = cleanText(w)
                w = ps.stem(w)
                try:
                    parsed_query.append((w,d[c])) 
                except:
                    parsed_query.append((w,"b")) 
            else:
                q = cleanText(q)
                q = ps.stem()
                parsed_query.append((q,"b"))
        return parsed_query,isField
    else:
        query = cleanText(query)
        parsed_query = []
        query_words = query.split(" ")
        for word in query_words:
            
            if len(word)>1 and word[-1]=='\n':
                word = word[0:-1]
            word = ps.stem(word)
            
            if stopwords[word]!=1 and len(word)>0:
                parsed_query.append(word)
        return parsed_query, isField
    # except:
    #     q_t = query.split()
    #     # t = []
    #     # for i in q_t:
    #     #     if ":" in i:
    #     #         a,b = i.split(":")
    #     #         if stopwords[a]!=1:
    #     #             t.append(ps.stem(i))
    #     #         if stopwords[b]!=1:
    #     #             t.append(ps.stem(i))    
    #     #     else:
    #     #         if stopwords[i]!=1:
    #     #             t.append(ps.stem(i))
    #     # return t, False

def normalSearch(query):
    docToFreqMap = defaultdict(int) 
    for word in query:
        # print(word)
        d = invertedIndex[word]
        # print(type(d))
        for docID,rest in d.items():
            # print(docID)
            for category,freq in rest.items():
                docToFreqMap[docID]+=freq
                
    docToFreqMap = sorted(docToFreqMap.items(), key=lambda item: item[1], reverse=True)[0:10]

    result = []

    for i in docToFreqMap:
        docID,freq = i
        # print(docID+" "+str(freq))
        result.append(getName(docID))
    
    return result

def fieldSearch(query):

    docToFreqMap = defaultdict(int) 
    for word,c in query:
        # print(word)
        d = invertedIndex[word]
        # print(type(d))
        for docID,rest in d.items():
            # print(docID)
            for category,freq in rest.items():
                if category == c:
                    docToFreqMap[docID]+=freq
                
    docToFreqMap = sorted(docToFreqMap.items(), key=lambda item: item[1], reverse=True)[0:10]

    result = []

    for i in docToFreqMap:
        docID,freq = i
        # print(docID+" "+str(freq))
        result.append(getName(docID))
    
    return result

def searchOne(query):
    query, isField = parseQuery(query)
    # print(query)
    result = []
    if isField:
        result = fieldSearch(query)
    else:
        result = normalSearch(query)

    # print(result)
    return result

def getResults(queries):
    results = []
    for query in queries:
        result = searchOne(query)
        # print(result)
        results.append(result)
    return results

def search(path_to_index, queries):
    '''Write your code here'''
    indexFile = path_to_index+"/index.txt"
    readIndexFromFile(indexFile)
    # print(invertedIndex)
    docTitleFile = path_to_index+"/docTitleMap.txt"
    readDocToName(docTitleFile)
    results = getResults(queries)
    # print(results)
    return results

def main():
    path_to_index = sys.argv[1]
    testfile = sys.argv[2]
    path_to_output = sys.argv[3]
    queries = read_file(testfile)
    outputs = search(path_to_index, queries)
    write_file(outputs, path_to_output)


if __name__ == '__main__':
    main()

