'''
Simple test case for checking get_cost
'''
import unittest
import cnn_mapping as cm 

class TestCostModel(unittest.TestCase):

    
    def test_simple(self):
        capacity_list = [512, 131072]
        access_cost_list = [1, 2, 64]
        static_cost_list = [0.2, 4096*0.2] 
        para_count_list = [12, 1]

        loop_order_list = [(0, 6), (2, 6), (6, 0), (3, 1), (6, 3), (1, 2), (6, 4)]
        loop_blockings_list = [(3, 1), (1, 1), (1, 8), (1, 2), (1, 32), (8, 8), (1, 1)]
        loop_partitionings_list = [(1, 1), (3, 1), (1, 1), (4, 1), (1, 1), (1, 1), (1, 1)]

        point = cm.MappingPoint(loop_order_list, loop_blockings_list, loop_partitionings_list)
        resource = cm.Resource(capacity_list, access_cost_list, static_cost_list, para_count_list, 0, [1, 0])
        layer = cm.Layer(64, 32, 8, 8, 3, 3, 1)
        cm.utils.print_loop_nest(point)
        cost = cm.cost_model.get_cost(resource, point, layer, True)
        real_cost = (6400*288 + 2048*1152 + 18432*64) + (6400*96 + 2048*48 + 18432*4)*2 + (6400*32 + 2048*16 + 18432*1)*64
        self.assertEqual(cost, real_cost)
'''
    def test_parallelism(self):   
        capacity_list = [512, 4096, 16384]
        access_cost_list = [1, 6, 23]
        static_cost_list = [0.2, 32*0.2, 512*0.2] 
        para_count_list = [1, 4, 16]

        loop_order_list = [(0, 2, 2), (1, 3, 3), (2, 0, 4), (3, 1, 5), (4, 4, 0), (5, 5, 1), (6, 6, 6)]
        loop_blockings_list = [(3, 1, 1), (3, 1, 1), (1, 4, 1), (1, 4, 1), (1, 1, 8), (1, 1, 16), (1, 1, 1)]
        loop_partitionings_list = [(1, 1, 1), (1, 1, 1), (1, 2, 1), (1, 2, 1), (1, 1, 4), (1, 1, 4), (1, 1, 1)]

        point = cm.MappingPoint(loop_order_list, loop_blockings_list, loop_partitionings_list)
        resource = cm.Resource(capacity_list, access_cost_list, static_cost_list, para_count_list)
        layer = cm.Layer(64, 32, 8, 8, 3, 3, 1)
        cost = cm.cost_model.get_cost(resource, point, layer, True)
        real_cost = (6400*32 + 2048*64*2 + 18432*64) + (6400*32 + 2048*64*2 + 18432*1)*6 + (6400 + 2048*64*2 + 18432)*23
        self.assertEqual(cost, real_cost)

'''
     
    
if __name__ == '__main__':
    unittest.main()