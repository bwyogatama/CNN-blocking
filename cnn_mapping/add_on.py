from mapping_point import MappingPoint
import loop_enum as le
import h5py


import copy
import time
import math
from collections import OrderedDict
from operator import add
import numpy as np
from collections import Iterable

def get_PE_values(point,resource):

	blocking = zip(*point.loop_blockings)
	partitioning = zip(*point.loop_partitionings)
	order = zip(*point.loop_orders)
	para_dim = list(point.para_loop_dim)

	num_level = resource.buffer_levels()
	num_loop = le.NUM

	blocking_reshape = []
	partitioning_reshape = []
	order_reshape = []
	para_dim_reshape = []

	for i in xrange(num_level):
		blocking_reshape.append(list(blocking[num_level-1-i]))
		partitioning_reshape.append(list(partitioning[num_level-1-i]))
		order_reshape.append(list(order[num_level-1-i]))
		para_dim_reshape.append(para_dim[num_level-1-i])
	
	arrange_order(order_reshape,num_level,num_loop)

	new_partitioning = []
	new_blocking = []
	new_ordering1 = {}
	new_ordering2 = {}

	arrange_bp(partitioning_reshape,blocking_reshape,order_reshape,para_dim_reshape,num_level,num_loop,new_partitioning,new_blocking)
	make_ordering_dict(order_reshape,num_level,num_loop,new_ordering1, new_ordering2)

	'''
	print blocking_reshape
	print partitioning_reshape
	print order_reshape
	print para_dim_reshape
	print new_blocking
	print new_partitioning
	print new_ordering1
	print new_ordering2
	'''
	
	tile_blocking = []
	tile_partitioning = []
	tile_bi = []
	tile_pi = []
	tile_po = []
	tile_dict = {}
	optim_block = {}

	start = time.time()
	opt_generate_loop_partitioning(new_ordering1, new_blocking, new_partitioning, 0, -1, num_loop, num_level, tile_partitioning, tile_pi, tile_po)
	opt_pre_block_generate_loop(new_ordering1, new_blocking, new_partitioning, optim_block)
	opt_generate_loop_blocking(new_ordering1, new_blocking, new_partitioning, optim_block, 0, -1, num_loop, num_level, tile_blocking, tile_bi)
	end = time.time()
	print (end-start)

	#print "tile_pi: ",tile_pi[len(tile_pi)-1]
	#print "tile_po: ",tile_po[len(tile_po)-1]
	#print "tile_bi: ",tile_bi[len(tile_bi)-1]

	array_width= 16

	for i in xrange(num_level):
		if para_dim_reshape[i] != None:
			cur_level = i
			break

	if len(para_dim_reshape[cur_level])>2:
		finish = 0
		while (finish==0):
			x_input = input("Unrolled loop in the x dimension: ")
			y_input = input("Unrolled loop in the y dimension: ")
			para_dim_new = para_dim_reshape
			para_dim_new[cur_level] = []

			if isinstance(x_input,Iterable)==False:
				x_input = [x_input]
			else:
				x_input = list(x_input)

			para_dim_new[cur_level].append(x_input)

			if isinstance(y_input,Iterable)==False:
				y_input = [y_input]
			else:
				y_input = list(y_input)
			
			para_dim_new[cur_level].append(y_input)
			print "para_dim = ",para_dim_new
			temp = raw_input("Continue? (y/n): ")

			if temp=='y':
				finish=1
			elif temp=='n':
				print ("Enter the inputs once again: ")
				finish=0
			else:
				print("Incorrect input")
				finish=0

	elif len(para_dim_reshape[cur_level])==1:
		para_dim_new = para_dim_reshape
		para_dim_new[cur_level] = para_dim_reshape[cur_level].append([1])
		print "para_dim = ",para_dim_new
	else:
		para_dim_new = para_dim_reshape
		print "para_dim = ",para_dim_new

	finish = 0
	while (finish==0):
		coordinate = input("Enter PE Coordinate: ")
		result = solveit(coordinate, array_width, para_dim_new, partitioning_reshape, cur_level, new_ordering1, num_loop)
		#print result
		if result[0] == None:
			print ("The selected PE does not perform any computation, please enter another PE coordinate")
			continue
		result = tile_pi[tile_po.index(result)]
		result = np.tile((result),(len(tile_bi),1))
		tile_result = np.add(tile_bi,result)
		print
		print
		print tile_result

		h5f = h5py.File('result'+str(coordinate)+'.h5', 'w')
		h5f.create_dataset('result', data=tile_result)
		h5f.close()

		temp = raw_input("Again? (y/n): ")

		if temp=='y':
			finish=0
		elif temp=='n':
			finish=1
		else:
			print("Incorrect input")
			finish=0	

	del tile_bi
	del tile_pi
	del tile_po
	del tile_result

