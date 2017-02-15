#!/usr/bin/env bash
core=$(grep --count ^processor /proc/cpuinfo)
n=$(($core*2+1))
/usr/local/bin/gunicorn --workers $n --threads $n -p /log/gunicorn.pid --error-logfile /log/gunicorn.log -D --time 600 -b 0.0.0.0:8080 api:app