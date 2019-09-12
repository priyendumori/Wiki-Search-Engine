import sys
from collections import defaultdict
from nltk.stem import PorterStemmer
import timeit
import re
from bisect import bisect
from math import log10
from operator import itemgetter


ps = PorterStemmer()

stopwords=defaultdict(int)                                          #Create stopwords list
with open('stopwords.txt','r') as f:
    for line in f:
        line= line.strip()
        stopwords[line]=1

# Regular Expression to remove Punctuation
regExp4 = re.compile(r'[.,;_?()"/\']',re.DOTALL)

def cleanText(text):
    '''
    Use the Regular Expressions stored to remove unnecessary things from text for tokenizing
    '''
    text = text.lower()
    text = regExp4.sub(' ',text)
    text = re.sub(r'[^\x00-\x7F]+',' ', text)
    return text

noDocs=0
docNameMap = defaultdict(int)
def readDocToName():
    global docNameMap
    global noDocs
    path = "merged_index/docTitleMap.txt"
    with open(path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            docID,t = line.split("#")
            ind = t.rfind(":")
            # t = t.split(":")[0:-1]
            name = t[:ind]
            docNameMap[docID]=name
            noDocs+=1

def getName(docID):
    # print(docID," ",docNameMap[docID])
    return docNameMap[docID]


secondaryIndex = list()
def readSecondaryIndex():
    try:
        f = open("merged_index/secondary_index.txt","r")
        for line in f:
            secondaryIndex.append(line.split()[0])
    except:
        print( "Can't find the secondary index file in 'merged_index' Folder.")
        print( "Re - run the program when the file is in the same folder.")
        sys.exit(1)


def parseQuery(query):
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
                q = ps.stem(q)
                parsed_query.append((q,"b"))
        return parsed_query,isField
    else:
        query = cleanText(query)
        parsed_query = []
        query_words = query.split(" ")
        for word in query_words:
            word = ps.stem(word)
            
            if stopwords[word]!=1 and len(word)>0:
                parsed_query.append(word)
        return parsed_query, isField

def binary_search(l, word):
    lo = 0
    hi = len(l)-1
    while lo <= hi:
        mid = int((lo + hi)/2)
        t = l[mid].split("=")[0]
        # print(t,word)
        if t == word:
            return mid
        
        elif t < word:
            lo = mid + 1
        else:
            hi = mid - 1
    return lo

weight = dict()
weight["t"] = 1000
weight["i"] = 50
weight["r"] = 50
weight["l"] = 50
weight["c"] = 50
weight["b"] = 1

def normalSearch(query):
    global weight
    globalSearch = dict(list())
    id_tfidf_map = defaultdict(int)
    for word in query:
        loc = bisect(secondaryIndex,word)
        startFlag = False
        if loc-1 >= 0 and secondaryIndex[loc-1] == word:
            startFlag = True
            if loc-1 != 0:
                loc -= 1
            if loc+1 == len(secondaryIndex) and secondaryIndex[loc] == word:
                loc += 1

        primaryFile = "merged_index/index" + str(loc) + ".txt"
        # print("opening primary file ",primaryFile)
        file = open(primaryFile,"r")
        data = file.read()
        if startFlag:
            startIndex = data.find(word+"=")
        else:
            startIndex = data.find("\n"+word+"=")
        endIndex = data.find("\n",startIndex+1)
        reqLine = data[startIndex:endIndex]
        # print(word)
        # ind = binary_search(data,word)
        # print("index ",ind)
        # reqLine = data[ind]
        # print("line read: ",reqLine.split("=")[0])
        pl = reqLine.split("=")[1].split(",")
        # print("posting list len: ",len(pl))
        numDoc = len(pl)
        idf = log10(noDocs/numDoc)

        for d in pl:
            docID, rest1 = d.split(":")
            num = rest1.split("#")
            tf = 0
            for i in num:
                category = i[0]
                freq = i[1:]
                tf += int(freq) * int(weight[category])
                # tf += int(freq) 
            
            id_tfidf_map[docID] += float(log10(1+tf)) * float(idf)

    docToFreqMap = sorted(id_tfidf_map.items(), key=lambda item: item[1], reverse=True)[0:10]

    result = []

    for i in docToFreqMap:
        docID,freq = i
        # print(docID+" "+str(freq))
        result.append(getName(docID))
        # print(getName(docID))
    
    return result
        
def printSearchResult(result):
    for res in result:
        print(res)

def fieldSearch(query):
    globalSearch = dict(list())
    id_tfidf_map = defaultdict(int)
    for word, cat in query:
        loc = bisect(secondaryIndex,word)
        startFlag = False
        if loc-1 >= 0 and secondaryIndex[loc-1] == word:
            startFlag = True
            if loc-1 != 0:
                loc -= 1
            if loc+1 == len(secondaryIndex) and secondaryIndex[loc] == word:
                loc += 1

        primaryFile = "merged_index/index" + str(loc) + ".txt"
        file = open(primaryFile,"r")
        data = file.readlines()
        
        ind = binary_search(data,word)
        
        reqLine = data[ind]

        pl = reqLine.split("=")[1].split(",")
        pl_updated = []
        for i in pl:
            if cat in i:
                pl_updated.append(i)
        if(len(pl_updated)<=0):
            pl_updated = pl 
        # print(pl_updated)
        numDoc = len(pl_updated)
        idf = log10(noDocs/numDoc)
        
        for d in pl_updated:
            docID, rest1 = d.split(":")
            num = rest1.split("#")
            tf = 0
            for i in num:
                category = i[0]
                freq = i[1:]
                tf += int(freq) * int(weight[category])
                # tf += int(freq) 
            
            id_tfidf_map[docID] += float(log10(1+tf)) * float(idf)

    docToFreqMap = sorted(id_tfidf_map.items(), key=lambda item: item[1], reverse=True)[0:10]

    result = []

    for i in docToFreqMap:
        docID,freq = i
        # print(docID+" "+str(freq))
        result.append(getName(docID))
        # print(getName(docID))
    
    return result

print()
print("reading secondary index")
readSecondaryIndex()
print("Done...!")
print()
print("reading doc name map")
readDocToName()
print("Done...!")
print()

while True:
    print()
    query = input("Enter your query: ")
    print()
    start = timeit.default_timer()
    queryWords, isField = parseQuery(query)
    # print(queryWords)
    if not isField:
        try:
            result = normalSearch(queryWords)
            stop = timeit.default_timer()
            printSearchResult(result)
            print()
            print( "Query Took ",stop-start," seconds.")
            print()
            print()
        except Exception as e:
            print( "Some Error Occurred! Try Again")
            print(e)
    else:
        try:
            result = fieldSearch(queryWords)
            stop = timeit.default_timer()
            printSearchResult(result)
            print()
            print( "Query Took ",stop-start," seconds.")
            print()
            print()
        except Exception as e:
            print( "Some Error Occurred! Try Again")
            print(e)