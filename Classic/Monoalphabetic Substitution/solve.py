import re
import string
import random
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
	crib_words = []
	min_length_words = filter(lambda x:len(x)>min_length,words)
	min_repeat_words = filter(lambda x:(len(x)-len(set(x)))>min_repeats,min_length_words)
	for word in min_repeat_words:
		pattern,letters = crib_pattern(word)
		for hit in re.findall(pattern,data):
			if len(hit) != len(set(hit)): continue # capture groups must be distinct
			mapping=dict(zip(letters,hit))
			crib_words.append((word,crib_template(mapping),mapping))
			break
	return crib_words

def crib_pattern(word):
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

def crib_template(crib_mapping):
	alphabet = ''
	for letter in string.uppercase:
		entry = crib_mapping.get(letter)
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
	elements+= [([name],template,mapping) for name,mapping,template in cribs]
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
	prefix_trie = {}
	for word in words:
		level = prefix_trie
		for letter in word: level=level.setdefault(letter,{})
		level['words']=level.get('words',[])+[word]
	return prefix_trie

def trie_prefix(prefix_trie, data):
	words = []
	level = prefix_trie
	for letter in data:
		level=level.get(letter)
		if level is None: break
		words.extend(level.get('words',[]))
	words = words[::-1] # reverse to use largest words first
	return words

def crackMonoalphabeticCipher(words, data):
	global mono_freqs,prefix_trie
	mono_freqs = calc_frequencies(data)
	prefix_trie = trie_create(words)

	crib_words = find_cribs(words, data)
	cribs = maximize_cribs(crib_words)

	key = None
	while key is None:
		for names,template,mapping in cribs:
			print('testing potential crib(s): %s'%(', '.join(names)))
			key = crackMonoalphabeticCrib(words, data, template, length_cap=500)
			if key is not None: break
	subdata = data.translate(string.maketrans(key,string.uppercase))
	print('"%s" => %s'%(key,subdata))
	print ' '.join(words_fitness(subdata, length_cap=None)[1])
	return key,subdata

def crackMonoalphabeticCrib(words, data, crib_template, length_cap=200):
	alphabet = shuffle(crib_template)
	max_fitness,max_length = fitness(alphabet,data)
	while max_fitness < length_cap:
		next_fitness,next_length,alphabet = enhance(alphabet, data, crib_template, length_cap=length_cap, last_max=(max_fitness,max_length))
		print next_fitness,next_length,alphabet,data[:100].translate(string.maketrans(alphabet,string.uppercase))
		if next_fitness == -1: return # max_fitness,max_length = fitness(alphabet, data)
		if next_fitness <= max_fitness: continue
		max_fitness = next_fitness
		max_length = next_length
	return alphabet

def enhance(alphabet, data, crib_template, length_cap=200, last_max=(-1,0)):
	swap = lambda x,y:x.replace(y[0],'-').replace(y[1],y[0]).replace('-',y[1])
	indices = [i for i in xrange(len(alphabet)) if crib_template[i]=='-']
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
			ptxt = data[:100].translate(string.maketrans(max_alphabet,string.uppercase))
			readable = ' '.join(words_fitness(ptxt)[1]+[ptxt[max_length:]])
			print('enhance failed; randomizing at %.3f: "%s" => %s'%(max_fitness,max_alphabet,readable))
		max_alphabet = shuffle(crib_template)
		max_fitness = -1
		max_length = 0
	return (max_fitness,max_length,max_alphabet)

def fitness(alphabet, data, length_cap=200):
	fitness = 1
	for letter,guess in zip(alphabet,string.uppercase):
		fitness *= (1 - abs(mono_freqs.get(letter,0) - english_freqs.get(guess,0.0)))**4
	ptxt = data[:length_cap].translate(string.maketrans(alphabet,string.uppercase))
	maxlen,maxwords = words_fitness(ptxt,length_cap=length_cap)
	if maxlen > 0: fitness *= maxlen
	if len(maxwords): fitness *= sum(map(lambda x:x**2,map(len,maxwords)))/float(len(maxwords))
	fitness /= 4.0
	return (fitness,maxlen)

