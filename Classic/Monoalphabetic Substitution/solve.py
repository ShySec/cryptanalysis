#!/usr/bin/env python2
# thanks to https://github.com/OrenLeaffer for the find_cribs_backptr technique

import re
import time
import string
import random
import logging
import collections

english_freqs = {'a': 0.0817, 'c': 0.0278, 'b': 0.0149, 'e': 0.1270, 'd': 0.0425, 'g': 0.0202, 'f': 0.0223, 'i': 0.0697, 'h': 0.0609, 'k': 0.0077, 'j': 0.0015, 'm': 0.0241, 'l': 0.0403,
                 'o': 0.0751, 'n': 0.0675, 'q': 0.0009, 'p': 0.0193, 's': 0.0633, 'r': 0.0599, 'u': 0.0276, 't': 0.0906, 'w': 0.0236, 'v': 0.0098, 'y': 0.0197, 'x': 0.0015, 'z': 0.0007}
english_freqs = dict((k.upper(),v) for k,v in english_freqs.items())

def shuffle(template):
	alphabet = ''
	charset = list(set(string.uppercase).difference(template))
	random.shuffle(charset)
	for letter in template:
		if letter != '-': alphabet += letter
		else: alphabet += charset.pop()
	return alphabet

def find_cribs(words, data, min_length=8, min_repeats=3):
	if len(data) > 0: return find_cribs_backptr(words, data, min_length, min_repeats)
	return find_cribs_backref(words, data, min_length, min_repeats)

def find_cribs_backref(words, data, min_length=8, min_repeats=3):
	crib_words = []
	words = filter(lambda x:len(x)>min_length,words)
	words = filter(lambda x:(len(x)-len(set(x)))>min_repeats,words)
	for word in words:
		pattern,letters = backref_regex(word)
		for hit in re.findall(pattern,data):
			if len(hit) != len(set(hit)): continue # capture groups must be distinct
			mapping=dict(zip(letters,hit))
			crib_words.append((word,crib_template(mapping),mapping))
			break
	return crib_words

def backref_regex(word):
	expr = ''
	groups = {}
	mapping = []
	for letter in word:
		entry = groups.get(letter)
		if entry is not None: expr += '\\%d'%entry
		else:
			groups[letter] = len(groups)+1
			mapping.append(letter)
			expr += '(.)'
	return expr,mapping

def find_cribs_backptr(words, data, min_length=8, min_repeats=3):
	# thanks to https://github.com/OrenLeaffer the backptr method
	crib_words = []
	words = filter(lambda x:len(x)>min_length,words)
	words = filter(lambda x:(len(x)-len(set(x)))>min_repeats,words)
	dataref = backptr_string(data)
	for word in words:
		pattern,letters = backptr_regex(word)
		for hit in re.findall(pattern,dataref):
			index = dataref.find(hit)
			mapping=dict(zip(word,data[index:index+len(word)]))
			crib_words.append((word,crib_template(mapping),mapping))
			break
	return crib_words

def backptr_pattern(data):
	refs={}
	refdata=[]
	for index,letter in enumerate(data):
		ref=refs.get(letter,index)
		if index-ref>255: ref=index
		refdata.append(index-ref)
		refs[letter]=index
	return refdata

def backptr_string(data):
	return ''.join(chr(c) for c in backptr_pattern(data))

def backptr_regex(data):
	regex = ''
	groups = 1
	mapping = []
	bref = backptr_pattern(data)
	for index,ref in enumerate(bref):
		if ref > 0: regex += '\\x%02x'%ref
		else:
			regex += '[\\x00\\x%02x-\\xff]'%(index+1)
			mapping.append(data[index])
	return regex,mapping

def crib_template(mapping):
	alphabet = ''
	for letter in string.uppercase:
		entry = mapping.get(letter)
		if entry: alphabet += entry
		else: alphabet += '-'
	return alphabet

