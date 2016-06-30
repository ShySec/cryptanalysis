# Fault-Tolerant Word Extraction
## Make Believe Words and Partial Keys

The [Monoalphabetic Substitution solver](/post/20160627-Monoalphabetic%20Substitution) used a [depth-first search](https://en.wikipedia.org/wiki/Depth-first_search) for fast [text segmentation](https://en.wikipedia.org/wiki/Text_segmentation). While this approach is very efficient when word choices pass or fail cleanly, the worst case impact of pass/fail only becoming clear many choices later may waste enormous amounts of computation. Fortunately, English text is highly localized and rapidly diffuses errors (segmentation-wise). For example, 'ANALYTICS' is not in the Linux [/usr/share/dict/american-english](http://manpages.ubuntu.com/manpages/precise/man5/american-english.5.html) dictionary causing 'ANALYTICS APPLIES STATISTICAL' to segment into 'ANALYTIC SAP PLIES STATISTICAL'.

A [pathological](https://en.wikipedia.org/wiki/Pathological_(mathematics)#Computer_science) input is one wherein a character late in the plaintext cannot be incoporated into a word (either due to key errors or incomplete dictionary). An example of this is visible when running `segment_words` on portions of some incorrectly accepted plaintext (alphabet "GZOWSYVETMBFQUIKNXHPJRLDAC") where e('DIVERSE') was decrypted to 'DIBERSE' at 213.

~~~python
>>> l=213;s=time.time();wf=segment_words(ptxt,length_cap=l);e=time.time();print e-s,wf[1]
0.0005s ['ANALYSIS', 'OF', 'DATA', 'IS', 'A', 'PROCESS', 'OF', 'INSPECTING', 'CLEANING', 'TRANSFORMING', 'AND', 'MODELING', 'DATA', 'WITH', 'THE', 'GOAL', 'OF', 'DISCO', 'BERING', 'USEFUL', 'INFORMATION', 'SUGGESTING', 'CONCLUSIONS', 'AND', 'SUPPORTING', 'DECISION', 'MAXING', 'DATA', 'ANALYSIS', 'HAS', 'MULTIPLE', 'FACTS', 'AND', 'APPROACHES', 'ENCOMPASSING']
>>> l=214;s=time.time();wf=segment_words(ptxt,length_cap=l);e=time.time();print e-s,wf[1]
6.8491s ['ANALYSIS', 'OF', 'DATA', 'IS', 'A', 'PROCESS', 'OF', 'INSPECTING', 'CLEANING', 'TRANSFORMING', 'AND', 'MODELING', 'DATA', 'WITH', 'THE', 'GOAL', 'OF', 'DISCO', 'BERING', 'USEFUL', 'INFORMATION', 'SUGGESTING', 'CONCLUSIONS', 'AND', 'SUPPORTING', 'DECISION', 'MAXING', 'DATA', 'ANALYSIS', 'HAS', 'MULTIPLE', 'FACTS', 'AND', 'APPROACHES', 'ENCOMPASSING']
>>> ptxt[201:213]+' '+ptxt[213:220]+' '+ptxt[220:240]
'ENCOMPASSING DIBERSE TECHNIVUESUNDERABARI'
~~~

The impact is much worse the later it occurs. When parsing the correctly decrypted plaintext the execution time jumps from ~8ms (length_cap=630) to [over a month](https://en.wikipedia.org/wiki/Extrapolation) (length_cap=631)! The problem was the 3 letter acronym `"EDA"` which was neither in the dictionary nor happened to "fit" into a word (like the `"EDA"` substring at position 570).

### Curing Pathology with [Commitment Bias](https://en.wikipedia.org/wiki/Escalation_of_commitment)

Text segmentation errors tend to be fairly localized (although I haven't found any supporting studies ^(yet)) either shifting the next several words beyond recovery (failing the tree) or incorporating into the next several words (failing to propagate). So one very easy fix to pathological inputs is to "pass" a word choice if its selection allowed at least N more words to be segmented. Doubling down on "failed" paths could miss better options, but fast and semi-accurate cognitive biases are pretty convincing. Attempting to extract `'EDA'` (length_cap=631) now takes just 10ms.

~~~python
def segment_words(data, length_cap=200, last='', prefix_words=[], min_commitment=20):
  max_length = 0
  max_words = prefix_words
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
    if pre_length>min_commitment: break # limit backtracking
  return (max_length,max_words)
~~~

### Curing Pathology with [Acceptance](https://en.wikipedia.org/wiki/K%C3%BCbler-Ross_model#Stages)

Real-world data includes typos, proper nouns, errors, esoteric words, science words, and [made up words](https://xkcd.com/483/). This means any real-world parser needs the ability to identify new words, identify word variants, or otherwise progress beyond the problem. On the other hand, unknown words may also result from bad word replacements or bad decryptions - so any error mitigation must meet a high threshold for correctness. Since segment_words already returns partial results to root notes on failure, it's just a matter of identifying then a failure represents an unknown word then reparsing that tree. And now `'EDA'` (along with `'ANALYTICS'`) can be correctly segmented.

~~~python
def segment_words(data, length_cap=200, last='', prefix_words=[], skip_at=None, min_commitment=20):
  ...
  for word in trie_prefix(prefix_trie, data):
    ...
    if pre_length>min_commitment: break # limit backtracking
      if not skippable: break
      next_skip_at=len(pre_words)-len(prefix_words)
      skip_length,skip_words = segment_words(data[word_len:], length_cap-word_len, last=word, prefix_words=prefix_words+[word], skip_at=next_skip_at, skippable=skippable)
      if skip_length+word_len > max_length: max_length,max_words = skip_length+word_len,skip_words
      if skip_length+word_len == max_length and len(skip_words)<len(max_words):
        max_length,max_words = skip_length+word_len,skip_words
      if max_length >= length_cap: break
  # try to skip unknown words during backtrack
  if skip_at == 0:
    for skip in xrange(3,24):
      word = data[:skip]
      word_len = len(word)
      prefix_trie_bak = prefix_trie
      prefix_trie = trie_copy(prefix_trie)
      trie_add(prefix_trie,word) # temporarily add to dictionary
      skip_length,skip_words = segment_words(data[word_len:], length_cap-word_len, last=word, prefix_words=[word], skippable=skippable)
      prefix_trie = prefix_trie_bak
      if skip_length<min_commitment: continue
      if skip_length+word_len >= max_length: max_length,max_words = skip_length+word_len,prefix_words+skip_words
      logging.info('added %s to dictionary (%s)',word,''.join(prefix_words[-3:]+['-',word,'-']+skip_words[1:4]))
      trie_add(prefix_trie, word)
      break
  return (max_length,max_words)

def trie_copy(trie):
  import copy
  return copy.deepcopy(trie)
~~~

~~~bash
$ python solve.py
testing potential crib(s): STATISTICS, CLASSIFICATION, CONCLUSIONS, INTELLIGENCE, DISSEMINATION, UNSTRUCTURED, STATISTICAL, STATISTIC, INDIFFERENT
fitness 74.558 (length 17) "GBOWSYVDTMRFQUINCXHPJZLEAK"
fitness 74.961 (length 17) "GBOWSYVDTKRFQUINCXHPJZLEAM"
fitness 83.829 (length 18) "GBOWSYVDTERFQUINCXHPJZLKAM"
fitness 2320.662 (length 74) "GBOWSYVDTERFQUIKCXHPJZLNAM"
fitness 2419.744 (length 74) "GBOWSYVDTREFQUIKCXHPJZLNAM"
fitness 24475.805 (length 221) "GBOWSYVETRDFQUIKCXHPJZLNAM"
fitness 24593.720 (length 221) "GBOWSYVETRDFQUIKNXHPJZLCAM"
fitness 34499.428 (length 261) "GBOWSYVETNDFQUIKRXHPJZLCAM"
fitness 44640.233 (length 303) "GCOWSYVETNDFQUIKRXHPJZLBAM"
"GCOWSYVETNDFQUIKRXHPJZLBAM" => ANALYSISOFDATAISAPROCESSOFINSPECTINGCLEANINGTRANSFORMINGANDMODELINGDATAWITHTHEGOALOFDISCOVERINGUSEFULINFORMATIONSUGGESTINGCONCLUSIONSANDSUPPORTINGDECISIONMAKINGDATAANALYSISHASMULTIPLEFACTSANDAPPROACHESENCOMPASSINGDIVERSETECHNIQUESUNDERAVARIETYOFNAMESINDIFFERENTBUSINESSSCIENCEANDSOCIALSCIENCEDOMAINSDATAMININGISAPARTICULARDATAANALYSISTECHNIQUETHATFOCUSESONMODELINGANDKNOWLEDGEDISCOVERYFORPREDICTIVERATHERTHANPURELYDESCRIPTIVEPURPOSESBUSINESSINTELLIGENCECOVERSDATAANALYSISTHATRELIESHEAVILYONAGGREGATIONFOCUSINGONBUSINESSINFORMATIONINSTATISTICALAPPLICATIONSSOMEPEOPLEDIVIDEDATAANALYSISINTODESCRIPTIVESTATISTICSEXPLORATORYDATAANALYSISEDAANDCONFIRMATORYDATAANALYSISCDAEDAFOCUSESONDISCOVERINGNEWFEATURESINTHEDATAANDCDAONCONFIRMINGORFALSIFYINGEXISTINGHYPOTHESESPREDICTIVEANALYTICSFOCUSESONAPPLICATIONOFSTATISTICALMODELSFORPREDICTIVEFORECASTINGORCLASSIFICATIONWHILETEXTANALYTICSAPPLIESSTATISTICALLINGUISTICANDSTRUCTURALTECHNIQUESTOEXTRACTANDCLASSIFYINFORMATIONFROMTEXTUALSOURCESASPECIESOFUNSTRUCTUREDDATAALLAREVARIETIESOFDATAANALYSISDATAINTEGRATIONISAPRECURSORTODATAANALYSISANDDATAANALYSISISCLOSELYLINKEDTODATAVISUALIZATIONANDDATADISSEMINATIONTHETERMDATAANALYSISISSOMETIMESUSEDASASYNONYMFORDATAMODELING
DEBUG:root:unknown word at EDAANDCONFIRMATORYDATAANALYSISCDAEDAFOCU (['STATISTICS', 'EXPLORATORY', 'DATA', 'ANALYSIS'])
DEBUG:root:unknown word at CDAEDAFOCUSESONDISCOVERINGNEWFEATURESINT (['CON', 'FIRM', 'A', 'TORY', 'DATA', 'ANALYSIS'])
DEBUG:root:unknown word at SFOCUSESONAPPLICATIONOFSTATISTICALMODELS (['HYPO', 'THESES', 'PREDICTIVE', 'ANALYTIC'])
INFO:root:added SFOC to dictionary (THESESPREDICTIVEANALYTIC-SFOC-USESONAPPLICATION)
INFO:root:added CDA to dictionary (TORYDATAANALYSIS-CDA-EDAFOCUSESON)
INFO:root:added EDA to dictionary (EXPLORATORYDATAANALYSIS-EDA-ANDCONFIRM)
ANALYSIS OF DATA IS A PROCESS OF INSPECTING CLEANING TRANSFORMING AND MODELING DATA WITH THE GOAL OF DISCOVERING USEFUL INFORMATION SUGGESTING CONCLUSIONS AND SUPPORTING DECISION MAKING DATA ANALYSIS HAS MULTIPLE FACTS AND APPROACHES ENCOMPASSING DIVERSE TECHNIQUES UNDER A VARIETY OF NAMES INDIFFERENT BUSINESS SCIENCE AND SOCIAL SCIENCE DOMAINS DATA MINING IS A PARTICULAR DATA ANALYSIS TECHNIQUE THAT FOCUSES ON MODELING AND KNOWLEDGE DISCOVERY FOR PREDICTIVE RATHER THAN PURELY DESCRIPTIVE PURPOSES BUSINESS INTELLIGENCE COVERS DATA ANALYSIS THAT RELIES HEAVILY ON AGGREGATION FOCUSING ON BUSINESS INFORMATION IN STATISTICAL APPLICATIONS SOME PEOPLE DIVIDED AT A ANALYSIS INTO DESCRIPTIVE STATISTICS EXPLORATORY DATA ANALYSIS EDA AND CON FIRM A TORY DATA ANALYSIS CDA EDA FOCUSES ON DISCOVERING NEW FEATURES IN THE DATA AND CDA ON CONFIRMING OR FALSIFYING EXISTING HYPO THESES PREDICTIVE ANALYTIC SFOC USES ON APPLICATION OF STATISTICAL MODELS FOR PREDICTIVE FORECASTING OR CLASSIFICATION WHILE TEXT ANALYTIC SAP PLIES STATISTICAL LINGUISTIC AND STRUCTURAL TECHNIQUES TO EXTRACT AND CLASSIFY INFORMATION FROM TEXTUAL SOURCES A SPECIES OF UNSTRUCTURED DATA ALL ARE VARIETIES OF DATA ANALYSIS DATA INTEGRATION IS A PRECURSOR TOD AT A ANALYSIS AND DATA ANALYSIS IS CLOSELY LINKED TOD AT A VISUALIZATION AND DATA DISSEMINATION THE TERM DATA ANALYSIS IS SOMETIMES USED AS A SYNONYM FORD AT A MODELING
execution time: 16.563
~~~
