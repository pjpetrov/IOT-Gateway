#!/bin/bash
docker compose -f ./debug_telegram.yml build 
docker compose -f ./debug_telegram.yml up
