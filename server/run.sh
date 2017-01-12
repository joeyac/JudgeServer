#!/usr/bin/env bash
core=$(grep --count ^processor /proc/cpuinfo)
n=$(($core*2+1))
gunicron --workers $n --threads $n --error-logfile /log/gunicorn.log --time 600 --bind 0.0.0.0:8080 api:app