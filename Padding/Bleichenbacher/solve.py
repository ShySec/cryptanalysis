import os
import sys
import string
import pickle
import random
import requests

def debug(msg, *args):
	print msg % args

def to_bytes(data):
	return ('%096x'%data).decode('hex')

def egcd(a, b):
	if a == 0: return (b, 0, 1)
	g, y, x = egcd(b % a, a)
	return (g, x - (b // a) * y, y)

def lcm(*numbers):
	def lcm(a, b): return (a * b) // egcd(a, b)[0]
	return reduce(lcm, numbers, 1)

def modinv(a, m):
	g, x, y = egcd(a, m)
	if g != 1: return
	return x % m

def bound(k):
	return 2**(8*(k-2))

def mult(si):
	return (cnum*pow(si,e,n))%n

def encrypt(ptxt, e, n):
	from Crypto.Hash import SHA
	from Crypto.PublicKey import RSA
	from Crypto.Cipher import PKCS1_v1_5
	key = RSA.construct(map(long,(n,e))) # sagemath Integers break RSA.construct
	return PKCS1_v1_5.new(key).encrypt(ptxt+SHA.new(ptxt).digest())

def decrypt(ctxt, e, p, q):
	from Crypto import Random
	from Crypto.Hash import SHA
	from Crypto.PublicKey import RSA
	from Crypto.Cipher import PKCS1_v1_5
	key = RSA.construct(map(long,(p*q,e,modinv(e,(p-1)*(q-1)),p,q))) # sagemath Integers break RSA.construct
	sentinel = Random.new().read(long(15)+SHA.digest_size) # Assume data of length 15
	message = PKCS1_v1_5.new(key).decrypt(ctxt, sentinel) # decrypt and return data OR sentinel (if padding invalid)
	digest = SHA.new(message[:-SHA.digest_size]).digest() # recalculate the hash
	if digest==message[-SHA.digest_size:]: return message # verify the hash
	return

def decrypt_with_pad(ctxt, e, p, q):
	from Crypto.PublicKey import RSA
	key = RSA.construct(map(long,(p*q,e,modinv(e,(p-1)*(q-1)),p,q)))
	return key.decrypt(ctxt)

def cache_load():
	if not os.path.exists('cache.db'): return {}
	return pickle.loads(open('cache.db').read())

def cache_update(data, value):
	cache[data] = value
	open('cache.db.tmp','wb').write(pickle.dumps(cache))
	os.rename('cache.db.tmp','cache.db')
	return value

cache = cache_load()
def padding_oracle(data):
	entry = cache.get(data)
	if entry is not None: return entry
	response=requests.get('%s/%s'%(server,data))
	debug('%s <- %s/%s'%(response.text,server,data))
	return cache_update(data,response.text=='1')

def conforming(si):
	global queries
	queries += 1
	if local: return conforming_local(si)
	return conforming_remote(si)

def conforming_local(si, tests=dict(header=True, valid_pad=True, null_delim=True)):
	data = to_bytes(decrypt_with_pad((cnum*pow(si,e,n))%n,e,p,q))
	if tests.get('header') and data[:2] != '\x00\x02': return False
	if tests.get('valid_pad') and '\x00' in data[1:10]: return False
	if tests.get('null_delim') and '\x00' not in data[10:]: return False
	return True

def conforming_remote(si):
	return padding_oracle(mult(si))

def find_conforming(value):
	while True:
		if conforming(value): return value
		value += 1

def divup(x, y):
	val = divmod(x,y)
	if not val[1]: return val[0]
	return val[0]+1

def divdn(x, y):
	return divmod(x,y)[0]

def step1():
	debug("\n## step1")
	s = [1]
	c = [mult(1)]
	M = [[[2*B,3*B-1]]]
	debug("M=%s",M)
	return step2a(s,c,M)

def step2(s,c,M):
	debug("\n## step2")
	if len(M[-1]) >= 2: return step2b(s,c,M)
	return step2c(s,c,M)

def step2a(s,c,M):
	debug("\n## step2a")
	s1 = find_conforming(divup(n,3*B))
	c1 = mult(s1)
	return step3(s+[s1],c+[c1],M)

def step2b(s,c,M):
	debug("\n## step2b")
	si = find_conforming(int(s[-1]+1))
	ci = mult(si)
	return step3(s+[si],c+[ci],M)

def step2c(s,c,M):
	debug("\n## step2c")
	a,b = M[-1][0]
	ri = divup(2*(b*s[-1] - 2*B),n)
	while True:
		sLo = divup(2*B+ri*n,b)
		sHi = divup(3*B+ri*n,a)
		for shift in xrange(sHi-sLo):
			si = sLo+shift
			if not conforming(si): continue
			ci = mult(si)
			return step3(s+[si],c+[ci],M)
		ri += 1

def step3(s,c,M):
	debug("\n## step3")
	si = s[-1]
	intervals = []
	debug("s=%s,M=%s",si,M[-1])
	for (a,b) in M[-1]:
		rLo = divdn(a*si-3*B+1,n)
		rHi = divup(b*si-2*B,n)
		debug('rLo=%s,rHi=%s',rLo,rHi)
		debug('a=%s,b=%s',a,b)
		for rshift in xrange(rHi-rLo+1):
			r = rLo+rshift
			lower = max(a,divup(r*n+2*B,si))
			upper = min(b,divdn(r*n+3*B-1,si))
			debug('%s - %s',lower,upper)
			if lower > upper: continue
			intervals.append([lower,upper])
	if not intervals: intervals = M[-1]
	debug("step3 => %s",intervals)
	return s,c,M+[intervals]

def step4(s,c,M):
	debug("\n## step4")
	for (a,b) in M[-1]:
		if a != b: continue
		print 'success => %s'%a
		return False
	return True

def attempt_decrypt(s,c,M):
	base = modinv(pow(s[0],e,n),n)
	for (a,b) in M[-1]:
		if a != b: continue
		value = (base * a)%n
		value_hex = '%096x'%value
		value_text = value_hex.decode('hex').split('\x00',2)[-1]
		value_print = filter(lambda x:x in string.printable,value_text)
		debug('%s\n%s\n%r\n%s',value,value_hex,value_text,value_print)
		if local: debug("%s",value_text[:-20]) # remove hash

def attack():
	s,c,M=step1()
	while step4(s,c,M):
		s,c,M=step2(s,c,M)
	debug('s=%s,c=%s,M=%s',s[-1],c[-1],M[-1])
	attempt_decrypt(s,c,M)

def assert_local_parameters(padded_ptxt):
	assert decrypt_with_pad(to_bytes(cnum),e,p,q) == padded_ptxt
	assert conforming(1) == True
	assert conforming(0) == False

def fixed_attack():
	debug("fixed attack")
	global e,p,q,n,cnum,local
	e,p,q = 3, 3107118869952759654056833918094500731837827021271511961771, 992983477001951052486234279505429027883013167985825891047
	padded_ptxt = '022d8f12ebc27ebec644f6377cee7dee00616161616161616161613495ff69d34671d1e15b33a63c1379fdedd3a32a'.decode('hex') # decrypt_with_pad(encrypt(ptxt,e,n),e,p,q)
	ctxt = '0525a87ddb66bd47b4366a272b34543e5758f745a96b5f7cddf774be48d0167a9f07877995cbf4ffd42e6de5e7e078f5'.decode('hex') # encrypt(ptxt,e,n)
	ptxt = 'aaaaaaaaaa'
	local = True

	n = p*q
	cnum = int(ctxt.encode('hex'),16)
	assert_local_parameters(padded_ptxt)
	attack()

def local_attack():
	debug("local attack")
	global e,p,q,n,cnum,local
	e,p,q = 3, 2791389255207484224763601846789596793395166036691746405957, 5338440783478444725454593548837864485136797999638265880279
	ptxt = 'bbbbbbbbbb'
	local = True

	n = p*q
	ctxt = encrypt(ptxt,e,n)
	cnum = int(ctxt.encode('hex'),16)
	padded_ptxt = decrypt_with_pad(ctxt,e,p,q)
	assert_local_parameters(padded_ptxt)
	attack()

def sage_attack(bits=384): # requires sage to generate primes P,Q
	debug("sage attack")
	global e,p,q,n,cnum,local
	while True:
		e,p,q = 3, random_prime(2**(bits/2)), random_prime(2**(bits/2))
		if modinv(e,(p-1)*(q-1)): break
	ptxt = 'aaaaaaaaaa'
	local = True

	n = p*q
	ctxt = encrypt(ptxt,e,n)
	cnum = int(ctxt.encode('hex'),16)
	padded_ptxt = decrypt_with_pad(ctxt,e,p,q)
	assert_local_parameters(padded_ptxt)
	attack()

def remote_attack():
	debug("remote attack")
	global e,p,q,n,cnum,local
	e,n = 0x3,0x4c81390477e071a7a9afd85eeb93f3596cf69fb8e7fadf422f22c68891586611af5e74aa8b4df9a585486898f632ae63
	cnum = 0x1cb75d15d80c8bd7572281de5da592a428db429870b4a654b8722f98acc220b6701f6c0b7313fb9ef4ca15a87d9273bb
	local = False
	attack()

if __name__ == '__main__':
	queries = 0
	B = bound(48) # key length
	server = '' # add server URL for a remote attack
	choice = int(sys.argv[1]) if len(sys.argv)>1 else 1
	if choice == 1: fixed_attack()
	if choice == 2: local_attack()
	if choice == 3: sage_attack()
	if choice == 4: remote_attack()
	print '%d queries'%queries
