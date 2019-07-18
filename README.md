# CNN-blocking + Partial Sums Locator

The tool to optimize the CNN-blocking is based on https://github.com/xuanyoya/CNN-blocking/tree/dev.
A new feature is added to the basic optimizer in order to capture/record the partial sums locations associated with each PE (Processing Element).
The library for the new feature can be found in cnn_mapping/add_on.py.

## Inputs & Outputs
Inputs: CNN model (networks), accelerator architecture, dataflow/scheduling, and PE coordinate.

Outputs: best mapping point, partial sums locations (with respect to the PE coordinate).

## Running the tool

usage: run_optimizer.py [-h] [-s SCHEDULE] [-v]
                        [{basic,mem_explore, dataflow_explore}] arch network

positional arguments:
  ```
  {basic,mem_explore, dataflow_explore}   optimizer type  ---> choose basic to run the new feature

  arch                  architecture specification --> see examples/arch

  network               network specification --> see examples/networks
  ```

optional arguments:
  ```
  -h, --help            show this help message and exit

  -s SCHEDULE, --schedule SCHEDULE restriction of the schedule space --> see examples/schedule
  this is optional but restricting the schedule space will accelerate the scipt significantly

  -v, --verbose         vebosity
  ```

# Examples
## To optimize loop blocking.
Dataflow: Eyeriss

Memory Architecture: 3 level

Network: AlexNet Conv2 Batch16

```
python ./tools/run_optimizer.py -v -s ./examples/schedule/eyeriss_alex_conv2.json basic ./examples/arch/3_level_mem_baseline_asic.json ./examples/network/alex_conv2_batch16.json 
```

Dataflow: TPU

Memory Architecture: 3 level

Network: AlexNet Conv2 Batch16

```
python ./tools/run_optimizer.py -v -s ./examples/schedule/tpu.json basic ./examples/arch/3_level_mem_baseline_asic.json ./examples/network/alex_conv2_batch16.json
```

# Output examples

## CNN-blocking output

Dataflow: Eyeriss

Memory Architecture: 3 level

Network: AlexNet Conv3 Batch16

```
Smallest Cost:  13344276111.4
Best mapping_point loop_blockings:  [(3, 1, 1), (1, 1, 1), (13, 1, 1), (1, 1, 1), (8, 2, 6), (1, 64, 4), (1, 1, 16)]
Best mapping_point loop_partitionings:  [(1, 1, 1), (3, 1, 1), (1, 1, 1), (13, 1, 1), (4, 1, 1), (1, 1, 1), (1, 1, 1)]
Best mapping_point para_dim:  ([[0], [1], [3], [4]], None, None)
Best mapping_point loop_order:  [(0, 6, 6), (1, 6, 6), (2, 6, 6), (3, 6, 6), (4, 1, 1), (6, 0, 2), (6, 6, 0)]
best energy:  13344276111.4
cost for each level:  [9946550108.16, 11521843.200000048, 649666560, 2736537600]
```

Output explanation for the above example:

- Loop Blockings: the blocking factor for every loop variable in every memory level. 
	The convention goes by the following: 
	```
	[FX:(0,1,2) FY:(0,1,2) OX:(0,1,2) OY:(0,1,2) OC:(0,1,2) IC:(0,1,2) ON:(0,1,2)] with 0 being the blocking of the nearest memory level to the processing element.
	```
- Loop Partitionings: the number of parallel units for every loop variable in every memory level. 
	The convention goes by the following: 
	```
	[FX:(0,1,2) FY:(0,1,2) OX:(0,1,2) OY:(0,1,2) OC:(0,1,2) IC:(0,1,2) ON:(0,1,2)] with 0 being the partitioning of the nearest memory level to the processing element.
	```
- Loop Order: the order of the loop variables in every memory level.
	The convention goes by the following: 
	```
	[FX:(0,1,2) FY:(0,1,2) OX:(0,1,2) OY:(0,1,2) OC:(0,1,2) IC:(0,1,2) ON:(0,1,2)] with 0 being the loop order of the nearest memory level to the processing element and n being the highest memory level.
	```
- Parallel Dimensions: the list of unrolled loops in the every dimension for each memory level.
	The convention goes by the following: 
	```
	(Level 0: [[Loops unrolled in the 1st dimension], [Loops unrolled in the 2nd dimension]], Level 1: [[Loops unrolled in the 1st dimension], [Loops unrolled in the 2nd dimension]], Level n: [[Loops unrolled in the 1st dimension], [Loops unrolled in the 2nd dimension]) 
	with level 0 being the parallel dimension of the nearest memory level to the processing element. 
	```
	To specify the loop, each number represent different loop variables:  
	```
		FX = 0
		FY = 1
		OX = 2
		OY = 3
		OC = 4
		IC = 5
		ON = 6
	```
	If the output does not match with the convention, the tool will ask the user to specify the unrolled loop manually during the simulation.

## Partial Sums Locator Output

The partial sums locator will ask the user for the PE coordinate and generate the location of the partial sums associated with that PE. The output will also be stored in "result.h5" file for further use.

```
The partial sums location:

[[  0   2   0 ...  24   0   0]
 [  1   2   0 ...  24   0   0]
 [  2   2   0 ...  24   0   0]
 ...
 [  0   2  12 ... 383 255  15]
 [  1   2  12 ... 383 255  15]
 [  2   2  12 ... 383 255  15]]
```
The convention goes by the following:
The location of the partial sums could be addressed in 7 dimension: [FX FY OX OY OC IC ON].
By knowing which computation happens in each dimension, the partial sums location could be obtained.
Therefore, the matrix column represents different loop variables to identify the computation that happens in each dimension while the matrix row represents the each partial sums that is generated by the PE

```
 [  FX  FY  OX  OY  OC  IC  ON] 
[[  0   2   0 ...  24   0   0]  --> 1st partial sums generated by the PE
 [  1   2   0 ...  24   0   0]  --> 2nd partial sums generated by the PE
 [  2   2   0 ...  24   0   0]  --> 3rd partial sums generated by the PE
 ...
 [  0   2  12 ... 383 255  15]  
 [  1   2  12 ... 383 255  15]
 [  2   2  12 ... 383 255  15]] --> last partial sums generated by the PE
```

# Restrictions

## CNN-blocking Scheduling Restrictions

See examples/schedule!
- This tool does not support multi-level parallelism (the parallelization only occur on 1 memory level)
- Cannot specify more than 1 level of {blocking, ordering, partitioning} for each loop variables
- If (total parallel factor < 0.5 * total PE) then we cannot specify more than 2 loop variables in the same level (example: Google TPU)
- If (total parallel factor > 0.5 * total PE) then we could specify more than 2 loop variables in the same level, but we need to specify the para_dim parameter manually later on (example: Eyeriss).

## Partial Sums Locator Restrictions

- The Partial Sums Locator could only be used for a 2D PE Array with single level parallelism (the parallelization only occur on 1 memory level)
- The speed of the Partial Sums Locator goes linear with the number of parallel units.
- The result.h5 file could get pretty big in size depending on the networks