#start cur_loop = -1
def opt_generate_loop(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking = [], tile_partitioning = [], tile_bi = [], tile_pi = []):

	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		tile_b = []
		tile_p = []
		for key in order:
			add_b = 0
			add_p = 0
			for i in xrange(len(order[key])):
				mul_b = 1
				mul_p = 1
				for j in xrange(i+1,len(order[key])):
					mul_b = mul_b*(blocking[j][key])
					mul_p = mul_p*(partitioning[j][key])
				add_b = add_b+mul_b*(tile_blocking[order[key][i]]-1)
				add_p = add_p+mul_p*(tile_partitioning[order[key][i]]-1)
			tile_b.append(add_b)
			tile_p.append(add_p+1)

		tile_bi.append(tile_b)
		tile_pi.append(tile_p)
		#tile_pi.append(tile_partitioning[((num_level-1)*num_loop):])

		del tile_blocking
		del tile_partitioning
		del tile_b
		del tile_p
		
	else:
		if cur_loop == num_loop-1:
			cur_level = cur_level+1
			cur_loop = 0
		else:
			cur_loop = cur_loop+1
		tile_partitioning_temp = tile_partitioning
		tile_blocking_temp = tile_blocking
		for par in xrange(partitioning[cur_level][cur_loop]):
			tile_partitioning = copy.copy(tile_partitioning_temp)
			tile_partitioning.append(par+1)
			for block in xrange(blocking[cur_level][cur_loop]):
				tile_blocking=copy.copy(tile_blocking_temp)
				tile_blocking.append(block+1)
				opt_generate_loop(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_partitioning, tile_bi, tile_pi)
	

def opt_generate_loop_blocking(order, blocking, partitioning, optim_block, cur_level, cur_loop, num_loop, num_level, tile_blocking = [], tile_bi = []):

	#print cur_level, cur_loop
	#print tile_blocking 
	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		tile_b = []
		y = num_loop-1
		#tile_b = [1,]*num_loop
		for key in order:
			add = 0
			for i in xrange(len(order[key])):
				add = add+optim_block[key][i]*(tile_blocking[num_loop*i+y-order[key][i]]-1)
			tile_b.append(add)	
			#tile_b[num_loop-1-key] = add

		#tile_bo.append(tile_blocking)
		tile_bi.append(tile_b)

		del tile_blocking
		del tile_b

	else:
		if cur_loop == num_loop-1:
			cur_level = cur_level+1
			cur_loop = 0
		else:
			cur_loop = cur_loop+1

		tile_blocking_temp = tile_blocking
		for block in xrange(blocking[cur_level][cur_loop]):
			tile_blocking=copy.copy(tile_blocking_temp)
			tile_blocking.append(block+1)
			opt_generate_loop_blocking(order, blocking, partitioning, optim_block, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_bi)
	

def opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning = [], tile_pi = [], tile_po = []):

	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		tile_p = []
		tile_pn = []
		#tile_p = [1,]*num_loop
		for key in order:
			add = 0
			add2 = 0
			for i in xrange(len(order[key])):
				mul = 1
				mul2 = 1
				for j in xrange(i,len(order[key])):
					if (j+1==num_level):
						x=1
					else:
						x=partitioning[j+1][num_loop-1-order[key][j]]
					mul = mul*(blocking[j][num_loop-1-order[key][j]])*x
					mul2 = mul2*x
				add = add+mul*(tile_partitioning[num_loop*i+num_loop-1-order[key][i]]-1)
				add2 = add2+mul2*(tile_partitioning[num_loop*i+num_loop-1-order[key][i]]-1)
			tile_p.append(add)
			tile_pn.append(add2)
			#tile_p[num_loop-1-key]=add

		#tile_po.append(tile_partitioning)
		tile_pi.append(tile_p)
		tile_po.append(tile_pn)

		del tile_p
		del tile_pn
		del tile_partitioning
		
	else:
		if cur_loop == num_loop-1:
			cur_level = cur_level+1
			cur_loop = 0
		else:
			cur_loop = cur_loop+1
		tile_partitioning_temp = tile_partitioning
		for par in xrange(partitioning[cur_level][cur_loop]):
			tile_partitioning = copy.copy(tile_partitioning_temp)
			tile_partitioning.append(par+1)
			opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning, tile_pi, tile_po)

