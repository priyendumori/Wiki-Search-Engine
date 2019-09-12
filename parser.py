from xml.sax import parse,ContentHandler
import sys
import re
import timeit
from nltk.stem import PorterStemmer
from collections import defaultdict

stopwords=defaultdict(int)                                          #Create stopwords list
with open('stopwords.txt','r') as f:
  for line in f:
    line= line.strip()
    stopwords[line]=1

pathToIndex = sys.argv[2]
# pathToIndexFile = pathToIndex +  "/index.txt"
pathToIndexFile = pathToIndex
docTitleMapFile = pathToIndex+"/docTitleMap.txt"
ps = PorterStemmer()
invertedIndex = defaultdict(lambda:defaultdict(lambda:defaultdict(int)))
documentTitleMapping = open(docTitleMapFile,"w")
limit = 25000
stemCache = {}

# Regular Expression to remove URLs
regExp1 = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',re.DOTALL)
# Regular Expression to remove CSS
regExp2 = re.compile(r'{\|(.*?)\|}',re.DOTALL)
# Regular Expression to remove {{cite **}} or {{vcite **}}
regExp3 = re.compile(r'{{v?cite(.*?)}}',re.DOTALL)
# Regular Expression to remove Punctuation
regExp4 = re.compile(r'[.,;_()"/\']',re.DOTALL)
# Regular Expression to remove [[file:]]
regExp5 = re.compile(r'\[\[file:(.*?)\]\]',re.DOTALL)
# Regular Expression to remove Brackets and other meta characters from title
regExp6 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/?]",re.DOTALL)
# Regular Expression to remove <..> tags from text
regExp10 = re.compile(r'<(.*?)>',re.DOTALL)
# Regular Expression to remove junk from text
regExp11 = re.compile(r"[~`!@#$%-^*+{\[}\]\|\\<>/\?]",re.DOTALL)

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
    text = re.sub(r'[^\x00-\x7F]+','', text)
    return text

def updateIndex(wordList,docID,t):
    for word in wordList:
        # word = regExp11.sub(' ',word)
        word = re.sub(r'[^\x00-\x7F]+','', word)
        word = word.strip()
        
        if word.isalnum() and len(word)>=3 and stopwords[word]!=1:
            # Stemming the Words

            if word in stemCache.keys():
                word = stemCache[word] 
            else: 
                stemCache[word] = ps.stem(word)
                word = stemCache[word]

            # word = ps.stem(word)
            if stopwords[word]!=1:
                if word in invertedIndex:
                    if docID in invertedIndex[word]:
                    	if t in invertedIndex[word][docID]:
                    		invertedIndex[word][docID][t] += 1
                    	else:
                    		invertedIndex[word][docID][t] = 1
                    else:
                    	invertedIndex[word][docID] = {t:1}
                else:
                	invertedIndex[word] = dict({docID:{t:1}})

def processTitle(text,docID):
    text = cleanText(text)
    # stop_words = set(stopwords.words('english'))
    words = text.split()
    words = [regExp6.sub(' ',word) for word in words if word.isalnum() and stopwords[word]!=1]
    updateIndex(words,docID,"t")

def tokenise(data):                                                 #Tokenise
    tokenisedWords=re.findall("\d+|[\w]+",data)
    # tokenisedWords=re.findall("[0-9a-z]+",data)
    tokenisedWords=[key for key in tokenisedWords]
    # tokenisedWords = data.split()
    return tokenisedWords

def findExternalLinks(data):
    links=[]
    lines = data.split("==external links==")
    if len(lines)>1:
        lines=lines[1].split("\n")
        for i in range(len(lines)):
            if '* [' in lines[i] or '*[' in lines[i]:
                word=""
                temp=lines[i].split(' ')
                word=[key for key in temp if 'http' not in temp]
                word=' '.join(word)
                links.append(word)
    links=tokenise(' '.join(links))
    # links = stopWords(links)
    # links= stemmer(links)

    # temp=defaultdict(int)
    # for key in links:
    #     temp[key]+=1
    # links=temp
    return links

