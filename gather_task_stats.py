import os
from collections import defaultdict
from tqdm import tqdm
import matplotlib.pyplot as plt
from astropy.time import Time
import numpy as np
import pandas as pd
import lsst.daf.butler as daf_butler


def add_datetime(df0, mjd_col, dt_col, offset=7.):
    df0[dt_col] = Time(df0[mjd_col].to_numpy() - offset/24.,
                       format="mjd").to_datetime()
    return df0


def extract_metadata(md, data):
    prefixes = ("prep", "init", "start", "end")
    info = md['quantum']
    # Wall times
    times = np.array([Time(info[f"{_}Utc"].split('+')[0])
                      for _ in ("prep", "end")])
    dt = times[1:] - times[:-1]
    for prefix, dt in zip(("run",), dt):
        data[f"{prefix}_wall_time"].append(dt.sec)
    data['start_utc'].append(times[0].mjd)
    data['end_utc'].append(times[-1].mjd)
    # max RSS
    data['max_rss'].append(info['endMaxResidentSetSize']/1024**3)
    # major page faults
    data['major_page_faults'].append(info['endMajorPageFaults'])
    # CPU times
    times = []
    for prefix in prefixes:
        try:
            value = info[f"{prefix}CpuTime"]
        except KeyError:
            value = info["endCpuTime"]
        times.append(value)
    times = np.array(times)
    dt = times[1:] - times[:-1]
    for prefix, dt in zip(("prep", "init", "run"), dt):
        data[f"{prefix}_cpu_time"].append(dt)
    # Node info
    if 'nodeName' in info:
        data['node_name'].append(info['nodeName'])
    # Butler put/get info
    if 'butler_metrics' in info:
        for key in ('time_in_put', 'time_in_get', 'n_get', 'n_put'):
            data[key].append(info['butler_metrics'][key])
    else:
        for key in ('time_in_put', 'time_in_get', 'n_get', 'n_put'):
            data[key].append(None)
    return data


def task_summaries(df0, tasks):
    data = defaultdict(list)
    for task in tasks:
        df = df0.query(f"task=='{task}'")
        data['task'].append(task)
        data['num_jobs'].append(len(df))
        data['total_wall_time'].append(sum(df['run_wall_time']))
        data['total_cpu_time'].append(sum(df['run_cpu_time']))
        data['median_wall_cpu_ratio'].append(
            np.median(df['run_wall_time']/df['run_cpu_time']))
    return pd.DataFrame(data)


def plot_time_history(df0, label=None, linestyle=None, color=None, alpha=0.5):
    start_time = df0['start_utc'].to_numpy()
    end_time = df0['end_utc'].to_numpy()
    delta = np.ones(len(df0))
    df = pd.DataFrame(dict(times=np.concat((start_time, end_time)),
                           deltas=np.concat((delta, -delta)),
                           datetime=np.concat((df0['start_dt'].to_numpy(),
                                               df0['end_dt'].to_numpy()))))
    df = df.sort_values('times')
    df['num_jobs'] = np.cumsum(df['deltas'])
    plt.plot(df['datetime'], df['num_jobs'], label=label, linestyle=linestyle,
             color=color, alpha=alpha)


def plot_processing_history(df0):
    plt.figure(1)
    plt.clf()
    tasks = list(set(df0['task']))
    for task in tasks:
        df = df0.query(f"task=='{task}'")
        plot_time_history(df, label=task, alpha=1.0)
    plot_time_history(df0, label='all', color='grey')
    plt.legend(fontsize='x-small')
    plt.xlabel("Time (PT)")
    plt.ylabel("Running jobs")


if __name__ == '___main__':
    tasks = [
        "isr",
        "calibrateImage",
        "standardizeSingleVisitStar",
        "consolidateSingleVisitStar",
        "consolidateVisitSummary",
        "associateIsolatedStar",
        "analyzeSingleVisitStarAssociation",
        "makeAnalysisSingleVisitStarAssociationMetricTable",
        "makeAnalysisSingleVisitStarAssociationWholeSkyPlot",
        "makeInitialVisitDetectorTable",
        "makeInitialVisitTable"
    ]

    user = os.environ["USER"]
    lsst_version = "w_2026_18"

    repo = "main"
    collections = [f"u/{user}/stage1_benchmark_{lsst_version}"]

    butler = daf_butler.Butler(repo, collections=collections)

    dfs = []
    for task in tasks:
        dstype = f"{task}_metadata"
        try:
            refs = list(set(
                butler.registry.queryDatasets(dstype, findFirst=True)))
        except (daf_butler.MissingDatasetTypeError,
                daf_butler.EmptyQueryResultError):
            continue
        data = defaultdict(list)
        print(task)
        for ref in tqdm(refs):
            md = butler.get(ref)
            data = extract_metadata(md, data)
        df = pd.DataFrame(data)
        df['task'] = task
        df = add_datetime(df, 'start_utc', 'start_dt')
        df = add_datetime(df, 'end_utc', 'end_dt')
        dfs.append(df)

    df0 = pd.concat(dfs)
    df_tasks = task_summaries(df0, tasks)
    print(df_tasks)
