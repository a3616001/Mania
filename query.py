import urllib
import json
import sys

def answer(path):
	print path

def getPaperJson(id):
	url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=Id=%d&count=1000&attributes=RId,F.FId,J.JId,C.CId,AA.AuId,AA.AfId&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id
	f = urllib.urlopen(url)
	result = json.loads(f.read())
	return result['entities'][0]

def join(l1, l2):
	n1 = len(l1)
	n2 = len(l2)
	l1.sort()
	l2.sort()
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

	json1 = getPaperJson(id1)
	json2 = getPaperJson(id2)
	#print json1['RId']
	#print json2

	# =========== 1-hop =========== 

	# Id-Id
	if json1.has_key('RId') and id2 in json1['RId']:
		answer((id1, id2))

	# =========== 2-hop =========== 

	# Id-F.FId-Id
	if json1.has_key('F') and json2.has_key('F'):
		FIdList1 = map(lambda x:x['FId'], json1['F'])
		FIdList2 = map(lambda x:x['FId'], json2['F'])
		jointFIdList = join(FIdList1, FIdList2)
		for FId in jointFIdList:
			answer(id1, FId, id2)

	# Id-J.JId-Id
	if json1.has_key('J') and json2.has_key('J') and json1['J']['JId'] == json2['J']['JId']:
		answer((id1, json1['J']['JId'], id2))

	# Id-C.CId-Id
	if json1.has_key('C') and json2.has_key('C') and json1['C']['CId'] == json2['C']['CId']:
		answer((id1, json1['C']['CId'], id2))

	# Id-AA.AuId-Id
	if json1.has_key('AA') and json2.has_key('AA'):
		AuIdList1 = map(lambda x:x['AuId'], json1['AA'])
		AuIdList2 = map(lambda x:x['AuId'], json2['AA'])
		jointAuIdList = join(AuIdList1, AuIdList2)
		for AuId in jointAuIdList:
			answer((id1, AuId, id2))

	# Id-Id-Id
	# TODO 根据 year cite 等优化
	if json1.has_key('RId'):
		RIdList = json1['RId']
		url = 'https://oxfordhk.azure-api.net/academic/v1.0/evaluate?expr=RId=%d&count=10000&attributes=Id&subscription-key=f7cc29509a8443c5b3a5e56b0e38b5a6'%id2
		Id2cited = json.loads(urllib.urlopen(url).read())['entities']
		Id2citedList = map(lambda x:x['Id'], Id2cited)
		jointRIdList = join(RIdList, Id2citedList)
		for RId in jointRIdList:
			answer((id1, RId, id2))

	# =========== 3-hop =========== 
	# Id-F.FId-Id-Id

	# Id-J.JId-Id-Id

	# Id-C.CId-Id-Id

	# Id-AA.AuId-Id-Id

	# Id-Id-F.FId-Id

	# Id-Id-J.JId-Id

	# Id-Id-C.CId-Id

	# Id-Id-AA.AuId-Id

	# Id-Id-Id-Id

def query(id1, id2):
	query_Id_Id(id1, id2)

def main():
	#query(2140190241, 1514498087)
	#query(2140190241, 1490955312)
	#query(2126125555, 2153635508)
	query(2126125555, 2060367530)

if __name__ == '__main__':
    main()