def findInfoBoxTextCategory(data):                                        #find InfoBox, Text and Category
    info=[]
    bodyText=[]
    category=[]
    links=[]
    flagtext=1
    lines = data.split('\n')
    infobox_done = False
    for i in range(len(lines)):
        if '{{infobox' in lines[i] and not infobox_done:
            flag=0
            temp=lines[i].split('{{infobox')[1:]
            info.extend(temp)
            while True:
                # print(lines[i])
                if i>=len(lines):
                    break
                if '{{' in lines[i]:
                    count=lines[i].count('{{')
                    flag+=count
                if '}}' in lines[i]:
                    count=lines[i].count('}}')
                    flag-=count
                if flag<=0:
                    break
                i+=1
                if i<len(lines):
                    info.append(lines[i])
            infobox_done=True

        elif flagtext:
            if '[[category' in lines[i] or '==external links==' in lines[i]:
                flagtext=0
            else:   
                bodyText.append(lines[i])
                
        else:
            if "[[category" in lines[i]:
                try:
                    d = lines[i].split(":")[1]
                    # print(d)
                    d=d[:-2]
                    # print(d)
                    category.append(d)
                    # line = data.split("[[category:")
                    # if len(line)>1:
                    #     category.extend(line[1:-1])
                    #     temp=line[-1].split(']]')
                    #     category.append(temp[0])
                except:
                    pass

    category=tokenise(' '.join(category))
    # category = stopWords(category)
    # category= stemmer(category)
            
    info=tokenise(' '.join(info))
    # info = stopWords(info)
    # info= stemmer(info)

    bodyText=tokenise(' '.join(bodyText))
    # bodyText = stopWords(bodyText)
    # bodyText= stemmer(bodyText)

    return info, bodyText, category

def writeIndexToFiles():
    f = open(pathToIndexFile,"w")
    for key,val in sorted(invertedIndex.items()):
        s =str(key)+"="
        for k,v in sorted(val.items()):
            s += str(k) + ":"
            for k1,v1 in v.items():
                s = s + str(k1) + str(v1) + "#"
            s = s[:-1]+","
        f.write(s[:-1]+"\n")
    f.close()

def processText(data,docID):
    data = data.lower()                                               #Case Folding
    # data = cleanText(data)
    externalLinks = findExternalLinks(data)
    data = data.replace('_',' ').replace(',',' ')
    infoBox, bodyText, category = findInfoBoxTextCategory(data)                      #Tokenisation
    # print("--------------------------Category--------------------------")
    # print(category)
    # print()
    # print("--------------------------INFOBOX--------------------------")
    # print(infoBox)
    # print()
    # print("--------------------------EXTERNAL--------------------------")
    # print(externalLinks)
    # print()
    # print("--------------------------BODYTEXT--------------------------")
    # print(bodyText)

    updateIndex(bodyText,docID,"b")
    updateIndex(category,docID,"c")
    updateIndex(infoBox,docID,"i")
    updateIndex(externalLinks,docID,"l")

    if docID%limit == 0:
        f = open(pathToIndexFile+"/"+str(docID),"w")
        for key,val in sorted(invertedIndex.items()):
            s =str(key)+"="
            for k,v in sorted(val.items()):
                s += str(k) + ":"
                for k1,v1 in v.items():
                    s = s + str(k1) + str(v1) + "#"
                s = s[:-1]+","
            f.write(s[:-1]+"\n")
        f.close()
        invertedIndex.clear()
        stemCache.clear()
        # print("Processed doc "+str(docID))
  
class WikiDataHandler(ContentHandler):
    def __init__(self):
        self.docID = 0
        # self.buffer = ""
        self.contentType = ""
        self.title = ""
        self.pageTitle = ""
        self.text = ""
        self.id = ""
        self.flag = False
    
    def startElement(self,element,attributes):
        if element == "title":
            self.contentType = "title"
            # self.buffer = ""
            self.title = ""
            self.flag=True
        if element == "page":
            self.docID += 1
        if element == "text":
            self.contentType = "text"
            # self.buffer = ""
            self.text = ""
       	if element == "id" and self.flag:
            self.contentType = "id"
       		# self.buffer = ""
            self.id = ""
    
    def endElement(self,element):
        if element == "title":
            # print("*******TITLE*******")
            # print(self.title)
            processTitle(self.title,self.docID)
            self.pageTitle = self.title
            # self.buffer = ""
            self.title=""
            self.contentType = ""
        elif element == "text":
            # self.buffer = ""
            processText(self.text,self.docID)
            self.text = ""
            self.contentType = ""
        elif element == "id" and self.flag:
            try:
                documentTitleMapping.write(str(self.docID)+"#"+self.pageTitle+":"+self.id+"\n")
            except:
                documentTitleMapping.write(str(self.docID)+"#"+self.pageTitle.encode('utf-8')+":"+self.id.encode('utf-8')+"\n")
            self.flag = False
            self.id = ""
            self.contentType = ""
            # self.buffer = ""
            
    def characters(self,content):
        if self.contentType == "text":
            self.text += content
        elif self.contentType == "title":
            self.title += content
        elif self.contentType == "id":
            self.id += content
        # self.buffer = self.buffer + content

print("Parsing...")
start = timeit.default_timer()
parse(sys.argv[1],WikiDataHandler())
stop = timeit.default_timer()
print("Time taken for Parsing:",stop-start," seconds.")
mins = float(stop-start)/float(60)
print( "Time taken for Parsing:",mins," Minutes.")
hrs = float(mins)/float(60)
print( "Time taken for Parsing:",hrs," Hours.")
# writeIndexToFiles()
print( "DONE!")

