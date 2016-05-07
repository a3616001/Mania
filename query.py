import urllib2 as urllib
import ujson as json
#import json
import sys
import time
from multiprocessing.dummy import Pool

def answer(ans, path):
	#print path
	ans.append(path)

def getPaperJson(id, urlAttributes):
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Id=%d&count=1000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id,urlAttributes)
	#sys.stderr.write(url + '\n')
	f = urllib.urlopen(url)
	result = json.loads(f.read())
	return result['entities'][0]

def join(l1, l2): # join two sorted list
	n1 = len(l1)
	n2 = len(l2)
	#l1.sort()
	#l2.sort()
	p1 = 0
	p2 = 0
	ret = []
	while p1 < n1 and p2 < n2:
		if l1[p1] < l2[p2]:
			p1 += 1
		elif l1[p1] > l2[p2]:
			p2 += 1
		else:
			ret.append(l1[p1])
			p1 += 1
			p2 += 1
	return ret

def query_Id_Id(id1, id2, json1, json2):
	#sys.stderr.write('query_Id_Id ' + str(id1) + ' ' + str(id2) + '\n')
	print 'query_Id_Id', id1, id2
	ans = []

	#print json1

	#json1 = getPaperJson(id1, 'RId,F.FId,J.JId,C.CId,AA.AuId')
	#json2 = getPaperJson(id2, 'F.FId,J.JId,C.CId,AA.AuId')
	#print json1['RId']
	#print json2
	
	now = time.time()
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=RId=%d&count=200000&orderby=CC:desc&attributes=Id,F.FId,J.JId,C.CId,AA.AuId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=%d,CC>0)&count=50000&orderby=CC:desc&attributes=Id,F.FId,J.JId,C.CId,AA.AuId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	Id2cited = json.loads(urllib.urlopen(url).read())['entities']
	print 'time use2: ', time.time() - now
	# =========== 1-hop =========== 

	# Id-Id
	if json1.has_key('RId') and id2 in json1['RId']:
		answer(ans, [id1, id2])

	# =========== 2-hop =========== 

	# Id-F.FId-Id
	if json1.has_key('F'):
		FIdList1 = map(lambda x:x['FId'], json1['F'])
		FIdList1.sort()
	if json2.has_key('F'):
		FIdList2 = map(lambda x:x['FId'], json2['F'])
		FIdList2.sort()		
	if json1.has_key('F') and json2.has_key('F'):
		jointFIdList = join(FIdList1, FIdList2)
		for FId in jointFIdList:
			answer(ans, [id1, FId, id2])

	# Id-J.JId-Id
	if json1.has_key('J') and json2.has_key('J') and json1['J']['JId'] == json2['J']['JId']:
		answer(ans, [id1, json1['J']['JId'], id2])

	# Id-C.CId-Id
	if json1.has_key('C') and json2.has_key('C') and json1['C']['CId'] == json2['C']['CId']:
		answer(ans, [id1, json1['C']['CId'], id2])

	# Id-AA.AuId-Id
	if json1.has_key('AA'):
		AuIdList1 = map(lambda x:x['AuId'], json1['AA'])
		AuIdList1.sort()
	if json2.has_key('AA'):
		AuIdList2 = map(lambda x:x['AuId'], json2['AA'])
		AuIdList2.sort()
	if json1.has_key('AA') and json2.has_key('AA'):
		jointAuIdList = join(AuIdList1, AuIdList2)
		for AuId in jointAuIdList:
			answer(ans, [id1, AuId, id2])

	# Id-Id-Id
	# TODO 
	if json1.has_key('RId'):
		RIdList = json1['RId']
		Id2citedList = map(lambda x:x['Id'], Id2cited)
		RIdList.sort()
		Id2citedList.sort()
		jointRIdList = join(RIdList, Id2citedList)
		for RId in jointRIdList:
			answer(ans, [id1, RId, id2])

	# =========== 3-hop =========== 

	# Id-*-Id-Id
	if len(Id2cited) != 0:

		now = time.time()
		poolResult = []
		pool = Pool(20)
		if json1.has_key('F'):
			for FId in FIdList1:
				url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=%d,Composite(F.FId=%d))&count=200000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id2, FId)
				poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url, )))
		if json1.has_key('J'):
			url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=%d,Composite(J.JId=%d))&count=200000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id2, json1['J']['JId'])
			poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url, )))
		if json1.has_key('C'):
			url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=%d,Composite(C.CId=%d))&count=200000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id2, json1['C']['CId'])
			poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url, )))
		if json1.has_key('AA'):
			for AuId in AuIdList1:
				url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=%d,Composite(AA.AuId=%d))&count=200000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id2, AuId)
				poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url, )))
		pool.close()
		pool.join()
		print 'time use3: ', time.time() - now

		idx = 0

		# Id-F.FId-Id-Id
		if json1.has_key('F'):
			for FId in FIdList1:
				comPaperList = poolResult[idx].get()
				idx += 1
				for comPaper in comPaperList:
					answer(ans, [id1, FId, comPaper['Id'], id2])

		# Id-J.JId-Id-Id
		if json1.has_key('J'):
			JId = json1['J']['JId']
			comPaperList = poolResult[idx].get()
			idx += 1
			for comPaper in comPaperList:
				answer(ans, [id1, JId, comPaper['Id'], id2])

		# Id-C.CId-Id-Id
		if json1.has_key('C'):
			CId = json1['C']['CId']
			comPaperList = poolResult[idx].get()
			idx += 1
			for comPaper in comPaperList:
				answer(ans, [id1, CId, comPaper['Id'], id2])
		
		# Id-AA.AuId-Id-Id
		if json1.has_key('AA'):
			for AuId in AuIdList1:
				comPaperList = poolResult[idx].get()
				idx += 1
				for comPaper in comPaperList:
					answer(ans, [id1, AuId, comPaper['Id'], id2])

	# Id-Id-*-Id
	if json1.has_key('RId'):

		urlAttributes = 'Id,RId'
		if json2.has_key('F'):
			urlAttributes += ',F.FId'
		if json2.has_key('J'):
			urlAttributes += ',J.JId'
		if json2.has_key('C'):
			urlAttributes += ',C.CId'
		if json2.has_key('AA'):
			urlAttributes += ',AA.AuId'
		now = time.time()	
		pool = Pool(20)	
		id1CitePapersInfoResult = pool.map_async(lambda x:getPaperJson(x, urlAttributes), json1['RId'])
		pool.close()
		pool.join()
		id1CitePapersInfo = id1CitePapersInfoResult.get()
		print 'time use4: ', time.time() - now
		# Id-Id-F.FId-Id
		if json2.has_key('F'):
			for id1CitePaper in id1CitePapersInfo:
				if id1CitePaper.has_key('F'):
					FIdListTmp = map(lambda x:x['FId'], id1CitePaper['F'])
					FIdListTmp.sort()
					jointFIdList = join(FIdListTmp, FIdList2)
					for FId in jointFIdList:
						answer(ans, [id1, id1CitePaper['Id'], FId, id2])

		# Id-Id-J.JId-Id
		if json2.has_key('J'):
			for id1CitePaper in id1CitePapersInfo:
				if id1CitePaper.has_key('J') and id1CitePaper['J']['JId'] == json2['J']['JId']:
					answer(ans, [id1, id1CitePaper['Id'], json2['J']['JId'], id2])

		# Id-Id-C.CId-Id
		if json2.has_key('C'):
			for id1CitePaper in id1CitePapersInfo:
				if id1CitePaper.has_key('C') and id1CitePaper['C']['CId'] == json2['C']['CId']:
					answer(ans, [id1, id1CitePaper['Id'], json2['C']['CId'], id2])

		# Id-Id-AA.AuId-Id
		if json2.has_key('AA'):
			for id1CitePaper in id1CitePapersInfo:
				if id1CitePaper.has_key('F'):
					AuIdListTmp = map(lambda x:x['AuId'], id1CitePaper['AA'])
					AuIdListTmp.sort()
					jointAuIdList = join(AuIdListTmp, AuIdList2)
					for AuId in jointAuIdList:
						answer(ans, [id1, id1CitePaper['Id'], AuId, id2])

		# Id-Id-Id-Id
		tmp = len(ans)
		for id1CitePaper in id1CitePapersInfo:
			if id1CitePaper.has_key('RId'):
				RIdListTmp = id1CitePaper['RId']
				RIdListTmp.sort()
				jointRIdList = join(RIdListTmp, Id2citedList)
				for RId in jointRIdList:
					answer(ans, [id1, id1CitePaper['Id'], RId, id2])
		print 'len(Id-Id-Id-Id) =', len(ans)-tmp

	# return ans
	return ans

