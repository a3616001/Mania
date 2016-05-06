import urllib
import json
import sys

def answer(ans, path):
	print path
	ans.append(path)

def getPaperJson(id, urlAttributes):
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Id=%d&count=1000&attributes=%s&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%(id,urlAttributes)
	sys.stderr.write(url + '\n')
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

def query_Id_Id(id1, id2):
	ans = []
	json1 = getPaperJson(id1, 'RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId')
	json2 = getPaperJson(id2, 'F.FId,J.JId,C.CId,AA.AuId,AA.AfId')
	#print json1['RId']
	#print json2

	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=RId=%d&count=200000&attributes=Id,F.FId,J.JId,C.CId,AA.AuId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
	#url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=And(RId=2060367530,Composite(F.FId=41008148))&count=200000&attributes=Id,F.FId,J.JId,C.CId,AA.AuId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'
	Id2cited = json.loads(urllib.urlopen(url).read())['entities']

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
		# Id-F.FId-Id-Id
		if json1.has_key('F'):
			for paper in Id2cited:
				if paper.has_key('F'):
					for F_element in paper['F']:
						if F_element['FId'] in FIdList1:
							answer(ans, [id1, F_element['FId'], paper['Id'], id2])

		# Id-J.JId-Id-Id
		if json1.has_key('J'):
			for paper in Id2cited:
				if paper.has_key('J') and paper['J']['JId'] == json1['J']['JId']:
					answer(ans, [id1, json1['J']['JId'], paper['Id'], id2])

		# Id-C.CId-Id-Id
		if json1.has_key('C'):
			for paper in Id2cited:
				if paper.has_key('C') and paper['C']['CId'] == json1['C']['CId']:
					answer(ans, [id1, json1['C']['CId'], paper['Id'], id2])

		# Id-AA.AuId-Id-Id
		if json1.has_key('AA'):
			for paper in Id2cited:
				if paper.has_key('AA'):
					for AA_element in paper['AA']:
						if AA_element['AuId'] in AuIdList1:
							answer(ans, [id1, AA_element['AuId'], paper['Id'], id2])

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

		id1CitePapersInfo = map(lambda x:getPaperJson(x, urlAttributes), json1['RId'])

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
		#for id1CitePaper in id1CitePapersInfo:
		for id1CitePaper in id1CitePapersInfo:
			if id1CitePaper.has_key('RId'):
				RIdListTmp = id1CitePaper['RId']
				RIdListTmp.sort()
				jointRIdList = join(RIdListTmp, Id2citedList)
				for RId in jointRIdList:
					answer(ans, [id1, id1CitePaper['Id'], RId, id2])

	# return ans
	return ans

def query(id1, id2):
	return query_Id_Id(id1, id2)

def main():
	#query(2140190241, 1514498087)
	#query(2140190241, 1490955312)
	query(2126125555, 2153635508)
	#query(2126125555, 2060367530)
	#query(2140190241, 2121939561)

if __name__ == '__main__':
    main()
