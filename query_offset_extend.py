import urllib2 as urllib
import ujson as json
#from join import *
import os
# import pycurl
# from StringIO import StringIO
import sys
import time
from multiprocessing.dummy import Pool

threadnum = 20

sumLen = 0
urlcache = dict()
pool = Pool(threadnum)

def urlrequest(url):
	global sumLen
	if url in urlcache:
		return urlcache[url]
	else:
		res = urllib.urlopen(url).read()
		sumLen += len(res)
		res = json.loads(res)
		if sumLen <= 333333333:
			urlcache[url] = res
		print 'sumLen', sumLen
		return res

def getPaperJson(id, urlAttributes):
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Id=%d&count=1000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id,urlAttributes)
	result = urlrequest(url)
	return result['entities'][0]

def getPaperJsonList(idList, urlAttributes):
	if idList == []:
		return []
	now = time.time()
	PaperJsonList = []
	poolResult = []
	L = 0
	expr = ''
	for id in idList:
		if expr == '':
			expr = 'Id=%d'%id
			L = len(expr)
		elif L + len(str(id)) + 8 <= 1800:
			expr = 'Or(%s,Id=%d)'%(expr,id)
			L += len(str(id)) + 8
		else:
			url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=%s&count=1000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(expr,urlAttributes)
			poolResult.append(pool.apply_async(lambda url:urlrequest(url)['entities'], (url, )))

			expr = 'Id=%d'%id
			L = len(expr)

	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=%s&count=1000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(expr,urlAttributes)

	poolResult.append(pool.apply_async(lambda url:urlrequest(url)['entities'], (url, )))

	PaperJsonList = [aJson for result in poolResult for aJson in result.get()]

	print 'getPaperJsonList time =', time.time() - now
	return PaperJsonList

def getAuthorPaperList(auidList, urlAttributes):
	if auidList == []:
		return []
	now = time.time()
	authorPaperList = []
	poolResult = []
	L = 0
	expr = ''
	for auid in auidList:
		if expr == '':
			expr = 'Composite(AA.AuId=%d)'%auid
			L = len(expr)
		elif L + len(str(auid)) + 24 <= 1800:
			expr = 'Or(%s,Composite(AA.AuId=%d))'%(expr,auid)
			L += len(str(auid)) + 24
		else:
			url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=%s&count=100000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(expr,urlAttributes)
			poolResult.append(pool.apply_async(lambda url:urlrequest(url)['entities'], (url, )))

			expr = 'Composite(AA.AuId=%d)'%auid
			L = len(expr)

	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=%s&count=100000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(expr,urlAttributes)
	poolResult.append(pool.apply_async(lambda url:urlrequest(url)['entities'], (url, )))

	#for result in poolResult:
	#	paperList = result.get()
	#	for aPaper in paperList:
	#		authorPaperList.append(aPaper)
	authorPaperList = [aPaper for result in poolResult for aPaper in result.get()]

	print 'getAuthorPaperList time =', time.time() - now
	return authorPaperList

def join(l1, l2): # join two sorted list
	#now = time.time()
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
	#print 'join', n1, n2, time.time() - now
	return ret

def getId2Cited(id, CC, urlAttributes):
	now = time.time()
	Id2citedResult = []
	off = 0;
	cnt = max(CC / 10, 3000);
	#cnt = 2000000
	while off < CC:
		url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=RId=%d&count=%d&offset=%d&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id,cnt,off,urlAttributes)
		#print url
		Id2citedResult.append(pool.apply_async(lambda url:urlrequest(url)['entities'], (url,)))
		off += cnt

	Id2cited = []
	for eachResult in Id2citedResult:
		Id2cited.extend(eachResult.get())

	print 'getId2Cited time =', time.time() - now
	print 'len(Id2cited) =', len(Id2cited)
	return Id2cited

