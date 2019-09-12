# WikiPedia Search Engine

## Step 1 : Parsing the Data

To parse the data, run the file "parser.py"
To run the file, the syntax is "python3 parser.py <path-to-dump-file> <path-to-index-folder>"
It'll parse the whole dump and file the index files in the index files directory.
It also creates the document to title mapping file in the current directory named 'docTitleMap.txt' which will be used by the search module later.

## Step 2 : Merging the Indexes and Creating Secondary Indexes

To merge the individual index files and create the secondary index, run the file "merge_index.py"
There isn't any need for command line arguments. It takes the index files from index files directory and populates the 'merged_index' directory with indexes of given chunk size and creates a secondary index named 'secondary_index.txt' in the same folder.

## Step 3 : Running the Search Engine

To search for queries, run the file 'search.py'. It loads the index from 'merged_index' (both primary and secondary).
It also uses the file 'docTitleMap.txt' to display titles corresponding to the docIDs.
After it loads up, it gives the user a prompt to enter the query. After that the result of query is displayed. (top 10 results).

For Field Queries, follow the format:
```
	f1:<query> f2:<query> ...
```	
where f1,f2 are fields : title, body, ref, infobox, category, link