def opt_post_generate_loop(tile_bi,tile_pi):
	tile_px = []

	for i in xrange(len(tile_pi)):
		tile_px.append(tuple(tile_pi[i]))

	tile_dict = dict.fromkeys(tile_px)

	for key in tile_dict:
		tile_dict[key]=[]

	for key in tile_dict:
		for j in tile_bi:
			tile_dict[key].append(list(map(add,list(key),j)))

	return tile_dict	

def opt_pre_block_generate_loop(order, blocking, partitioning, optim_block):
	num_loop = len(order)
	for key in order:
		optim_block[key] = []
		for i in xrange(len(order[key])):
			mul = 1
			for j in xrange(i+1,len(order[key])):
				mul = mul*(blocking[j][num_loop-1-order[key][j]])*(partitioning[j][num_loop-1-order[key][j]])
			optim_block[key].append(mul)

def opt_pre_partition_generate_loop(order, blocking, partitioning, optim_partition1, optim_partition2):
	num_loop = len(order)
	num_level = len(order[0])
	for key in order:
		optim_partition1[key] = []
		optim_partition2[key] = []
		for i in xrange(len(order[key])):
			mul = 1
			mul2 = 1
			for j in xrange(i,len(order[key])):
				if (j+1==num_level):
					x=1
				else:
					x=partitioning[j+1][num_loop-1-order[key][j]]
				mul = mul*(blocking[j][num_loop-1-order[key][j]])*x
				mul2 = mul2*x
			optim_partition1[key].append(mul)
			optim_partition2[key].append(mul2)

#start cur_loop = -1
def generate_loop(blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking = [], tile_partitioning = [], tile_b = [], tile_p = []):

	#basis
	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		#check the tile_partitioning and tile_blocking
		tile_b.append(tile_blocking)
		tile_p.append(tile_partitioning)

		del tile_blocking
		del tile_partitioning

	else:
		if cur_loop == num_loop-1:
			cur_level = cur_level+1
			cur_loop = 0
		else:
			cur_loop = cur_loop+1
		#print
		#print 'cur_loop: ',cur_loop
		#print 'cur_level: ',cur_level
		tile_partitioning_temp = tile_partitioning
		tile_blocking_temp = tile_blocking
		for par in xrange(partitioning[cur_level][cur_loop]):
			#print "par ",par
			tile_partitioning = copy.copy(tile_partitioning_temp)
			tile_partitioning.append(par+1)
			for block in xrange(blocking[cur_level][cur_loop]):
				#print blocking[cur_level][cur_loop]
				#print "block ",block
				tile_blocking=copy.copy(tile_blocking_temp)
				tile_blocking.append(block+1)
				generate_loop(blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_partitioning, tile_b, tile_p)
	

def post_generate_loop(tile_b,tile_p):
	tile_dict = {}
	tile_px = []
	tile_bx = []
	for i in xrange(len(tile_p)):
		tile_px.append(tuple(tile_p[i]))
		tile_bx.append(tuple(tile_b[i]))

	tile_dict = dict.fromkeys(tile_px)

	for key in tile_dict:
		tile_dict[key]=[]

	for i in xrange(len(tile_px)):
		tile_dict[tile_px[i]].append(tile_bx[i])

	return tile_dict