def query_Id_Id_small(id1, id2, json1, json2):
	print 'query_Id_Id_small', id1, id2
	ans = []

	now = time.time()
	
	if 'RId' in json1:
		urlAttributes = 'Id,RId'
		if 'F' in json2:
			urlAttributes += ',F.FId'
		if 'J' in json2:
			urlAttributes += ',J.JId'
		if 'C' in json2:
			urlAttributes += ',C.CId'
		if 'AA' in json2:
			urlAttributes += ',AA.AuId'
		id1CitePapersInfo = getPaperJsonList(json1['RId'], urlAttributes)

	# =========== 1-hop =========== 

	# Id-Id
	if 'RId' in json1 and id2 in json1['RId']:
		ans.append([id1, id2])

	# =========== 2-hop =========== 

	# Id-F.FId-Id
	if 'F' in json1:
		FIdList1 = map(lambda x:x['FId'], json1['F'])
		FIdList1.sort()
	if 'F' in json2:
		FIdList2 = map(lambda x:x['FId'], json2['F'])
		FIdList2.sort()		
	if 'F' in json1 and 'F' in json2:
		jointFIdList = join(FIdList1, FIdList2)
		ans.extend([[id1, x, id2] for x in jointFIdList])
			

	# Id-J.JId-Id
	if 'J' in json1 and 'J' in json2 and json1['J']['JId'] == json2['J']['JId']:
		ans.append([id1, json1['J']['JId'], id2])

	# Id-C.CId-Id
	if 'C' in json1 and 'C' in json2 and json1['C']['CId'] == json2['C']['CId']:
		ans.append([id1, json1['C']['CId'], id2])

	# Id-AA.AuId-Id
	if 'AA' in json1:
		AuIdList1 = map(lambda x:x['AuId'], json1['AA'])
		AuIdList1.sort()
	if 'AA' in json2:
		AuIdList2 = map(lambda x:x['AuId'], json2['AA'])
		AuIdList2.sort()
	if 'AA' in json1 and 'AA' in json2:
		jointAuIdList = join(AuIdList1, AuIdList2)
		ans.extend([[id1, x, id2] for x in jointAuIdList])
			

	# Id-Id-Id
	if 'CC' in json2:
		Id2cited = getId2Cited(id2, json2['CC'], 'Id,F.FId,J.JId,C.CId,AA.AuId')
	else:
		Id2cited = []
	if 'RId' in json1:
		RIdList = json1['RId']
		#RIdSet = set(RIdList)
		Id2citedSet = set()
		map(lambda x:Id2citedSet.add(x['Id']), Id2cited)
		#Id2citedList = map(lambda x:x['Id'], Id2cited)
		#Id2citedSet = set(Id2citedList)
		#RIdList.sort()
		#Id2citedList.sort()
		#map(lambda x: ans.append([id1, x, id2]) if x in Id2citedSet else None, RIdList)
		for RId in RIdList:
			if RId in Id2citedSet:
				ans.append([id1, RId, id2])
		#jointRIdList = join(RIdList, Id2citedList)
		#ans.extend([[id1, x, id2] for x in jointRIdList])
		#ans.extend([[id1, x, id2] for x in Id2citedSet.intersection(RIdSet)])
			

	# =========== 3-hop =========== 

	# Id-*-Id-Id
	if len(Id2cited) != 0:
		# Id-F.FId-Id-Id
		if 'F' in json1:
			for paper in Id2cited:
				if 'F' in paper:
					for F_element in paper['F']:
						if F_element['FId'] in FIdList1:
							ans.append([id1, F_element['FId'], paper['Id'], id2])

		# Id-J.JId-Id-Id
		if 'J' in json1:
			for paper in Id2cited:
				if 'J' in paper and paper['J']['JId'] == json1['J']['JId']:
					ans.append([id1, json1['J']['JId'], paper['Id'], id2])

		# Id-C.CId-Id-Id
		if 'C' in json1:
			for paper in Id2cited:
				if 'C' in paper and paper['C']['CId'] == json1['C']['CId']:
					ans.append([id1, json1['C']['CId'], paper['Id'], id2])
		
		# Id-AA.AuId-Id-Id
		if 'AA' in json1:
			for paper in Id2cited:
				if 'AA' in paper:
					for AA_element in paper['AA']:
						if AA_element['AuId'] in AuIdList1:
							ans.append([id1, AA_element['AuId'], paper['Id'], id2])

	# Id-Id-*-Id
	if 'RId' in json1:
		if 'F' in json2:
			for id1CitePaper in id1CitePapersInfo:
				if 'F' in id1CitePaper:
					FIdListTmp = map(lambda x:x['FId'], id1CitePaper['F'])
					FIdListTmp.sort()
					jointFIdList = join(FIdListTmp, FIdList2)
					ans.extend([[id1, id1CitePaper['Id'], x, id2] for x in jointFIdList])
						

		# Id-Id-J.JId-Id
		if 'J' in json2:
			for id1CitePaper in id1CitePapersInfo:
				if 'J' in id1CitePaper and id1CitePaper['J']['JId'] == json2['J']['JId']:
					ans.append([id1, id1CitePaper['Id'], json2['J']['JId'], id2])

		# Id-Id-C.CId-Id
		if 'C' in json2:
			for id1CitePaper in id1CitePapersInfo:
				if 'C' in id1CitePaper and id1CitePaper['C']['CId'] == json2['C']['CId']:
					ans.append([id1, id1CitePaper['Id'], json2['C']['CId'], id2])

		# Id-Id-AA.AuId-Id
		if 'AA' in json2:
			for id1CitePaper in id1CitePapersInfo:
				if 'AA' in id1CitePaper:
					AuIdListTmp = map(lambda x:x['AuId'], id1CitePaper['AA'])
					AuIdListTmp.sort()
					jointAuIdList = join(AuIdListTmp, AuIdList2)
					ans.extend([[id1, id1CitePaper['Id'], x, id2] for x in jointAuIdList])
						

		# Id-Id-Id-Id
		tmp = len(ans)
		for id1CitePaper in id1CitePapersInfo:
			if 'RId' in id1CitePaper:
				RIdListTmp = id1CitePaper['RId']
				#RIdListTmp.sort()
				#map(lambda x:ans.extend([id1, id1CitePaper['Id'], x, id2]) if x in Id2citedSet else None, RIdListTmp)
				for RId in RIdListTmp:
					if RId in Id2citedSet:
						ans.append([id1, id1CitePaper['Id'], RId, id2])
				#jointRIdList = join(RIdListTmp, Id2citedList)
				#ans.extend([[id1, id1CitePaper['Id'], x, id2] for x in jointRIdList])
					

	return ans

