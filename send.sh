#!/usr/bin/env bash

rsync -av -P --exclude='.venv' --exclude='.idea' --exclude='.git' --exclude='uv.lock' --exclude='__pycache__' . prx:/opt/nas_monitor/
