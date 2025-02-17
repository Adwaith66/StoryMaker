#!/bin/bash
#
# Linux/Mac BASH script to build docker container
#
docker rmi final-client
docker build -t final-client .