def maximize_cribs(cribs):
	elements=[]
	for name,template,mapping in cribs*2: # doubled to catch all pairings
		hit = False
		for index,element in enumerate(elements):
			emap,estrs = element
			combo = merge_crib_maps(emap, mapping)
			if combo is None: continue
			elements[index] = [combo,estrs+[name]]
			hit = True
		if not hit: elements.append([mapping,[name]])
	elements = [(list(set(estrs)),crib_template(emap),emap) for emap,estrs in elements]
	elements+= [([name],template,mapping) for name,template,mapping in cribs]
	elements = sorted(elements, key=lambda x:sum(map(len,x[0])),reverse=True)
	return elements

def merge_crib_maps(base, extension):
	combined={}
	for key in base.keys()+extension.keys():
		bvalue = base.get(key)
		evalue = extension.get(key)
		if   bvalue is None: combined[key]=evalue
		elif evalue is None: combined[key]=bvalue
		elif bvalue == evalue: combined[key]=evalue
		else: return # conflicting cribs
	return combined

def trie_create(words):
	trie = {}
	for word in words: trie_add(trie,word)
	return trie

def trie_add(trie, word):
	for letter in word: trie=trie.setdefault(letter,{})
	trie['words']=trie.get('words',[])+[word]

def trie_prefix(trie, data):
	words = []
	level = trie
	for letter in data:
		level=level.get(letter)
		if level is None: break
		words.extend(level.get('words',[]))
	words = words[::-1] # reverse to use largest words first
	return words

def trie_copy(trie):
	import copy
	return copy.deepcopy(trie)

def crackMonoalphabeticCipher(words, data):
	# precomputation
	global mono_freqs,prefix_trie
	mono_freqs = calc_frequencies(data)
	prefix_trie = trie_create(words)
	# cribs = likely plaintext chunks
	crib_words = find_cribs(words, data)
	cribs = maximize_cribs(crib_words)
	# start attack
	key = None
	s=time.time()
	while key is None:
		for names,template,mapping in cribs:
			print('testing potential crib(s): %s'%(', '.join(names)))
			key = crackMonoalphabeticCrib(words, data, template, length_cap=300)
			if key is not None: break
	e=time.time()
	subdata = data.translate(string.maketrans(key,string.uppercase))
	print('"%s" => %s'%(key,subdata))
	print(' '.join(segment_words(subdata, length_cap=None)[1]))
	print('execution time: %.3f'%(e-s))
	return key,subdata

def crackMonoalphabeticCrib(words, data, template, length_cap=200):
	alphabet = shuffle(template)
	max_fitness,max_length = fitness(alphabet,data)
	while max_length < length_cap:
		next_fitness,next_length,alphabet = enhance(alphabet, data, template, length_cap=length_cap, last_max=(max_fitness,max_length))
		logging.debug('fitness %.3f (length %d) "%s"',next_fitness,next_length,alphabet)
		if next_fitness == -1: return # max_fitness,max_length = fitness(alphabet, data)
		if next_fitness <= max_fitness: continue
		max_fitness = next_fitness
		max_length = next_length
	return alphabet

def enhance(alphabet, data, template, length_cap=200, last_max=(-1,0)):
	swap = lambda x,y:x.replace(y[0],'-').replace(y[1],y[0]).replace('-',y[1])
	indices = [i for i in xrange(len(alphabet)) if template[i]=='-']
	random.shuffle(indices)
	max_alphabet = alphabet
	last_fitness,last_length = last_max
	max_fitness,max_length = last_fitness,last_length
	for index in indices:
		letter = alphabet[index]
		for subindex in indices:
			if subindex == index: continue
			partner = alphabet[subindex]
			test_alphabet = swap(alphabet,[letter,partner])
			test_fitness,test_length = fitness(test_alphabet, data, length_cap=length_cap)
			if test_fitness <= max_fitness: continue
			max_alphabet = test_alphabet
			max_fitness = test_fitness
			max_length = test_length
		if max_fitness > last_fitness: break
	if max_fitness == last_fitness:
		if max_fitness >= 0:
			ptxt = data[:length_cap+20].translate(string.maketrans(max_alphabet,string.uppercase))
			plen,pwords=segment_words(ptxt)
			readable = '%s :: %s'%(pwords,ptxt[plen:])
			logging.info('enhance failed; randomizing at %.3f: "%s" => %s'%(max_fitness,max_alphabet,readable))
		max_alphabet = shuffle(template)
		max_fitness = -1
		max_length = 0
	return (max_fitness,max_length,max_alphabet)

