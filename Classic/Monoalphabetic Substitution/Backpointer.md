~~~python
def find_cribs_backref(words, data, min_length=8, min_repeats=3):
	crib_words = []
	words = filter(lambda x:len(x)>min_length,words)
	words = filter(lambda x:(len(x)-len(set(x)))>min_repeats,words)
	for word in words:
		pattern,letters = backref_pattern(word)
		for hit in re.findall(pattern,data):
			if len(hit) != len(set(hit)): continue # capture groups must be distinct
			mapping=dict(zip(letters,hit))
			crib_words.append((word,backref_template(mapping),mapping))
			break
	return crib_words
~~~

This function scanned through the ciphertext to find letter patterns from *interesting* words (featuring repeated letters) with 4 steps:

1. Find all words with 8+ characters and 3+ character repeats (ex: 'CODEPENDENT')
1. Generate a regular expression pattern (ex: r'(.)(.)(.)(.)(.)\4(.)\3\4\6(.)')
1. Find all pattern matches in the ciphertext (ex: [('ZSHPGPTHPTO','TUHPGPTHPTO'])
1. Eliminate any non-distinct capture groups (ex: charmap('TUHPGPTHPTO') => {'C':'T','N':'T'})

The 4th step was necessary because the [capture groups](http://www.rexegg.com/regex-capture.html) used to identify specific [backreferences](http://www.regular-expressions.info/backref.html) (e.g. the 6th character matches the 4th character for 'CODEPENDENT') did not prohibit capture group overlap (e.g. the 1st and 2nd character should not match for 'CODEPENDENT'). This felt [inelegant](https://en.wikipedia.org/wiki/No_Silver_Bullet#Summary), but regular expression didn't seem to offer an easy fix to "capture everything EXCEPT the text in capture group 1". Fortunately, [oren](https://github.com/OrenLeaffer) came up with a clever approach.

The two key insights were translating the ciphertext into single-character [backpointers](http://www.commandlinefanatic.com/cgi-bin/showarticle.cgi?article=art001) and capture groups using index-based character ranges. The first insight means converting each character of the text into either 0 ("we haven't seen it before") or the distance to last sighting ("we saw it 2 characters ago"). For example, `CODEPENDENT` turns into `[0, 0, 0, 0, 0, 2, 0, 5, 3, 3, 0]` since the 2nd 'E' (index 6) occurs 2 units after the 1st 'E' (index 4). The second insight allows converting the backpointer array into a [necessary & sufficient](https://en.wikipedia.org/wiki/Necessary_and_sufficient_condition) regular expression by replacing each non-zero with the same ASCII value (e.g. 2 => '\x02') and replacing each zero with an index-based character range (e.g., the 3rd chracter ('D') becomes r'[\x00\x03-\xff]'). That is pretty clever in that it allows the 3rd character to have any value **except** the values in the 1st character (which would be '\x02') or the 2nd character (which would be '\x01').

~~~python
def find_cribs_backptr(words, data, min_length=8, min_repeats=3):
	# thanks to https://github.com/OrenLeaffer the backptr method
	crib_words = []
	words = filter(lambda x:len(x)>min_length,words)
	words = filter(lambda x:(len(x)-len(set(x)))>min_repeats,words)
	dataref = ''.join(chr(c) for c in backptr_pattern(data))
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
~~~

Perhaps unsurprisingly, the backpointer solution is slower than the backreference when the wordlist is large relative to the ciphertext and the text is highly differentiated (not one letter repeated 1000 times). This cost isn't from the relative complexity of the expressions though, but instead the cost of generating them (per the benchmarks below shows). Thanks Oren!

~~~python
>>> timeit.timeit("import re;re.compile('[\\x00\\x01-\\xff][\\x00\\x02-\\xff][\\x00\\x03-\\xff][\\x00\\x04-\\xff][\\x00\\x05-\\xff]\\x02[\\x00\\x07-\\xff]\\x05\\x03\\x03[\\x00\\x0b-\\xff]')")
1.0376930236816406
>>> timeit.timeit("import re;re.compile('(.)(.)(.)(.)(.)\4(.)\3\4\6(.)')")
1.0382349491119385

>>> timeit.timeit("import re;re.findall('[\\x00\\x01-\\xff][\\x00\\x02-\\xff][\\x00\\x03-\\xff][\\x00\\x04-\\xff][\\x00\\x05-\\xff]\\x02[\\x00\\x07-\\xff]\\x05\\x03\\x03[\\x00\\x0b-\\xff]','%s')"%data,number=100000)
9.716220140457153
>>> timeit.timeit("import re;re.findall('(.)(.)(.)(.)(.)\4(.)\3\4\6(.)','%s')"%data,number=100000)
9.648783922195435

>>> timeit.timeit("import solve;solve.backptr_regex('CODEPENDENT')")
12.500058889389038
>>> timeit.timeit("import solve;solve.backref_regex('CODEPENDENT')")
6.2223169803619385
~~~