def query_AuId_Id(auId1, id2, json1, json2):
	#sys.stderr.write('query_AuId_Id ' + str(auId1) + ' ' + str(id2) + '\n')
	print 'query_AuId_Id', auId1, id2
	ans = []
	
	now = time.time()

	# =========== 1-hop =========== 

	# AuId-Id
	for paper in json1:
		if paper['Id'] == id2:
			ans.append([auId1, id2])
			break


	# =========== 2-hop =========== 

	# AuId-Id-Id
	for paper in json1:
		if 'RId' in paper and (id2 in paper['RId']):
			ans.append([auId1, paper['Id'], id2])

	# =========== 3-hop =========== 

	# AuId-Id-F.FId-Id
	if 'F' in json2:
		FIdList2 = map(lambda x:x['FId'], json2['F'])
		FIdList2.sort()
		for paper in json1:
			if 'F' in paper:
				FIdListTmp = map(lambda x:x['FId'], paper['F'])
				FIdListTmp.sort()
				jointFIdList = join(FIdListTmp, FIdList2)
				ans.extend([[auId1, paper['Id'], x, id2] for x in jointFIdList])
					

	# AuId-Id-C.CId-Id
	if 'C' in json2:
		CId2 = json2['C']['CId']
		for paper in json1:
			if 'C' in paper and paper['C']['CId'] == CId2:
				ans.append([auId1, paper['Id'], CId2, id2])

	# AuId-Id-J.JId-Id
	if 'J' in json2:
		JId2 = json2['J']['JId']
		for paper in json1:
			if 'J' in paper and paper['J']['JId'] == JId2:
				ans.append([auId1, paper['Id'], JId2, id2])

	# AuId-Id-AA.AuId-Id
	if 'AA' in json2:
		AuIdList2 = map(lambda x:x['AuId'], json2['AA'])
		AuIdList2.sort()
		for paper in json1:
			if 'AA' in paper:
				AuIdListTmp = map(lambda x:x['AuId'], paper['AA'])
				AuIdListTmp.sort()
				jointAuIdList = join(AuIdListTmp, AuIdList2)
				ans.extend([[auId1, paper['Id'], x, id2] for x in jointAuIdList])

	# AuId-Id-Id-Id
	if 'CC' in json2:
		Id2cited = getId2Cited(id2, json2['CC'], 'Id')
	else:
		Id2cited = []
	if len(Id2cited) > 0:
		Id2citedSet = set()
		map(lambda x:Id2citedSet.add(x['Id']), Id2cited)
		#Id2citedList = map(lambda x:x['Id'], Id2cited)
		#Id2citedList.sort()
		for paper in json1:
			if 'RId' in paper:
				RIdListTmp = paper['RId']
				#map(lambda x:ans.append([auId1, paper['Id'], x, id2]) if x in Id2citedSet else None, RIdListTmp)
				for RId in RIdListTmp:
					if RId in Id2citedSet:
						ans.append([auId1, paper['Id'], RId, id2])
				#RIdListTmp.sort()
				#jointRIdList = join(RIdListTmp, Id2citedList)
				#ans.extend([[auId1, paper['Id'], x, id2] for x in jointRIdList])
					

	# AuId-AA.AFId-AA.AuId-Id
	AFIdSet1 = set()
	for paper in json1:
		if 'AA' in paper:
			for author in paper['AA']:
				if author['AuId'] == auId1 and 'AfId' in author:
					AFIdSet1.add(author['AfId'])
	if len(AFIdSet1) > 0 and 'AA' in json2:
		authorPaperList = getAuthorPaperList(map(lambda x:x['AuId'], json2['AA']), 'AA.AuId,AA.AfId')
		authorSet2 = set()
		map(lambda x:authorSet2.add(x['AuId']), json2['AA'])
		uniqueSet = set()
		for paper in authorPaperList:
			if 'AA' in paper:
				for author in paper['AA']:
					auId2 = author['AuId']
					if (auId2 in authorSet2) and ('AfId' in author) and (author['AfId'] in AFIdSet1) and not((author['AfId'], auId2) in uniqueSet):
						ans.append([auId1, author['AfId'], auId2, id2])
						uniqueSet.add((author['AfId'], auId2))
	#print 'AuId-AfId-AuId-Id finished time =', time.time() - now

	return ans

