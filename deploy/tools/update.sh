#!/bin/bash


__filedir__=$(cd $(dirname "${BASH_SOURCE[0]}") && readlink -f .)


cp ${__filedir__}/../../../rdee-core/deploy/tools/deployer.py .