def fitness(alphabet, data, length_cap=200):
	fitness = 1
	for letter,guess in zip(alphabet,string.uppercase):
		fitness *= (1 - abs(mono_freqs.get(letter,0) - english_freqs.get(guess,0.0)))**4
	ptxt = data[:length_cap+20].translate(string.maketrans(alphabet,string.uppercase))
	maxlen,maxwords = segment_words(ptxt,length_cap=length_cap)
	if maxlen > 0: fitness *= maxlen
	if len(maxwords): fitness *= sum(map(lambda x:x**2,map(len,maxwords)))
	fitness /= 4.0
	return (fitness,maxlen)

def segment_words(data, length_cap=200, last='', prefix_words=[], skip_at=-1, skippable=False):
	global prefix_trie
	if length_cap is None:
		length_cap = len(data)
		skippable = True
	if length_cap > len(data): length_cap = len(data)
	max_words = prefix_words
	max_length = 0
	if not data: return (max_length,max_words)
	for word in trie_prefix(prefix_trie, data):
		if word == last: continue
		word_len = len(word)
		if word_len >= max_length: max_length,max_words = word_len,prefix_words+[word]
		if max_length >= length_cap: break
		# recursively check the children of this word
		pre_length,pre_words = segment_words(data[word_len:], length_cap-word_len, last=word, prefix_words=prefix_words+[word], skip_at=skip_at-1, skippable=skippable)
		if pre_length+word_len > max_length: max_length,max_words = pre_length+word_len,pre_words
		if pre_length+word_len == max_length and len(pre_words)<len(max_words):
			max_length,max_words = pre_length+word_len,pre_words
		if max_length >= length_cap: break
		if pre_length>20: # limit backtracking
			if not skippable: break
			force_skip_at=len(pre_words)-len(prefix_words)-1
			skip_distance=sum(map(len,pre_words[len(prefix_words):]))
			logging.debug('unknown word at %s (%s)',data[skip_distance:][:40],pre_words[len(prefix_words):])
			skip_length,skip_words = segment_words(data[word_len:], length_cap-word_len, last=word, prefix_words=prefix_words+[word], skip_at=force_skip_at, skippable=skippable)
			if skip_length+word_len > max_length: max_length,max_words = skip_length+word_len,skip_words
			if skip_length+word_len == max_length and len(skip_words)<len(max_words):
				max_length,max_words = skip_length+word_len,skip_words
			if max_length >= length_cap: break
	# try to skip unknown words during backtrack
	if skippable and skip_at == 0:
		for skip in xrange(3,24):
			word = data[:skip]
			word_len = len(word)
			prefix_trie_bak = prefix_trie
			prefix_trie = trie_copy(prefix_trie)
			trie_add(prefix_trie,word)
			skip_length,skip_words = segment_words(data[word_len:], length_cap-word_len, last=word, prefix_words=[word], skippable=skippable)
			prefix_trie = prefix_trie_bak
			if skip_length<20: continue
			if skip_length+word_len >= max_length: max_length,max_words = skip_length+word_len,prefix_words+skip_words
			logging.info('added %s to dictionary (%s)',word,''.join(prefix_words[-3:]+['-',word,'-']+skip_words[1:4]))
			trie_add(prefix_trie, word)
			break
	return (max_length,max_words)

one_letter_words = set(['A','I'])
two_letter_words = set(['AI', 'AM', 'AN', 'AS', 'AT', 'IF', 'IN', 'IS', 'IT', 'OF', 'ON', 'OR', 'UN', 'UP', 'US', 'BE', 'BY', 'GO', 'HI', 'NO', 'PI', 'SO', 'TO', 'WE', 'ME']) # https://en.wikipedia.org/wiki/Two-letter_English_words