def query_Id_AuId(id1, auId2, json1, json2):
	print 'query_Id_AuId', id1, auId2
	ans = []
	
	paperIdSet = set()
	map(lambda x:paperIdSet.add(x['Id']), json2)
	#paperIdList = map(lambda x:x['Id'], json2)
	#paperIdList.sort()

	# =========== 1-hop ===========

	# Id-AuId
	if 'AA' in json1 and (auId2 in map(lambda x:x['AuId'], json1['AA'])):
		ans.append([id1, auId2])

	# =========== 2-hop ===========

	# Id-Id-AuId
	if 'RId' in json1:
		RIdList = json1['RId']
		#map(lambda x:ans.append([id1, x, auId2]) if x in paperIdSet else None, RIdList)
		for RId in RIdList:
			if RId in paperIdSet:
				ans.append([id1, RId, auId2])
		#RIdList.sort()
		#jointRIdList = join(paperIdList, RIdList)
		#ans.extend([[id1, x, auId2] for x in jointRIdList])
			

	# =========== 3-hop ===========

	# Id-F.FId-Id-AuId
	if 'F' in json1:
		FIdList1 = map(lambda x:x['FId'], json1['F'])
		FIdList1.sort()
		for paper in json2:
			if 'F' in paper:
				FIdListTmp = map(lambda x:x['FId'], paper['F'])
				FIdListTmp.sort()
				jointFIdList = join(FIdListTmp, FIdList1)
				ans.extend([[id1, x, paper['Id'], auId2] for x in jointFIdList])

	# Id-C.CId-Id-AuId
	if 'C' in json1:
		CId1 = json1['C']['CId']
		for paper in json2:
			if 'C' in paper and paper['C']['CId'] == CId1:
				ans.append([id1, CId1, paper['Id'], auId2])

	# Id-J.JId-Id-AuId
	if 'J' in json1:
		JId1 = json1['J']['JId']
		for paper in json2:
			if 'J' in paper and paper['J']['JId'] == JId1:
				ans.append([id1, JId1, paper['Id'], auId2])

	# Id-AA.AuId-Id-AuId
	if 'AA' in json1:
		AuIdList1 = map(lambda x:x['AuId'], json1['AA'])
		AuIdList1.sort()
		for paper in json2:
			if 'AA' in paper:
				AuIdListTmp = map(lambda x:x['AuId'], paper['AA'])
				AuIdListTmp.sort()
				jointAuIdList = join(AuIdListTmp, AuIdList1)
				ans.extend([[id1, x, paper['Id'], auId2] for x in jointAuIdList])
					

	# Id-Id-Id-AuId
	if 'RId' in json1:
		#citePaperInfoResults = pool.map_async(lambda x:getPaperJson(x, 'RId,Id'), RIdList)
		#pool.close()
		#pool.join()
		#citePaperInfos = citePaperInfoResults.get()
		citePaperInfos = getPaperJsonList(RIdList, 'RId,Id')
		for citePaperInfo in citePaperInfos:
			if 'RId' in citePaperInfo:
				RIdListTmp = citePaperInfo['RId']
				#map(lambda x:ans.append([id1, citePaperInfo['Id'], x, auId2]) if x in paperIdSet else None, RIdListTmp)
				for RId in RIdListTmp:
					if RId in paperIdSet:
						ans.append([id1, citePaperInfo['Id'], RId, auId2])
				#RIdListTmp.sort()
				#jointRIdList = join(RIdListTmp, paperIdList)
				#ans.extend([[id1, citePaperInfo['Id'], x, auId2] for x in jointRIdList])

	# Id-AA.AuId-AA.AfId-AuId
	AFIdSet2 = set()
	for paper in json2:
		if 'AA' in paper:
			for author in paper['AA']:
				if author['AuId'] == auId2 and 'AfId' in author:
					AFIdSet2.add(author['AfId'])
	if len(AFIdSet2) > 0 and 'AA' in json1:
		authorPaperList = getAuthorPaperList(map(lambda x:x['AuId'], json1['AA']), 'AA.AuId,AA.AfId')
		authorSet1 = set()
		map(lambda x: authorSet1.add(x['AuId']), json1['AA'])
		uniqueSet = set()
		for paper in authorPaperList:
			if 'AA' in paper:
				for author in paper['AA']:
					auId1 = author['AuId']
					if (auId1 in authorSet1) and 'AfId' in author and (author['AfId'] in AFIdSet2) and not((auId1, author['AfId']) in uniqueSet):
						ans.append([id1, auId1, author['AfId'], auId2])
						uniqueSet.add((auId1, author['AfId']))

	return ans

