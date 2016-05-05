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

def query_Id_Id(id1, id2):

	json1 = getPaperJson(id1)
	json2 = getPaperJson(id2)
	#print json1['RId']
	#print json2

	# 1-hop

	# Id-Id
	if id2 in json1['RId']:
		answer((id1, id2))

	# 2-hop

	# Id-F.FId-Id
	# TODO

	# Id-J.JId-Id
	# TODO

	# Id-C.CId-Id
	# TODO

	# Id-AA.AuId-Id
	# TODO



def query(id1, id2):
	query_Id_Id(id1, id2)

def main():
	#query(2140190241, 1514498087)
	query(2140190241, 1490955312)

if __name__ == '__main__':
    main()