def words_fitness(data, prefix='', length_cap=200, last=''):
	max_words = []
	max_length = 0
	for word in trie_prefix(prefix_trie, data[len(prefix):]):
		if word == last: continue
		segment = prefix+word
		if not data.startswith(segment): continue
		if len(segment) > max_length: max_length,max_words = len(segment),[word]
		if length_cap and max_length >= length_cap: break
		pre_length,pre_words = words_fitness(data, segment, length_cap, last=word)
		if pre_length > max_length: max_length,max_words = pre_length,[word]+pre_words
		elif pre_length == max_length and pre_words < len(max_words)+1:
			max_length,max_words = pre_length,[word]+pre_words
		if length_cap and max_length >= length_cap: break
	return (max_length,max_words)

one_letter_words = set(['A','I'])
two_letter_words = set(['AI', 'AM', 'AN', 'AS', 'AT', 'IF', 'IN', 'IS', 'IT', 'OF', 'ON', 'OR', 'UN', 'UP', 'US', 'BE', 'BY', 'GO', 'HI', 'NO', 'PI', 'SO', 'TO']) # https://en.wikipedia.org/wiki/Two-letter_English_words

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
	words = load_dictionary('/usr/share/dict/american-english')
	data = 'GUGFAHTHIYWGPGTHGKXIOSHHIYTUHKSOPTUVOFSGUTUVPXGUHYIXQTUVGUWQIWSFTUVWGPGLTPEPESVIGFIYWTHOIZSXTUVJHSYJFTUYIXQGPTIUHJVVSHPTUVOIUOFJHTIUHGUWHJKKIXPTUVWSOTHTIUQGDTUVWGPGGUGFAHTHEGHQJFPTKFSYGOPHGUWGKKXIGOESHSUOIQKGHHTUVWTZSXHSPSOEUTRJSHJUWSXGZGXTSPAIYUGQSHTUWTYYSXSUPCJHTUSHHHOTSUOSGUWHIOTGFHOTSUOSWIQGTUHWGPGQTUTUVTHGKGXPTOJFGXWGPGGUGFAHTHPSOEUTRJSPEGPYIOJHSHIUQIWSFTUVGUWDUILFSWVSWTHOIZSXAYIXKXSWTOPTZSXGPESXPEGUKJXSFAWSHOXTKPTZSKJXKIHSHCJHTUSHHTUPSFFTVSUOSOIZSXHWGPGGUGFAHTHPEGPXSFTSHESGZTFAIUGVVXSVGPTIUYIOJHTUVIUCJHTUSHHTUYIXQGPTIUTUHPGPTHPTOGFGKKFTOGPTIUHHIQSKSIKFSWTZTWSWGPGGUGFAHTHTUPIWSHOXTKPTZSHPGPTHPTOHSBKFIXGPIXAWGPGGUGFAHTHSWGGUWOIUYTXQGPIXAWGPGGUGFAHTHOWGSWGYIOJHSHIUWTHOIZSXTUVUSLYSGPJXSHTUPESWGPGGUWOWGIUOIUYTXQTUVIXYGFHTYATUVSBTHPTUVEAKIPESHSHKXSWTOPTZSGUGFAPTOHYIOJHSHIUGKKFTOGPTIUIYHPGPTHPTOGFQIWSFHYIXKXSWTOPTZSYIXSOGHPTUVIXOFGHHTYTOGPTIULETFSPSBPGUGFAPTOHGKKFTSHHPGPTHPTOGFFTUVJTHPTOGUWHPXJOPJXGFPSOEUTRJSHPISBPXGOPGUWOFGHHTYATUYIXQGPTIUYXIQPSBPJGFHIJXOSHGHKSOTSHIYJUHPXJOPJXSWWGPGGFFGXSZGXTSPTSHIYWGPGGUGFAHTHWGPGTUPSVXGPTIUTHGKXSOJXHIXPIWGPGGUGFAHTHGUWWGPGGUGFAHTHTHOFIHSFAFTUDSWPIWGPGZTHJGFTMGPTIUGUWWGPGWTHHSQTUGPTIUPESPSXQWGPGGUGFAHTHTHHIQSPTQSHJHSWGHGHAUIUAQYIXWGPGQIWSFTUV'
	crackMonoalphabeticCipher(words, data)