def query_AuId_AuId(auId1, auId2, json1, json2):
	sys.stderr.write('query_AuId_AuId ' + str(auId1) + ' ' + str(auId2) + '\n')
	ans = []

	# =========== 2-hop ===========
	AFIdSet1 = set()
	IdSet1 = set()
	for paper1 in json1:
		if 'AA' in paper1:
			for i in paper1['AA']:
				if 'AfId' in i and i['AuId'] == auId1:
					AFIdSet1.add(i['AfId'])
		if 'Id' in paper1:
			IdSet1.add(paper1['Id'])
	#IdList1.sort()

	AFIdSet2 = set()
	IdSet2 = set()
	for paper2 in json2:
		if 'AA' in paper2:
			for i in paper2['AA']:
				if 'AfId' in i and i['AuId'] == auId2:
					AFIdSet2.add(i['AfId'])
		if 'Id' in paper2:
			IdSet2.add(paper2['Id'])
	#IdList2.sort()

	#AuId-AFId-AuId
	if len(AFIdSet1)>0 and len(AFIdSet2)>0:
		# AFIdList1.sort()
		# AFIdList2.sort()
		# jointAFIdList = join(AFIdList1, AFIdList2)
		# jointAFIdList = np.intersect1d(AFIdList1, AFIdList2)
		jointAFIdSet = AFIdSet1.intersection(AFIdSet2)
		# for AFId in jointAFIdList:
		ans.extend([[auId1, x, auId2] for x in jointAFIdSet])
	#AuId-Id-AuId
	if len(IdSet1)>0 and len(IdSet2)>0:
		jointIdSet = IdSet1.intersection(IdSet2)
		ans.extend([[auId1, x, auId2] for x in jointIdSet])
		#jointIdList = join(IdList1, IdList2)
		#ans.extend([[auId1, x, auId2] for x in jointIdList])
	
	# =========== 3-hop ===========

	# AuId-Id-Id-AuId
	for paper1 in json1:
		if 'RId' in paper1:
			RIdList = paper1['RId']
			#map(lambda x:ans.append([auId1, paper1['Id'], x, auId2]) if x in IdSet2 else None, RIdList)
			for RId in RIdList:
				if RId in IdSet2:
					ans.append([auId1, paper1['Id'], RId, auId2])
			#RIdList.sort()
			#jointList = join(RIdList, IdList2)
			#ans.extend([[auId1, paper1['Id'], x, auId2] for x in jointList])
	return ans