def solveit(coordinate, array_width, para_dim, old_partitioning, cur_level, order, num_loop):

	result = []

	if (len(para_dim[cur_level])==2):

		alist = []
		blist = []

		alistmul = 1
		for i in xrange(len(para_dim[cur_level][0])):
			if (old_partitioning[cur_level][para_dim[cur_level][0][i]]!=1):
				alist.append(old_partitioning[cur_level][para_dim[cur_level][0][i]])
				alistmul = alistmul*old_partitioning[cur_level][para_dim[cur_level][0][i]]

		blistmul = 1
		for i in xrange(len(para_dim[cur_level][1])):
			if (old_partitioning[cur_level][para_dim[cur_level][1][i]]!=1):
				blist.append(old_partitioning[cur_level][para_dim[cur_level][1][i]])
				blistmul = blistmul*old_partitioning[cur_level][para_dim[cur_level][1][i]]

		#print alist
		#print blist

		if alistmul>=blistmul:
			xlistmul = alistmul
			ylistmul = blistmul
			xlist = copy.copy(alist)
			ylist = copy.copy(blist)
		else:
			xlistmul = blistmul
			ylistmul = alistmul
			xlist = copy.copy(blist)
			ylist = copy.copy(alist)

		#print xlist
		#print ylist
		#sort the y axis

		r = ceildiv(xlistmul,array_width)

		important = r*ylist[0]

		ylistr = copy.copy(ylist[::-1])
		ylistsum = [1,]*(len(ylist)-1)
		yblock = []

		for i in xrange(len(ylist)-1):
			for j in xrange(i+1,len(ylist)):
				ylistsum[i] = ylistsum[i]*ylistr[j]*r

		inity = coordinate[0]+1

		if (inity<=ylistmul*r):
			for i in xrange(len(ylistsum)):
				tempy = ceildiv(inity,ylistsum[i])
				yblock.append(tempy)
				inity = inity - ylistsum[i]*(tempy-1)
			
			if (inity%ylist[0]==0):
				yblock.append(ylist[0])
			else:
				yblock.append(inity%ylist[0])
		else:
			yblock.append(None)

		importanty = ceildiv(inity,ylist[0])

		yblock = yblock[::-1]

		#transformation
		#print importanty

		coordinateT = coordinate[1] + array_width*(importanty-1)

		#print coordinateT
		#sort the x axis

		xlistr = copy.copy(xlist[::-1])
		xlistsum = [1,]*(len(xlist)-1)
		xblock = []

		for i in xrange(len(xlist)-1):
			for j in xrange(i+1,len(xlist)):
				xlistsum[i] = xlistsum[i]*xlistr[j]

		#print xlistsum

		initx = coordinateT+1

		if (initx<=xlistmul):
			for i in xrange(len(xlistsum)):
				tempx = ceildiv(initx,xlistsum[i])
				xblock.append(tempx)
				initx = initx - xlistsum[i]*(tempx-1)

			if (initx%xlist[0]==0):
				xblock.append(xlist[0])
			else:
				xblock.append(initx%xlist[0])
		else:
			xblock.append(None)

		xblock = xblock[::-1]

		#print xblock
		#print yblock

		if xblock[0]==None or yblock[0]==None:
			result = [None]
			return result

		result = [0,]*num_loop
		resultord = [1,]*num_loop

		if alistmul>=blistmul: #alist=x
			for i in xrange(len(para_dim[cur_level][0])):
				result[para_dim[cur_level][0][i]] = xblock[i]-1

			for j in xrange(len(para_dim[cur_level][1])):
				result[para_dim[cur_level][1][j]] = yblock[j]-1
		else:
			for i in xrange(len(para_dim[cur_level][0])):
				result[para_dim[cur_level][0][i]] = yblock[i]-1

			for j in xrange(len(para_dim[cur_level][1])):
				result[para_dim[cur_level][1][j]] = xblock[j]-1

		#print result

		for i in xrange(num_loop):
			resultord[num_loop-1-order[i][cur_level]] = result[i]

	return result

def ceildiv(a,b):
	if a%b==0:
		result = a/b
	else:
		result = a/b+1
	return result

def arrange_order(order, num_level, num_loop):
	for i in xrange(num_level):
		temp = 0
		for j in xrange(num_loop):
			if order[i][j]==6:
				order[i][j] = order[i][j]-temp
				temp = temp+1

def arrange_bp(old_partitioning,old_blocking,old_ordering,old_para_dim,num_level,num_loop,partitioning,blocking):
	for i in xrange(num_level):
		mini_partitioning = [1,]*num_loop
		mini_blocking = [1,]*num_loop
		for j in xrange(num_loop):
			mini_partitioning[num_loop-1-old_ordering[i][j]]=old_partitioning[i][j]
			mini_blocking[num_loop-1-old_ordering[i][j]]=old_blocking[i][j]
		partitioning.append(mini_partitioning)
		blocking.append(mini_blocking)

