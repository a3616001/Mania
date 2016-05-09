from flask import Flask, request, jsonify
import json
import os
from query_map import *
import time
app = Flask(__name__)


@app.route('/maniarest')
def call():
    id1 = request.args.get('id1')
    id2 = request.args.get('id2')
#    print id1, id2
    # os.system('./program {} {}'.format(id1, id2))
#    ans = []
#    with open('test.out', 'r') as f:
#        for line in f:
#            ans.append([_ for _ in map(int, line.split())])
    now = time.time()
#    import profile
#    profile.run('query(int({}), int({}))'.format(id1, id2))
    ans = query(int(id1), int(id2))
    print 'Answer Number = ', len(ans)
    print "time: {}".format(time.time() - now)
    return json.dumps(ans)


if __name__ == "__main__":
    #app.debug = True
    app.run(host = '0.0.0.0', port=80)