def query(id1, id2):
	now = time.time()

	json1 = []
	json2 = []
	paperJson1 = []
	paperJson2 = []
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Or(Or(Or(Composite(AA.AuId=%d),Composite(AA.AuId=%d)),Id=%d),Id=%d)&count=100000&attributes=Id,RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId,CC&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id1,id2,id1,id2)
	mix = urlrequest(url)['entities']
	print 'init get time =', time.time() - now
	for ele in mix:
		if 'AA' in ele:
			AuIdList = map(lambda x:x['AuId'], ele['AA'])
			if id1 in AuIdList:
				json1.append(ele)
			if id2 in AuIdList:
				json2.append(ele)
		if ele['Id'] == id1:
			paperJson1.append(ele)
		if ele['Id'] == id2:
			paperJson2.append(ele)
	print 'init time =', time.time() - now
	
	if json1 and json2:
		return query_AuId_AuId(id1, id2, json1, json2)
	elif json1:
		return query_AuId_Id(id1, id2, json1, paperJson2[0])
	elif json2:
		return query_Id_AuId(id1, id2, paperJson1[0], json2)
	else:
		return query_Id_Id_small(id1, id2, paperJson1[0], paperJson2[0])
		#paperJson1 = paperJson1[0]
		#paperJson2 = paperJson2[0]
		#if 'CC' in paperJson2 and paperJson2['CC'] >= 50000:
		#	return query_Id_Id_big(id1, id2, paperJson1, paperJson2)
		#else:
		#	return query_Id_Id_small(id1, id2, paperJson1, paperJson2)			

def main(id1, id2):
	#query(2140190241, 1514498087)
	#query(2140190241, 1490955312)
	#query(2126125555, 2153635508)
	#query(2126125555, 2060367530)
	#query(2140190241, 2121939561)
	#query(2175015405, 1514498087)
	#print query(2251253715,2180737804)
	#print len(query(2100837269, 621499171))
	print len(query(id1, id2))
	now = time.time()
	print len(query(id1, id2))
	#print len(query(2140619391,2044675247))
	print time.time() - now

if __name__ == '__main__':
    main(int(sys.argv[1]), int(sys.argv[2]))
