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
            t = t.split(":")[0:-1]
            name = ' '.join(t)
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

def normalSearch(query):
    globalSearch = dict(list())
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
        data = file.readlines()
        # if startFlag:
        #     startIndex = data.find(word+"=")
        # else:
        #     startIndex = data.find("\n"+word+"=")
        # endIndex = data.find("\n",startIndex+1)
        # reqLine = data[startIndex:endIndex]
        # print(word)
        ind = binary_search(data,word)
        # print("index ",ind)
        reqLine = data[ind]
        # print("line read: ",reqLine.split("=")[0])
        pl = reqLine.split("=")[1].split(",")
        # print("posting list len: ",len(pl))
        numDoc = len(pl)
        idf = log10(noDocs/numDoc)
        for i in pl:
            docID, entry = i.split(":")
            if docID in globalSearch:
                globalSearch[docID].append(entry+"_"+str(idf))
            else:
                globalSearch[docID] = [entry+"_"+str(idf)]
    lengthFreq = dict(dict())
    regEx = re.compile(r'(\d+|\s+)')
    for k in globalSearch:
        weightedFreq = 0
        n = len(globalSearch[k])
        for x in globalSearch[k]:
            x,idf = x.split("_")
            x = x.split("#")
            for y in x:
                lis = regEx.split(y)
                tagType, freq = lis[0], lis[1]
                if tagType == "t":
                    weightedFreq += int(freq)*1000
                elif tagType == "i" or tagType == "c" or tagType == "r" or tagType == "e":
                    weightedFreq += int(freq)*50
                elif tagType == "b":
                    weightedFreq += int(freq)
        if n in lengthFreq:
            lengthFreq[n][k] = float(log10(1+weightedFreq))*float(idf)
        else:
            lengthFreq[n] = {k : float(log10(1+weightedFreq))*float(idf)}
    count = 0
    flag = False
    # resultList = []
    
    K = 10
    # lii = heapq.nlargest(K,lengthFreq.items(), key=itemgetter(0))
    # count = 1
    # print(type(lengthFreq))
    for k,v in sorted(lengthFreq.items(),reverse=True):
        # print(count)
        # count+=1
        # print(k)
        # print(type(v))
        # print(v)
        for k1,v1 in sorted(v.items(),key=itemgetter(1),reverse=True):
            # print(k1,v1)
            print (docNameMap[k1])
            count += 1
            if count == K:
                flag = True
                break
        if flag:
            break
        # print()

def fieldSearch(query):
    globalSearch = dict(list())
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
        for i in pl_updated:
            docID, entry = i.split(":")
            if docID in globalSearch:
                globalSearch[docID].append(entry+"_"+str(idf))
            else:
                globalSearch[docID] = [entry+"_"+str(idf)]
    lengthFreq = dict(dict())
    regEx = re.compile(r'(\d+|\s+)')
    for k in globalSearch:
        weightedFreq = 0
        n = len(globalSearch[k])
        for x in globalSearch[k]:
            x,idf = x.split("_")
            x = x.split("#")
            for y in x:
                lis = regEx.split(y)
                tagType, freq = lis[0], lis[1]
                if tagType == "t":
                    if cat == "t":
                        weightedFreq += int(freq)*1000
                    else:
                        weightedFreq += int(freq)
                elif tagType == "i":
                    if cat == "i":
                        weightedFreq += int(freq)*50
                    else:
                        weightedFreq += int(freq)
                elif tagType == "c":
                    if cat == "c":
                        weightedFreq += int(freq)*50
                    else:
                        weightedFreq += int(freq)
                elif tagType == "r":
                    if cat == "r":
                        weightedFreq += int(freq)*50
                    else:
                        weightedFreq += int(freq)
                elif tagType == "e":
                    if cat == "e":
                        weightedFreq += int(freq)*50
                    else:
                        weightedFreq += int(freq)
                elif tagType == "b":
                    weightedFreq += int(freq)
        if n in lengthFreq:
            lengthFreq[n][k] = float(log10(1+weightedFreq))*float(idf)
        else:
            lengthFreq[n] = {k : float(log10(1+weightedFreq))*float(idf)}
    count = 0
    flag = False
    
    K = 10
    for k,v in sorted(lengthFreq.items(),reverse=True):
        for k1,v1 in sorted(v.items(),key=itemgetter(1),reverse=True):
            print (docNameMap[k1])
            count += 1
            if count == K:
                flag = True
                break
        if flag:
            break

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
            normalSearch(queryWords)
            stop = timeit.default_timer()
            print()
            print( "Query Took ",stop-start," seconds.")
            print()
            print()
        except Exception as e:
            print( "Some Error Occurred! Try Again")
            print(e)
    else:
        try:
            fieldSearch(queryWords)
            stop = timeit.default_timer()
            print()
            print( "Query Took ",stop-start," seconds.")
            print()
            print()
        except Exception as e:
            print( "Some Error Occurred! Try Again")
            print(e)