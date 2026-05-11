shared_stack_root=/cvmfs/sw.lsst.eu/almalinux-x86_64/lsst_distrib
if [ -z "$1" ]
then
    # set up the most recently available weekly
    foo=`/usr/bin/ls -rt ${shared_stack_root} | grep w_20`
    version=`echo $foo | awk -F ' ' '{print $NF}'`
else
    # set up the requested version
    version=$1
fi
shared_stack_dir=${shared_stack_root}/${version}

LSST_DISTRIB=${shared_stack_dir}
if [[ -f ${LSST_DISTRIB}/loadLSST-ext.bash ]]; then
    source ${LSST_DISTRIB}/loadLSST-ext.bash
    setup lsst_distrib
else
    source ${LSST_DISTRIB}/loadLSST.bash
    setup lsst_distrib -t $(basename "$shared_stack_dir")
fi

export OMP_NUM_THREADS=1
export NUMEXPR_MAX_THREADS=1
export OMP_PROC_BIND=false
export LSST_S3_USE_THREADS=False
export LSST_VERSION=${version}
export BPS_WMS_SERVICE_CLASS=lsst.ctrl.bps.parsl.ParslService

PS1="\[\033]0;\w\007\][`hostname` ${version}] "
