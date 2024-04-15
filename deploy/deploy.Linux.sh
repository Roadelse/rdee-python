#!/bin/bash

#@ Introduction
###############################################################################
# This scripts aims to deploy the rdee-python in system                       #
# Support flexible deployment method, inlcuding:                              #
#    ● install package into python                                            #
#    ● setenv bash script                                                     #
#    ● modulefile                                                             #
# ----------------------------------------------------------------------------#
#                                                                             #
# 2024-01-08  Roadelse  Initialized                                           #
###############################################################################

#@ Prepare
#@ .
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    echo "The script can only be executed rather than sourced!"
    exit 101
fi
scriptDir=$(cd $(dirname "${BASH_SOURCE[0]}") && readlink -f .)
workDir=$PWD

#@ .preliminary-functions
function error() {
    echo -e '\033[31m'"$1"'\033[0m'
    exit 101
}
function success() {
    echo -e '\033[32m'"$1"'\033[0m'
}
function pathDep() {
    if [[ -z $1 ]]; then
        return -1
    fi
    depth=$(echo "$1" | grep -o '/' | wc -l)
    echo $depth
}
function get_pypath() {
    IFS=: read -ra pypaths <<<$PYTHONPATH
    minDepth=999
    rstPath=
    for pp in "${pypaths[@]}"; do
        if [[ ! -w $pp ]]; then
            continue
        fi
        ppDep=$(pathDep $pp)
        if [[ $ppDep -lt $minDepth ]]; then
            minDepth=$ppDep
            rstPath=$pp
        fi
    done
    echo $rstPath
}

#@ <.pre-check>
#@ <..python3>
if [[ -z $(which python 2>/dev/null) ]]; then
    error "Error! Cannot find python interpreter"
fi
pyver=$(python --version | cut -d' ' -f2)
min_pyver=$(cat $scriptDir/../MIN_PYTHON_VERSION)
if [[ $(echo $pyver | cut -d. -f1) != $(echo $min_pyver | cut -d. -f1) || $(echo $pyver | cut -d. -f2) -lt $(echo $min_pyver | cut -d. -f2) ]]; then
    error "Error! Python version is too old: $pyver, while out requirement is at least 3.6"
fi

#@ <.arguments>
#@ <..default>
deploy_mode="install"
profile=
show_help=0
#@ <..resolve>
while getopts "hd:p:" arg; do
    case $arg in
    h)
        show_help=1
        ;;
    d)
        deploy_mode=$OPTARG
        ;;
    p)
        profile=$OPTARG
        ;;
    ?) ;;
    esac
done

#@ .help
if [[ $show_help == 1 ]]; then
    echo "
deploy.Linux.sh [options]

[options]
    ● -h
        show this information
    ● -d deploy_mode
        select deployment target, supporting install, append, setenv, setenv+, module, module+
    ● -p profile
        select profile to be added
"
    exit 0
fi

#@ .dependent-variables
VERSION=$(cat $scriptDir/../VERSION)

if [[ $deploy_mode == "install" ]]; then
    if [[ -n "$(pip freeze | grep -P '^rdee')" ]]; then
        echo "Already installed in non-editable mode"
        exit 0
    fi
    if [[ -n "$(pip freeze | grep -P 'egg=rdee$')" ]]; then
        echo "Already installed in editable mode"
        exit 0
    fi

    cd $scriptDir/..
    pip install -e .
    if [[ $? -eq 0 ]]; then
        success "Successfully install rdee-python in $(which python)"
    else
        error "Error! Failed to install rdee-python in $(which python)"
    fi
elif [[ $deploy_mode == "append" ]]; then
    targetDir=$(get_pypath)
    if [[ -z "$targetDir" ]]; then
        error "Error! Cannot find valid path in env:PYTHONPATH to append, use other deploy_mode either"
    fi
    ln -s $scriptDir/../src/rdee $targetDir/rdee
    success "Succeed to append rdee-python in existed PYTHONPATH: $targetDir"
else
    mkdir -p $scriptDir/package
    ln -sf $scriptDir/../src/rdee $scriptDir/package/rdee
    text_setenv="# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
export PYTHONPATH=${scriptDir}/package:\$PYTHONPATH

"
    if [[ $deploy_mode == "setenv" ]]; then
        echo "$text_setenv" >$scriptDir/package/setenv.rdee.sh
        if [[ -n $profile ]]; then
            cat <<EOF >>.temp.rdee-python
# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
source $scriptDir/package/setenv.rdee.sh

EOF
            python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python
            rm -f .temp.rdee-python
        else
            success "Succeed to generate setenv script: $scriptDir/package/setenv.rdee.sh"
        fi
    elif [[ $deploy_mode == "setenv+" ]]; then
        if [[ -z $profile ]]; then
            error "Error! Must provide profile in setenv+ deploy mode"
        fi
        echo "$text_setenv" >.temp.rdee-python
        python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python
        success "Succeed to add setenv statements in $profile"
    elif [[ $deploy_mode =~ "module" ]]; then
        mkdir -p $scriptDir/package/modulefiles
        rm $scriptDir/package/modulefiles/*
        cat <<EOF >$script/package/modulefiles/$VERSION
#%Module1.0

prepend-path PYTHONPATH $scriptDir/package

EOF
        success "Succeed to generate modulefile in $scriptDir/package/modulefile"

        if [[ $deploy_mode == "module" && -n "$profile" ]]; then
            cat <<EOF >>.temp.rdee-python
# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
module use $scriptDir/package/modulefile

EOF
            python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python
            success "Succeed to add 'module use' statements in $profile"
        elif [[ $deploy_mode == "module+" ]]; then
            if [[ -z "$modulepath" ]]; then
                error "Error! module+ mode required modulepath provided"
            fi
            if [[ ! -d "$modulepath" ]]; then
                error "Error! modulepath must be an existed directory"
            fi
            ln -s $scriptDir/package/modulefiles $modulepath/rdee-python
            success "Succeed to put modulefiles into modulepath=$modulepath"
        fi
    else
        error "Error! Unexpected deploy_mode=${deploy_mode}"
    fi
fi
