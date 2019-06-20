#from mapping_point import MappingPoint

#import loop_enum as le
#import buffer_enum as be 

import copy
import math
from collections import OrderedDict
from operator import add

def get_PE_values(point,resource,layer):
	blocking = zip(*point.loop_blockings)
	partitioning = zip(*point.loop_partitionings)
	order = zip(*point.loop_orders)

	num_level = resource.buffer_levels()
	num_loop = le.NUM

	#reshape blocking partitioning order

	blocking_reshape = []
	partitioning_reshape = []
	order_reshape = []
	for i in xrange(num_level):
		blocking_reshape.append(list(blocking[num_level-1-i]))
		partitioning_reshape.append(list(partitioning[num_level-1-i]))
		order_reshape.append(list(order[num_level-1-i]))

	new_blocking = blocking_reshape
	new_partitioning = partitioning_reshape
	new_order = order_reshape
	reshape_blocking_partitioning_order(new_blocking,new_partitioning,new_order)

	order_dict = {}
	order_dict = generate_order_dict(new_order,num_loop)

	tile_blocking = []
	tile_partitioning = []
	tile_bi = []
	tile_pi = []
	cur_level = 0
	cur_loop = -1

	opt_generate_loop_blocking(order, new_blocking, new_partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_bi)
	opt_generate_loop_partitioning(order, new_blocking, new_partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning, tile_pi)


	tile_dict = opt_post_generate_loop(tile_bi,tile_pi)

	for key in tile_dict:
		print key
		print tile_dict[key]
		print

	return

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
	

def opt_generate_loop_blocking(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking = [], tile_bi = []):

	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		tile_b = []
		for key in order:
			add = 0
			for i in xrange(len(order[key])):
				mul = 1
				for j in xrange(i+1,len(order[key])):
					mul = mul*(blocking[j][key])*(partitioning[j][key])
				add = add+mul*(tile_blocking[order[key][i]]-1)

			tile_b.append(add)	

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
			opt_generate_loop_blocking(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_bi)
	

def opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning = [], tile_pi = []):

	if (cur_loop == num_loop-1) and (cur_level == num_level-1):
		tile_p = []
		for key in order:
			add = 0
			for i in xrange(len(order[key])):
				mul = 1
				for j in xrange(i,len(order[key])):
					if (j+1==num_level):
						x=1
					else:
						x=partitioning[j+1][key]
					mul = mul*(blocking[j][key])*x
				add = add+mul*(tile_partitioning[order[key][i]]-1)
			tile_p.append(add)	

		tile_po.append(tile_partitioning)
		tile_pi.append(tile_p)

		del tile_p
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
			opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning, tile_pi)

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


def generate_order_dict(order, num_loop, num_level):
	order_dict = {}
	for i in xrange(num_loop):
		order_dict[i]=[]
		for j in xrange(num_level):
			x = j*num_loop
			order_dict[i].append(num_loop-1-order[num_level-j-1][i]+x)

	return order_dict


def reshape_blocking_partitioning_order(new_blocking,new_partitioning,new_order):

	for i in xrange(len(new_order)):
		min_idx = i
		for j in xrange(i+1,len(new_order)):
			if new_order[min_idx] > new_order[j]:
				min_idx=j
		new_order[i],new_order[min_idx] = new_order[min_idx],new_order[i]
		new_partitioning[i],new_partitioning[min_idx] = new_partitioning[min_idx],new_partitioning[i]
		new_blocking[i],new_blocking[min_idx] = new_blocking[min_idx],new_blocking[i]


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




if __name__ == "__main__":

	
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

	order = {0:[0,2,4],1:[1,3,5]}
	blocking = [[1,2],[2,1],[2,3]]
	partitioning= [[1,1],[1,2],[2,2]]
	
	cur_level = 0
	cur_loop = -1
	num_loop = 2
	num_level = 3
	tile_blocking = []
	tile_partitioning = []
	tile_bi = []
	tile_pi = []
	tile_bo = []
	tile_po = []
	
	opt_generate_loop_blocking(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_bi)
	opt_generate_loop_partitioning(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_partitioning, tile_pi)

	#opt_generate_loop(order, blocking, partitioning, cur_level, cur_loop, num_loop, num_level, tile_blocking, tile_partitioning, tile_bi, tile_pi)

	'''
	print tile_bi
	print
	print tile_pi
	'''

	tile_dict = opt_post_generate_loop(tile_bi,tile_pi)

	
	for key in tile_dict:
		print key
		print tile_dict[key]
		print
	
	
	
	



