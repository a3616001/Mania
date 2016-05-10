from libcpp.vector cimport vector

cpdef join(l1, l2): # join two sorted list
	cdef int n1, n2
	cdef long long p1, p2
	n1 = len(l1)
	n2 = len(l2)
	p1 = 0
	p2 = 0
	cdef vector[long long] ret
	while p1 < n1 and p2 < n2:
		if l1[p1] < l2[p2]:
			p1 += 1
		elif l1[p1] > l2[p2]:
			p2 += 1
		else:
			ret.push_back(l1[p1])
			p1 += 1
			p2 += 1
	return ret
	 