def query_AuId_Id(auId1, id2, json1, json2):
	#sys.stderr.write('query_AuId_Id ' + str(auId1) + ' ' + str(id2) + '\n')
	print 'query_AuId_Id', auId1, id2
	ans = []

	#now = time.time()
	#json2 = getPaperJson(id2, 'F.FId,J.JId,C.CId,AA.AuId,AA.AfId')
	#print 'time use2: ', time.time() - now
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,RId,F.FId,J.JId,C.CId,AA.AuId&orderby=D:desc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%auId1
	#json1 = json.loads((urllib.urlopen(url)).read())['entities']

	# =========== 1-hop =========== 

	# AuId-Id
	for paper in json1:
		if paper['Id'] == id2:
			answer(ans, [auId1, id2])
			break


	# =========== 2-hop =========== 

	# AuId-Id-Id
	for paper in json1:
		if paper.has_key('RId') and (id2 in paper['RId']):
			answer(ans, [auId1, paper['Id'], id2])

	# =========== 3-hop =========== 

	# AuId-Id-F.FId-Id
	if json2.has_key('F'):
		FIdList2 = map(lambda x:x['FId'], json2['F'])
		FIdList2.sort()
		for paper in json1:
			if paper.has_key('F'):
				FIdListTmp = map(lambda x:x['FId'], paper['F'])
				FIdListTmp.sort()
				jointFIdList = join(FIdListTmp, FIdList2)
				for FId in jointFIdList:
					answer(ans, [auId1, paper['Id'], FId, id2])

	# AuId-Id-C.CId-Id
	if json2.has_key('C'):
		CId2 = json2['C']['CId']
		for paper in json1:
			if paper.has_key('C') and paper['C']['CId'] == CId2:
				answer(ans, [auId1, paper['Id'], CId2, id2])

	# AuId-Id-J.JId-Id
	if json2.has_key('J'):
		JId2 = json2['J']['JId']
		for paper in json1:
			if paper.has_key('J') and paper['J']['JId'] == JId2:
				answer(ans, [auId1, paper['Id'], JId2, id2])

	# AuId-Id-AA.AuId-Id
	if json2.has_key('AA'):
		AuIdList2 = map(lambda x:x['AuId'], json2['AA'])
		AuIdList2.sort()
		for paper in json1:
			if paper.has_key('AA'):
				AuIdListTmp = map(lambda x:x['AuId'], paper['AA'])
				AuIdListTmp.sort()
				jointAuIdList = join(AuIdListTmp, AuIdList2)
				for AuId in jointAuIdList:
					answer(ans, [auId1, paper['Id'], AuId, id2])

	# AuId-Id-Id-Id
	#now = time.time()
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=RId=%d&count=100000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	Id2cited = json.loads(urllib.urlopen(url).read())['entities']
	#print 'time use3:', time.time() - now
	if len(Id2cited) > 0:
		Id2citedList = map(lambda x:x['Id'], Id2cited)
		Id2citedList.sort()
		for paper in json1:
			if paper.has_key('RId'):
				RIdListTmp = paper['RId']
				RIdListTmp.sort()
				jointRIdList = join(RIdListTmp, Id2citedList)
				for RId in jointRIdList:
					answer(ans, [auId1, paper['Id'], RId, id2])

	# AuId-AA.AFId-AA.AuId-Id
	afId1 = -1
	for author in json1[0]['AA']:
		if author['AuId'] == auId1 and author.has_key('AfId'):
			afId1 = author['AfId']
	if afId1 != -1 and json2.has_key('AA'):
		for author in json2['AA']:
			if author.has_key('AfId') and author['AfId'] == afId1:
				answer(ans, [auId1, afId1, author['AuId'], id2])

	return ans

