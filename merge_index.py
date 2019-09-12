import os,sys
from os.path import isfile, join
import timeit
from collections import defaultdict
from heapq import heapify, heappush, heappop

indexFolder = "./merged_index/"
index_file_count = 0
secondary_index = {}
chunk_size = 100000

index_files_location = "./indexFiles/" 
index_files = [join(index_files_location,f) for f in os.listdir(index_files_location) if isfile(join(index_files_location, f))]
no_of_index_file = len(index_files)
is_completed = [False for i in range(no_of_index_file)]

file_pointers = {}
current_row_of_file = {}
k_way_heap = list()
words = {}
total = 0
invertedIndex = defaultdict()


def update_primary_index():
    global index_file_count
    update_secondary = True
    index_file_count = index_file_count + 1
    fileName = indexFolder + "index" + str(index_file_count) + ".txt"
    fp = open(fileName,"w")
    for i in sorted(invertedIndex):
        if update_secondary:
            secondary_index[i] = index_file_count
            update_secondary = False
        
        toWrite = str(i) + "=" + invertedIndex[i] + "\n"
        fp.write(toWrite)

def update_secondary_index():
	fileName = indexFolder + "secondary_index.txt"
	fp = open(fileName,"w")
	for i in sorted(secondary_index):
		toWrite = str(i) + " " + str(secondary_index[i]) + "\n"
		fp.write(toWrite)

start = timeit.default_timer()

for i in range(no_of_index_file):
    is_completed[i] = True
    try:
        file_pointers[i] = open(index_files[i],"r")
    except:
        print("problem in opening file ")
    current_row_of_file[i] = file_pointers[i].readline()
    words[i] = current_row_of_file[i].strip().split("=")
    if words[i][0] not in k_way_heap:
        heappush(k_way_heap,words[i][0])

while is_completed.count(False) != no_of_index_file:
    total = total + 1
    word = heappop(k_way_heap)
    for i in range(no_of_index_file):
        if is_completed[i] and words[i][0] == word:
            if word not in invertedIndex:
                invertedIndex[word] = words[i][1]
            else:
                invertedIndex[word] += ","+words[i][1]

            current_row_of_file[i] = file_pointers[i].readline().strip()

            if current_row_of_file[i]:
                words[i] = current_row_of_file[i].split("=")
                if words[i][0] not in k_way_heap:
                    heappush(k_way_heap,words[i][0])
            else:
                is_completed[i] = False
                file_pointers[i].close()
                # os.remove(index_files[i])
    if total >= chunk_size:
        total = 0
        update_primary_index()
        invertedIndex.clear()
    
update_primary_index()
update_secondary_index()

stop = timeit.default_timer()

print ("Time for Merging:",stop-start," seconds.")
mins = float(stop-start)/float(60)
print ("Time for Merging:",mins," Minutes.")
hrs = float(mins)/float(60)
print ("Time for Merging:",hrs," Hours.")
print ("Check the External File(s) Now!")
