# assigning probility of happening some letters after or before some other letters
### This program get a dictionary of firstnames and lastnames with the count of them. This script use `Ngram` to findout what is the probabilty of happening `za` after `re` or what is the probabilty of happening `osse` before `sein`. This script just produce another dictionary of them.
  
## prepare
write these in command prompt to install require packages  
`pip install nltk`  

## package function
### ngrams
	extract continuous sequences of words or symbols or tokens in a document

## start code
### import packages to script
`from nltk import ngrams` ----> 
`import tqdm` ----> 
`import json` ----> 

### read from lastname.txt or firstname.json
`all_fl_firstname=read_names_file('Firstname')` ----> 
`all_fl_lastname=read_names_file('Lastname')`
1. read just from Firstname
2. read from both firstname and lastname

### start determine probilities 
`start_determine_probs(all_fl_firstname, 'Firstname')` ----> 
`start_determine_probs(all_fl_lastname, 'Lastname')`

1. get fistname or lastname dictionary and type of name
2. build an object from assinging_probilities class and calculate probility
3. save 3 files of probilities

### small example
`all_fl_firstname=read_names_file('Firstname')` ----> 
`start_determine_probs(all_fl_firstname, 'Firstname')`

`all_fl_lastname=read_names_file('Lastname')`   ----> 
`start_determine_probs(all_fl_lastname, 'Lastname')`

1. get dictionary of firstname and their repetetion
2. start to make 3 files of probilities

3. get dictionary of lastname and firstname and their repetetion
2. start to make 3 files of probilities