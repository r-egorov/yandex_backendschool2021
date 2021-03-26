#!/usr/bin/env bash
service nginx start
uwsgi --ini ./configs/uwsgi.ini