def query_Id_AuId(id1, auId2, json1, json2):
	#sys.stderr.write('query_AuId_Id ' + str(id1) + ' ' + str(auId2) + '\n')
	print 'query_Id_AuId', id1, auId2
	ans = []
	
	#now = time.time()
	#json1 = getPaperJson(id1, 'RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId')
	#print 'time use: ', time.time() - now	
	#now = time.time()
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,F.FId,J.JId,C.CId,AA.AuId&orderby=D:asc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%auId2
	#json2 = json.loads((urllib.urlopen(url)).read())['entities']

	paperIdList = map(lambda x:x['Id'], json2)
	paperIdList.sort()

	# =========== 1-hop ===========

	# Id-AuId
	if json1.has_key('AA') and (auId2 in map(lambda x:x['AuId'], json1['AA'])):
		answer(ans, [id1, auId2])

	# =========== 2-hop ===========

	# Id-Id-AuId
	if json1.has_key('RId'):
		RIdList = json1['RId']
		RIdList.sort()
		jointRIdList = join(paperIdList, RIdList)
		for RId in jointRIdList:
			answer(ans, [id1, RId, auId2])

	# =========== 3-hop ===========

	# Id-F.FId-Id-AuId
	if json1.has_key('F'):
		FIdList1 = map(lambda x:x['FId'], json1['F'])
		FIdList1.sort()
		for paper in json2:
			if paper.has_key('F'):
				FIdListTmp = map(lambda x:x['FId'], paper['F'])
				FIdListTmp.sort()
				jointFIdList = join(FIdListTmp, FIdList1)
				for FId in jointFIdList:
					answer(ans, [id1, FId, paper['Id'], auId2])

	# Id-C.CId-Id-AuId
	if json1.has_key('C'):
		CId1 = json1['C']['CId']
		for paper in json2:
			if paper.has_key('C') and paper['C']['CId'] == CId1:
				answer(ans, [id1, CId1, paper['Id'], auId2])

	# Id-J.JId-Id-AuId
	if json1.has_key('J'):
		JId1 = json1['J']['JId']
		for paper in json2:
			if paper.has_key('J') and paper['J']['JId'] == JId1:
				answer(ans, [id1, JId1, paper['Id'], auId2])

	# Id-AA.AuId-Id-AuId
	if json1.has_key('AA'):
		AuIdList1 = map(lambda x:x['AuId'], json1['AA'])
		AuIdList1.sort()
		for paper in json2:
			if paper.has_key('AA'):
				AuIdListTmp = map(lambda x:x['AuId'], paper['AA'])
				AuIdListTmp.sort()
				jointAuIdList = join(AuIdListTmp, AuIdList1)
				for AuId in jointAuIdList:
					answer(ans, [id1, AuId, paper['Id'], auId2])

	# Id-Id-Id-AuId
	if json1.has_key('RId'):
		pool = Pool(20)
		citePaperInfoResults = pool.map_async(lambda x:getPaperJson(x, 'RId'), RIdList)
		pool.close()
		pool.join()
		citePaperInfos = citePaperInfoResults.get()
		for citePaperInfo in citePaperInfos:
			if citePaperInfo.has_key('RId'):
				RIdListTmp = citePaperInfo['RId']
				RIdListTmp.sort()
				jointRIdList = join(RIdListTmp, paperIdList)
				for comRId in jointRIdList:
					answer(ans, [id1, RId, comRId, auId2])

	# Id-AA.AuId-AA.AfId-AuId
	afId2 = -1
	for author in json2[0]['AA']:
		if author['AuId'] == auId2 and author.has_key('AfId'):
			afId2 = author['AfId']
	if afId2 != -1 and json1.has_key('AA'):
		for author in json1['AA']:
			if author.has_key('AfId') and author['AfId'] == afId2:
				answer(ans, [id1, author['AuId'], afId2, auId2])
	#print 'time use2: ', time.time() - now
	return ans

