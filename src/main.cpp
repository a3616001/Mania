#include <iostream>
#include <cstdlib>
#include <cstring>
#include <string>

#include "httplib.h"

using namespace std;

int main()
{
	Request request("https://oxfordhk.azure-api.net/academic/v1.0/evaluate");
	request.addheader("expr", "Composite(AA.AuN=='jiawei%20han')");
	request.addheader("count", "10");
	request.addheader("attributes", "Id,Ti,CC,AA.AuId,AA.AfId");
	request.addheader("orderby", "CC:desc");
	request.addheader("subscription-key", "f7cc29509a8443c5b3a5e56b0e38b5a6");
	string result = urlopen(request);
	cout << string << endl;
	return 0;
}
