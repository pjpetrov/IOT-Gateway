#!/bin/bash
docker compose build 
docker compose -f ./debug.yml up