def query_AuId_AuId(auId1, auId2, json1, json2):
	sys.stderr.write('query_AuId_AuId ' + str(auId1) + ' ' + str(auId2) + '\n')
	ans = []

	# =========== 2-hop ===========

	# AuId-*-AuId
	for paper1 in json1:
		for paper2 in json2:
			# AuId-AFId-AuId
			if paper1.has_key('AfId') and paper2.has_key('AfId'):
				if paper1['AfId']==paper2['AfId']:
					answer(ans, [auId1, paper1['AfId'], auId2])
			# AuId-Id-AuId
			if paper1.has_key('Id') and paper2.has_key('Id'):
				if paper1['Id']==paper2['Id']:
					answer(ans, [auId1, paper1['Id'], auId2])

	# =========== 3-hop ===========

	# AuId-Id-Id-AuId
	IdList2 = []
	for paper2 in json2:
		if paper2.has_key('Id'):
			IdList2.append(paper2['Id'])
	for paper1 in json1:
		if paper1.has_key('Id'):
			if paper1.has_key('RId') and paper1['RId'] in IdList2:
				answer(ans, [auId1, paper1['Id'], paper1['RId'], auId2])
			for paper2 in json2:
				if paper2.has_key('Id') and paper1['Id']==paper2['Id']:
					if paper2.has_key('RId') and paper2['RId'] in IdList2:
						answer(ans, [auId1, paper2['Id'], paper2['RId'],auId2])

	return ans