def make_ordering_dict(old_ordering,num_level,num_loop,new_ordering1, new_ordering2):
	for i in xrange(num_loop):
		new_ordering1[i] = [1,]*num_level
		new_ordering2[i] = [1,]*num_level
		for j in xrange(num_level):
			new_ordering1[i][j] = old_ordering[j][i]
			new_ordering2[i][j] = old_ordering[j][i]+num_loop*j

	
	#blocking = [[1,1,1,1,32,1,16],[1,1,2,1,1,48,1],[5,1,14,1,8,1,1]]
	#partitioning = [[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,5,1,28,1,1,1]]

	#blocking = [[1,1,1,1,1,1,1],[1,1,2,1,1,8,1],[5,1,14,1,8,1,1]]
	#partitioning = [[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,5,1,28,1,1,1]]

	#blocking = [[1,1,1,1,1,1,1],[1,1,2,1,1,2,1],[1,1,4,1,8,1,1]]
	#partitioning = [[1,1,1,1,1,1,1],[1,1,1,1,1,1,1],[1,5,1,2,1,1,1]]

	#OY OX FY FX
	#blocking = [[1,1,1,1],[1,1,1,1],[2,1,2,3]]
	#partitioning= [[1,1,1,1],[1,1,1,1],[1,3,3,1]]

	#order = [FX FY OX OY OC IC ON]

	'''
	order = {0:[0,3,4],1:[1,2,5]}
	order2 = {0:[0,1,0],1:[2,0,2],2:[1,3,1],3:[3,2,3]}
	blocking = [[1,2,1,1],[2,1,1,1],[2,3,4,2]]
	partitioning= [[1,1,1,1],[1,1,1,1],[2,2,6,2]]
	para_dim = [None,None,[[0,1],[2,3]]]
	
	
	cur_level = 2
	cur_loop = -1
	num_loop = 4
	num_level = 3
	tile_blocking = []
	tile_partitioning = []
	tile_bi = []
	tile_pi = []
	tile_bo = []
	tile_po = []

	coordinate= (6,2)
	array_width= 8

	#resultord = solveit(coordinate,array_width,para_dim,partitioning, cur_level, order2, num_loop)

	#print resultord
	
	#opt_generate_loop_blocking(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_bi)
	#opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning, tile_pi)

	#opt_generate_loop(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_partitioning, tile_bi, tile_pi)

	#print tile_bi
	#print
	#print tile_pi
	

	#tile_dict = opt_post_generate_loop(tile_bi,tile_pi)

	
	#for key in tile_dict:
	#	print key
	#	print tile_dict[key]
	#	print
	'''
	
	#blocking = [(3, 1, 1), (1, 1, 1), (13, 1, 1), (1, 1, 1), (8, 2, 6), (1, 64, 4), (1, 1, 16)]
	
	#blocking = [(3, 1, 1), (1, 1, 1), (13, 1, 1), (1, 1, 1), (8, 2, 6), (1, 6, 4), (1, 1, 16)]
	#partitioning = [(1, 1, 1), (3, 1, 1), (1, 1, 1), (13, 1, 1), (4, 1, 1), (1, 1, 1), (1, 1, 1)]
	#order = [(0, 6, 6), (1, 6, 6), (2, 6, 6), (3, 6, 6), (4, 1, 1), (6, 0, 2), (6, 6, 0)]
	#para_dim = ([[0], [1], [3], [4]], None, None)
	
	'''
	blocking = [(3, 1, 1), (2, 1, 1), (1, 1, 1), (1, 1, 1), (3, 1, 1), (1, 1, 1), (1, 1, 1)]
	partitioning = [(1, 1, 1), (3, 1, 1), (2, 1, 1), (3, 1, 1), (2, 1, 1), (1, 1, 1), (1, 1, 1)]
	order = [(0, 6, 6), (2, 6, 6), (1, 6, 6), (4, 6, 6), (3, 1, 1), (6, 0, 2), (6, 6, 0)]
	para_dim = ([[0], [1], [3], [4]], None, None)
	'''

	'''
	tile_dict = opt_post_generate_loop(tile_bi,tile_pi)

	for key in tile_dict:
		print key
		print tile_dict[key]
		print
	'''
	

	


