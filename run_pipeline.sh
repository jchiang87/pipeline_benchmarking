#!/usr/bin/env bash

source ./setup.sh w_2026_18

bps submit bps/bps_stage1.yaml 2>&1 | grep -v ^parsl.process_loggers | grep -v ^monitoring
