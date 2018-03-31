#!/usr/bin/python3

import os
import sys
import gensim.models
import pickle

# constants
window_len = 1
input_dir = "./preprocessed/"
output_dir = "./output/"
dimensionality = 50

# map each time window to a sentence list and an embedding model
sentence_sets = {}
models = {}

# parse args
if len(sys.argv) <= 3 :
	print("Usage: %s [start_year] [end_year] [window_len]" % sys.argv[0], file = sys.stderr)
	sys.exit(3)
start_year = int(sys.argv[1])
end_year = int(sys.argv[2])
window_len = int(sys.argv[3])

if end_year < start_year :
	print("that's not going to work", file = sys.stderr)
	sys.exit(2)

# make models
print("making models", end = "\r")
year_range = end_year + 1 - start_year
i = 1
for year in range(start_year, end_year + 1) :
	try :
		input = open(input_dir + str(year) + ".txt")
		
		# split by sentences
		text = input.read()
		text = text.replace("!", ".")
		text = text.replace("?", ".")
		sentences = text.split(".")
		sentences = [sent.split() for sent in sentences] # tokenize
		
		# add these sentences to every set in the time window
		for y in range(year, year + window_len) :
			if y not in sentence_sets :
				sentence_sets[y] = []
			sentence_sets[y] += sentences
	
	except :
		print("Could not find data for " + str(year) + " (" + str(year) + ".txt); skipping")

	# make embedding model regardless of whether data for this year was found (use windows)
	# however, there must be something in the set or else this won't work; fail if empty
	if len(sentence_sets[year]) == 0 :
		print("No data in window for " + str(year), file = sys.stderr)
		sys.exit(1)
	else :
		model = gensim.models.Word2Vec(sentence_sets[year], size = dimensionality, window = 5, min_count = 5, workers = 4)
		model.save(output_dir + str(year) + "+" + str(window_len) + ".word2vec")
		
		# clear sentence set and model from memory
		#del(model)
	del(sentence_sets[year])
	
	print("making models (%d/%d)" % (i, year_range), end = "\r")
	i += 1
print()
del(sentence_sets)

# consider only words that are in all models
print("finding overlap...", end = "\r")
base = list(models.values())[0] # there is probably a better way to do this but this gets the first model
wordset = []
i = 1
p = 0
for word in base :
	add = True
	for model in models :
		if word not in model :
			add = False
			break
	if add :
		wordset |= {word}
	
	i += 1
	if (100 * i // len(base)) > p :
		p = 100 * i // len(base)
		print("finding overlap (%d%%)" % (p), end = "\r")
print()

# save overlap set
output = open(output_dir + "overlap-%s-%s+%s" % (sys.argv[1], sys.argv[2], sys.argv[3]), "wb")
pickle.dump(wordset, output)
output.close()

# go through all candidate words
print("building neighbor lists...")
word_scores = {}
for word in wordset :
	top_tens_union = set()
	for model in models : # generate the set union over all models of the top ten lists
		top_tens_union |= set(model.most_similar(positive=[word], topn=10))
	
	# test metric: union cardinality
	word_scores[word] = len(top_tens_union)

# sort list
print("sorting...")
drifters = sorted(word_scores, key=word_scores.get)
del(word_scores)

# save sorted list
output = open(output_dir + "sorted-%s-%s+%s" % (sys.argv[1], sys.argv[2], sys.argv[3]), "wb")
pickle.dump(drifters, output)
output.close()

print()
print("best:")
for word in drifters[:30] :
	print(word)