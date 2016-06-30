# Cracking Monoalphabetic Substitution

[Monoalphabetic Substitution](https://en.wikipedia.org/wiki/Substitution_cipher#Simple_substitution) ciphers use a substitution alphabet to map plaintext characters to ciphertext characters. Although many common forms use a simple function to create the substitution alphabet (i.e., [Caesar Cipher](https://en.wikipedia.org/wiki/Caesar_cipher) offsets the alphabet), the general case may create arbitrarily mixed substitution alphabets (aka deranged alphabets). Given the 15 [oktillion](https://en.wikipedia.org/wiki/Names_of_large_numbers#Proposals_for_new_naming_system) alphabet orderings (21[!](https://en.wikipedia.org/wiki/Factorial)), can cryptanalysis defeat a monoalphabetic substitution cipher with a deranged alphabet?

### Monoalphabetic Encryption/Decryption

We can use an example to illustrate the operation of the Monoalphabetic Substitution and generating a test case for analysis. We select a [Random](https://en.wikipedia.org/wiki/Special:Random) Wikipedia article with sufficient length (1000+ characters) and few proper nouns for simpler cryptanalysis. The introduction for [Data Analysis](https://en.wikipedia.org/wiki/Data_analysis) is a good match for our criteria (and nicely related).

Step 1. Generate the (secret) substitution alphabet:

~~~python
import string
import random
alphabet=list(string.uppercase)
random.shuffle(alphabet)
alphabet=''.join(alphabet)
~~~

<snip/>

&nbsp;

Step 2. Prepare text from Wikipedia:

~~~python
import re

# intro text from https://en.wikipedia.org/wiki/Data_analysis
data='''Analysis of data is a process of inspecting, cleaning, transforming, and modeling data with the goal of discovering useful information, suggesting conclusions, and supporting decision-making. Data analysis has multiple facts and approaches, encompassing diverse techniques under a variety of names, in different business, science, and social science domains.\n\nData mining is a particular data analysis technique that focuses on modeling and knowledge discovery for predictive rather than purely descriptive purposes. Business intelligence covers data analysis that relies heavily on aggregation, focusing on business information. In statistical applications, some people divide data analysis into descriptive statistics, exploratory data analysis (EDA), and confirmatory data analysis (CDA). EDA focuses on discovering new features in the data and CDA on confirming or falsifying existing hypotheses. Predictive analytics focuses on application of statistical models for predictive forecasting or classification, while text analytics applies statistical, linguistic, and structural techniques to extract and classify information from textual sources, a species of unstructured data. All are varieties of data analysis.\n\nData integration is a precursor to data analysis, and data analysis is closely linked to data visualization and data dissemination. The term data analysis is sometimes used as a synonym for data modeling.'''

# cleanup the input text
data = re.sub('[^\w ]','',data) # remove all non-alphanumeric letters
data = data.upper() # uppercase all text
~~~

&nbsp;

Step 3. Encrypt with the substitution alphabet from step 1 ("GCOWSYVETNDFQUIKRXHPJZLBAM"):

~~~python
ctxt = data.translate(string.maketrans(string.uppercase,alphabet)) # GUGFAHTHIYWGPGTHGKXIOSHHIYTUHKSOPTUVOFSGUTUVPXGUHYIXQTUVGUWQIWSFTUVWGPGLTPEPESVIGFIYWTHOIZSXTUVJHSYJFTUYIXQGPTIUHJVVSHPTUVOIUOFJHTIUHGUWHJKKIXPTUVWSOTHTIUQGDTUVWGPGGUGFAHTHEGHQJFPTKFSYGOPHGUWGKKXIGOESHSUOIQKGHHTUVWTZSXHSPSOEUTRJSHJUWSXGZGXTSPAIYUGQSHTUWTYYSXSUPCJHTUSHHHOTSUOSGUWHIOTGFHOTSUOSWIQGTUHWGPGQTUTUVTHGKGXPTOJFGXWGPGGUGFAHTHPSOEUTRJSPEGPYIOJHSHIUQIWSFTUVGUWDUILFSWVSWTHOIZSXAYIXKXSWTOPTZSXGPESXPEGUKJXSFAWSHOXTKPTZSKJXKIHSHCJHTUSHHTUPSFFTVSUOSOIZSXHWGPGGUGFAHTHPEGPXSFTSHESGZTFAIUGVVXSVGPTIUYIOJHTUVIUCJHTUSHHTUYIXQGPTIUTUHPGPTHPTOGFGKKFTOGPTIUHHIQSKSIKFSWTZTWSWGPGGUGFAHTHTUPIWSHOXTKPTZSHPGPTHPTOHSBKFIXGPIXAWGPGGUGFAHTHSWGGUWOIUYTXQGPIXAWGPGGUGFAHTHOWGSWGYIOJHSHIUWTHOIZSXTUVUSLYSGPJXSHTUPESWGPGGUWOWGIUOIUYTXQTUVIXYGFHTYATUVSBTHPTUVEAKIPESHSHKXSWTOPTZSGUGFAPTOHYIOJHSHIUGKKFTOGPTIUIYHPGPTHPTOGFQIWSFHYIXKXSWTOPTZSYIXSOGHPTUVIXOFGHHTYTOGPTIULETFSPSBPGUGFAPTOHGKKFTSHHPGPTHPTOGFFTUVJTHPTOGUWHPXJOPJXGFPSOEUTRJSHPISBPXGOPGUWOFGHHTYATUYIXQGPTIUYXIQPSBPJGFHIJXOSHGHKSOTSHIYJUHPXJOPJXSWWGPGGFFGXSZGXTSPTSHIYWGPGGUGFAHTHWGPGTUPSVXGPTIUTHGKXSOJXHIXPIWGPGGUGFAHTHGUWWGPGGUGFAHTHTHOFIHSFAFTUDSWPIWGPGZTHJGFTMGPTIUGUWWGPGWTHHSQTUGPTIUPESPSXQWGPGGUGFAHTHTHHIQSPTQSHJHSWGHGHAUIUAQYIXWGPGQIWSFTUV
~~~

&nbsp;

Step 4. Decrypt with the substitution alphabet from step 1 ("GCOWSYVETNDFQUIKRXHPJZLBAM"):

~~~python
ptxt = ctxt.translate(string.maketrans(alphabet,string.uppercase)) # ANALYSISOFDATAISAPROCESSOFINSPECTINGCLEANINGTRANSFORMINGANDMODELINGDATAWITHTHEGOALOFDISCOVERINGUSEFULINFORMATIONSUGGESTINGCONCLUSIONSANDSUPPORTINGDECISIONMAKINGDATAANALYSISHASMULTIPLEFACTSANDAPPROACHESENCOMPASSINGDIVERSETECHNIQUESUNDERAVARIETYOFNAMESINDIFFERENTBUSINESSSCIENCEANDSOCIALSCIENCEDOMAINSDATAMININGISAPARTICULARDATAANALYSISTECHNIQUETHATFOCUSESONMODELINGANDKNOWLEDGEDISCOVERYFORPREDICTIVERATHERTHANPURELYDESCRIPTIVEPURPOSESBUSINESSINTELLIGENCECOVERSDATAANALYSISTHATRELIESHEAVILYONAGGREGATIONFOCUSINGONBUSINESSINFORMATIONINSTATISTICALAPPLICATIONSSOMEPEOPLEDIVIDEDATAANALYSISINTODESCRIPTIVESTATISTICSEXPLORATORYDATAANALYSISEDAANDCONFIRMATORYDATAANALYSISCDAEDAFOCUSESONDISCOVERINGNEWFEATURESINTHEDATAANDCDAONCONFIRMINGORFALSIFYINGEXISTINGHYPOTHESESPREDICTIVEANALYTICSFOCUSESONAPPLICATIONOFSTATISTICALMODELSFORPREDICTIVEFORECASTINGORCLASSIFICATIONWHILETEXTANALYTICSAPPLIESSTATISTICALLINGUISTICANDSTRUCTURALTECHNIQUESTOEXTRACTANDCLASSIFYINFORMATIONFROMTEXTUALSOURCESASPECIESOFUNSTRUCTUREDDATAALLAREVARIETIESOFDATAANALYSISDATAINTEGRATIONISAPRECURSORTODATAANALYSISANDDATAANALYSISISCLOSELYLINKEDTODATAVISUALIZATIONANDDATADISSEMINATIONTHETERMDATAANALYSISISSOMETIMESUSEDASASYNONYMFORDATAMODELING
assert(data == ptxt) # True
~~~

### Frequency Analysis

While the alphabet substitution masked individual letters, each plaintext letter (eg, 'G') is still represented by the same ciphertext symbol (eg, 'A' from step 1). This means the relative frequency of each symbol remains unchanged and potentially vulnerable to [Frequency Analysis](https://en.wikipedia.org/wiki/Frequency_analysis#An_example). Given our plaintext and ciphertext, the frequencies follow:

~~~python
def calc_frequencies(data):
  import collections
  unigrams = collections.defaultdict(int)
  for i in xrange(0,len(data),1): unigrams[data[i]] += 1
  for i in unigrams: unigrams[i] /= float(len(data))
  return dict(unigrams)

ptxt_freqs = calc_frequencies(ptxt) # [('A',0.117),('I',0.104),('S',0.0995),('E',0.083)...
ctxt_freqs = calc_frequencies(ctxt) # [('G',0.117),('T',0.104),('H',0.0995),('S',0.083)...
~~~

&nbsp;

This also means that, given a known plaintext letter distribution, the substitution alphabet can be recovered:

~~~python
ptxt_letter_ranking = [x[0] for x in sorted(ptxt_freqs.items(),key=lambda x:-x[1])]
ctxt_letter_ranking = [x[0] for x in sorted(ctxt_freqs.items(),key=lambda x:-x[1])]
letter_ranking_map = dict(zip(ptxt_letter_ranking,ctxt_letter_ranking))
freq_alphabet = ''.join(letter_ranking_map.get(l,'-') for l in string.uppercase)
# GCOWSYVET-DFQUIKRXHPJZLBAM # note J->N lost since J isn't in the message
assert(ptxt == ctxt.translate(string.maketrans(freq_alphabet,string.uppercase)))
~~~

&nbsp;

Plaintext frequencies aren't generally known however, but tend to mirror linguistic norms (over sufficiently large volumes of text). For example, [English Letter Frequencies](https://en.wikipedia.org/wiki/Letter_frequencies#Relative_frequencies_of_letters_in_the_English_language) tends to have letter frequencies like ```[('E',0.127,('T',0.090),('A',0.0817)...]```. Unfortunately, the sample text significantly deviates from the common distribution which weakens the predictive power, although still useful.weakening the inferred relationship between letters.

### Word Patterns

In addition to macroscopic frequency distributions, the Monoalphabetic Substitution cipher also preserves structures within words. For example, the word 'ANALYSIS' still consists of 6 unique symbols ('A','N','L','Y','S','I') -> ('G','U','F','A','H','T') with 2 early repeats and 2 late repeats ('A-A--S-S' -> 'G-G--H-H'). This property can be used to identify words within the ciphertext ([crib](https://en.wikipedia.org/wiki/Crib_(cryptanalysis))) and, by extension, the plaintext->ciphertext mapping for the letters of each word:

~~~python
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
~~~

Given a wordlist such as `/usr/share/dict/american-english`, `find_cribs` identifies potential cribs embedded in the ciphertext and their plaintext->ciphertext letter mapping. For example, `find_cribs(words, ctxt, min_length=12)` identifies 'CLASSIFICATION' crib in the ciphertext. Combining all non-conflicting cribs (e.g. overlapping letters map to same values) exposes 15 plaintext -> ciphertext letter mappings, massively reducing the search space from 26! (~15 oktillion) to 11! (~3 million). [Oren](https://github.com/OrenLeaffer) helped develop a better regex [here](Backpointer.md).

### Shotgun Optimization

[Shotgun Hill Climbing](https://en.wikipedia.org/wiki/Shotgun_hill_climbing) is an algorithm for maximizing [fitness](https://en.wikipedia.org/wiki/Fitness_function) indicators (frequency analysis, word extraction) through local optimization steps (i.e. single letter swap) with restart-on-plateau to avoid local maxima. This allows a simple approach to testing substitution alphabets with guided optimizations, without getting "stuck" on wrong (but locally optimal) solutions.

### Word Extraction

[Word Extraction](https://en.wikipedia.org/wiki/Text_segmentation#Word_segmentation) is the process of identifying words in the (partially) decrypted message. Since multiple words are (relatively) unlikely to occur at random, successfully extracting multiple words at the start of partially decrypted messages suggests a good candidate substitution alphabet. A prefix [trie](https://en.wikipedia.org/wiki/Trie) is a relatively simple optimization that avoids searching through every word in our wordlist to identify candidate words. Greater fault-tolerance implemented [here](Word Extraction.md).