def load_dictionary(filename):
	words = filter(lambda x:x,open(filename).read().upper().split('\n'))
	words = filter(lambda word:all(c in string.uppercase for c in word),words)
	words = filter(lambda word:len(word)>1 or word in one_letter_words,words)
	words = filter(lambda word:len(word)!=2 or word in two_letter_words,words)
	return set(words)

def calc_frequencies(data):
	unigrams = collections.defaultdict(int)
	for i in xrange(0,len(data),1): unigrams[data[i]] += 1
	for i in unigrams: unigrams[i] /= float(len(data))
	return unigrams

if __name__ == '__main__':
	#logging.getLogger().setLevel(logging.DEBUG)
	words = load_dictionary('/usr/share/dict/american-english')
	data = 'GUGFAHTHIYWGPGTHGKXIOSHHIYTUHKSOPTUVOFSGUTUVPXGUHYIXQTUVGUWQIWSFTUVWGPGLTPEPESVIGFIYWTHOIZSXTUVJHSYJFTUYIXQGPTIUHJVVSHPTUVOIUOFJHTIUHGUWHJKKIXPTUVWSOTHTIUQGDTUVWGPGGUGFAHTHEGHQJFPTKFSYGOPHGUWGKKXIGOESHSUOIQKGHHTUVWTZSXHSPSOEUTRJSHJUWSXGZGXTSPAIYUGQSHTUWTYYSXSUPCJHTUSHHHOTSUOSGUWHIOTGFHOTSUOSWIQGTUHWGPGQTUTUVTHGKGXPTOJFGXWGPGGUGFAHTHPSOEUTRJSPEGPYIOJHSHIUQIWSFTUVGUWDUILFSWVSWTHOIZSXAYIXKXSWTOPTZSXGPESXPEGUKJXSFAWSHOXTKPTZSKJXKIHSHCJHTUSHHTUPSFFTVSUOSOIZSXHWGPGGUGFAHTHPEGPXSFTSHESGZTFAIUGVVXSVGPTIUYIOJHTUVIUCJHTUSHHTUYIXQGPTIUTUHPGPTHPTOGFGKKFTOGPTIUHHIQSKSIKFSWTZTWSWGPGGUGFAHTHTUPIWSHOXTKPTZSHPGPTHPTOHSBKFIXGPIXAWGPGGUGFAHTHSWGGUWOIUYTXQGPIXAWGPGGUGFAHTHOWGSWGYIOJHSHIUWTHOIZSXTUVUSLYSGPJXSHTUPESWGPGGUWOWGIUOIUYTXQTUVIXYGFHTYATUVSBTHPTUVEAKIPESHSHKXSWTOPTZSGUGFAPTOHYIOJHSHIUGKKFTOGPTIUIYHPGPTHPTOGFQIWSFHYIXKXSWTOPTZSYIXSOGHPTUVIXOFGHHTYTOGPTIULETFSPSBPGUGFAPTOHGKKFTSHHPGPTHPTOGFFTUVJTHPTOGUWHPXJOPJXGFPSOEUTRJSHPISBPXGOPGUWOFGHHTYATUYIXQGPTIUYXIQPSBPJGFHIJXOSHGHKSOTSHIYJUHPXJOPJXSWWGPGGFFGXSZGXTSPTSHIYWGPGGUGFAHTHWGPGTUPSVXGPTIUTHGKXSOJXHIXPIWGPGGUGFAHTHGUWWGPGGUGFAHTHTHOFIHSFAFTUDSWPIWGPGZTHJGFTMGPTIUGUWWGPGWTHHSQTUGPTIUPESPSXQWGPGGUGFAHTHTHHIQSPTQSHJHSWGHGHAUIUAQYIXWGPGQIWSFTUV'
	crackMonoalphabeticCipher(words, data)