def query(id1, id2):
	#now = time.time()
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId&orderby=D:desc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id1
	#json1 = json.loads((urllib.urlopen(url)).read())['entities']
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,F.FId,J.JId,C.CId,AA.AuId,AA.AfId&orderby=D:asc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	#json2 = json.loads((urllib.urlopen(url)).read())['entities']
	#print 'time use: ', time.time() - now
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=1&attributes=Id,AA.AuId,AA.AfId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id1
	#json1 = (json.loads((urllib.urlopen(url)).read()))['entities']
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=1&attributes=Id,AA.AuId,AA.AfId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	#json2 = (json.loads((urllib.urlopen(url)).read()))['entities']

	url1 = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId&orderby=D:desc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id1
	url2 = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Composite(AA.AuId=%d)&count=20000&attributes=Id,F.FId,J.JId,C.CId,AA.AuId,AA.AfId&orderby=D:asc&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	poolResult = []
	pool = Pool(20)
	poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url1,)))
	poolResult.append(pool.apply_async(lambda url: json.loads((urllib.urlopen(url)).read())['entities'], (url2,)))
	poolResult.append(pool.apply_async(getPaperJson, (id1, 'RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId')))
	poolResult.append(pool.apply_async(getPaperJson, (id2, 'F.FId,J.JId,C.CId,AA.AuId,AA.AfId')))
	pool.close()
	pool.join()
	json1 = poolResult[0].get()
	json2 = poolResult[1].get()
	paperJson1 = poolResult[2].get()
	paperJson2 = poolResult[3].get()

	if json1 and json2:
		#afId1 = -1
		#afId2 = -1
		#for author in json1[0]['AA']:
		#	if author['AuId'] == id1 and author.has_key('AfId'):
		#		afId1 = author['AfId']
		#for author in json2[0]['AA']:
		#	if author['AuId'] == id2 and author.has_key('AfId'):
		#		afId2 = author['AfId']
		#return query_AuId_AuId(id1, id2, afId1, afId2)
		return query_AuId_AuId(id1, id2, json1, json1)
	elif json1:
		#afId1 = -1
		#for author in json1[0]['AA']:
		#	if author['AuId'] == id1 and author.has_key('AfId'):
		#		afId1 = author['AfId']
		#return query_AuId_Id(id1, id2, afId1)
		return query_AuId_Id(id1, id2, json1, paperJson2)
	elif json2:
		#afId2 = -1
		#for author in json2[0]['AA']:
		#	if author['AuId'] == id2 and author.has_key('AfId'):
		#		afId2 = author['AfId']
		#return query_Id_AuId(id1, id2, afId2)
		return query_Id_AuId(id1, id2, paperJson1, json2)
	else:
		return query_Id_Id(id1, id2, paperJson1, paperJson2)

def main():
	#query(2140190241, 1514498087)
	#query(2140190241, 1490955312)
	#query(2126125555, 2153635508)
	#query(2126125555, 2060367530)
	#query(2140190241, 2121939561)
	#query(2175015405, 1514498087)
	#print query(2251253715,2180737804)
	#print len(query(2100837269, 621499171))
	print len(query(2126125555,2060367530))

if __name__ == '__main__':
    main()
