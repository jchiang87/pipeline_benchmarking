## These are scripts for running benchmarking tests for Rubin pipelines at USDF

### Setup
To run these scripts, the user will need credentials for access the Butler repos at USDF.
[Instructions](https://df-ops.lsst.io/users/storage.html#butler-access) for obtaining those credentials
are described in the [Rubin Data Facilities documentation](https://df-ops.lsst.io/index.html).

### Running the pipeline benchmarking script
The [`run_pipeline.sh`](run_pipeline.sh) script will set up the LSST stack, and submit a slurm job to run a subset of the Rubin processing pipelines.
Currently, that script is hard-coded to use `w_2025_18` of the LSST stack in `/cvmfs/sw.lsst.eu/almalinux-x86_64/lsst_distrib/`.
The payload is defined in [bps/bps_stage1.yaml](bps/bps_stage1.yaml) and is currently configured to process 67 vists of LSSTCam data through
stage1 of the DRP pipeline.  The `ctrl_bps_parsl` plugin is used to avoid reliance on the HTCondor system.  These jobs are submitted directly
to slurm, while the parsl manager process runs interactively.  Running on 3 torino nodes exclusively, this job should finish in ~30 mins.

It's probably best to direct the screen output to a log file, e.g.,
```
$ ./run_pipeline.sh &> stage1_00.log
```

### Performance metrics
The [`gather_task_stats.py`](gather_task_stats.py) script will query the butler for the most recent set of task metadata
and will print a summary of wall and cpu times for each of the task types:
```
$ python gather_perf_stats.py
                                                 task  num_jobs  total_wall_time  total_cpu_time  median_wall_cpu_ratio
0                                                 isr     11524    193887.877842   187055.737294               1.026357
1                                      calibrateImage     11524    291403.668302   284097.372838               1.022547
2                          standardizeSingleVisitStar     11524      2304.541551     1686.542405               1.332215
3                          consolidateSingleVisitStar        67       384.694448      329.571411               1.165835
4                             consolidateVisitSummary        67      1304.395800     1212.479810               1.074500
5                               associateIsolatedStar       102       180.819559      175.162110               1.031341
6                   analyzeSingleVisitStarAssociation       102      1419.790734     1382.990363               1.021245
7   makeAnalysisSingleVisitStarAssociationMetricTable         1         0.667937        0.566245               1.179591
8   makeAnalysisSingleVisitStarAssociationWholeSky...         1        16.622047       16.188043               1.026810
9                       makeInitialVisitDetectorTable         1         7.612374        7.490431               1.016280
10                              makeInitialVisitTable         1         6.086022        5.836938               1.042674
```
This takes a few minutes to query the butler for the task metadata.

The main performance metric of interest is the total wall time, since that determines the overall throughput of the processing.
Other metrics of interest are the total cpu time and the median wall-to-cpu time ratio, since those are related to resource
contention among the jobs.
