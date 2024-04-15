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
    echo -e "\033[31mError!\033[0m The script can only be sourced rather than be executed!"
    exit 101
fi
scriptDir=$(cd $(dirname "${BASH_SOURCE[0]}") && readlink -f .)
workDir=$PWD
cd $scriptDir

#@ .preliminary-functions
function error() {
    echo -e '\033[31m'"Error"'\033[0m' "$1"
    exit 101
}
function error1utest() {
    conda activate base
    conda remove --name depTest --all -y >&/dev/null
    error "$1"
}
function success() {
    echo -e '\033[32m'"$1"'\033[0m'
}
function progress() {
    echo -e '\033[33m-- '"($(date '+%Y/%m/%d %H:%M:%S')) ""$1"'\033[0m'
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
    error "Cannot find python interpreter"
fi
pyver=$(python --version | cut -d' ' -f2)
min_pyver=$(cat $scriptDir/../MIN_PYTHON_VERSION)
if [[ $(echo $pyver | cut -d. -f1) != $(echo $min_pyver | cut -d. -f1) || $(echo $pyver | cut -d. -f2) -lt $(echo $min_pyver | cut -d. -f2) ]]; then
    error "Python version is too old: $pyver, while out requirement is at least 3.6"
fi

#@ <.arguments>
#@ <..default>
deploy_mode="install"
profile=
show_help=0
modulepath=
utest=0
verbose=0
#@ <..resolve>
while getopts "hd:p:m:uv" arg; do
    case $arg in
    h)
        show_help=1
        ;;
    u)
        utest=1
        ;;
    d)
        deploy_mode=$OPTARG
        ;;
    p)
        profile=$OPTARG
        ;;
    m)
        modulepath=$OPTARG
        ;;
    v)
        verbose=1
        ;;
    ?)
        error "Unknown option: $OPTARG"
        ;;
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

#@ Core
if [[ $utest == 0 ]]; then
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
        pip install -e . -i https://pypi.tuna.tsinghua.edu.cn/simple
        if [[ $? -eq 0 ]]; then
            success "Successfully install rdee-python in $(which python)"
        else
            error "Failed to install rdee-python in $(which python)"
        fi
    elif [[ $deploy_mode == "append" ]]; then
        targetDir=$(get_pypath)
        if [[ -z "$targetDir" ]]; then
            error "Cannot find valid path in env:PYTHONPATH to append, use other deploy_mode either"
        fi
        ln -sfT $scriptDir/../src/rdee $targetDir/rdee
        success "Succeed to append rdee-python in existed PYTHONPATH: $targetDir"
    else
        mkdir -p $scriptDir/package
        ln -sfT $scriptDir/../src/rdee $scriptDir/package/rdee
        text_setenv="# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
export PYTHONPATH=${scriptDir}/package:\$PYTHONPATH

"
        if [[ $deploy_mode == "setenv" ]]; then
            echo "$text_setenv" >$scriptDir/package/setenv.rdee-python.sh
            if [[ -e $scriptDir/../src/rdee/rdee ]]; then echo "occccccccccccccccccur"; fi
            success "Succeed to generate setenv script: $scriptDir/package/setenv.rdee-python.sh"

            if [[ -n $profile ]]; then
                cat <<EOF >.temp.rdee-python
# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
source $scriptDir/package/setenv.rdee-python.sh

EOF
                python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python

                if [[ $? -eq 0 ]]; then
                    success "Succeed to add source statements in $profile"
                else
                    error "Failed add source statements in $profile"
                fi
                rm -f .temp.rdee-python
            fi
            if [[ -e $scriptDir/../src/rdee/rdee ]]; then echo "11111111111111111111"; fi

        elif [[ $deploy_mode == "setenv+" ]]; then
            if [[ -z $profile ]]; then
                error "Must provide profile in setenv+ deploy mode"
            fi
            echo "$text_setenv" >.temp.rdee-python
            python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python
            if [[ $? -eq 0 ]]; then
                success "Succeed to add setenv statements in $profile"
            else
                error "Failed to add setenv statements in $profile"
            fi
            rm -f .temp.rdee-python

        elif [[ $deploy_mode =~ "module" ]]; then
            mkdir -p $scriptDir/package/modulefiles
            rm $scriptDir/package/modulefiles/*
            cat <<EOF >$scriptDir/package/modulefiles/$VERSION
#%Module1.0

prepend-path PYTHONPATH $scriptDir/package

EOF
            success "Succeed to generate modulefile in $scriptDir/package/modulefile"

            if [[ $deploy_mode == "module" && -n "$profile" ]]; then
                cat <<EOF >.temp.rdee-python
# >>>>>>>>>>>>>>>>>>>>>>>>>>> [rdee-python]
module use $scriptDir/package/modulefiles

EOF
                python $scriptDir/tools/fileop.ra-block.py $profile .temp.rdee-python
                if [[ $? -eq 0 ]]; then
                    success "Succeed to add 'module use' statements in $profile"
                else
                    error "Failed to add 'module use' statements in $profile"
                fi
                rm -f .temp.rdee-python

            elif [[ $deploy_mode == "module+" ]]; then
                if [[ -z "$modulepath" ]]; then
                    error "module+ mode required modulepath provided"
                fi
                if [[ ! -d "$modulepath" ]]; then
                    error "modulepath must be an existed directory"
                fi
                ln -sfT $scriptDir/package/modulefiles $modulepath/rdee-python
                if [[ $? -eq 0 ]]; then
                    success "Succeed to put modulefiles into modulepath=$modulepath"
                else
                    error "Failed to put modulefiles into modulepath=$modulepath"
                fi
            fi
        else
            error "Unexpected deploy_mode=${deploy_mode}"
        fi
    fi

else
    progress "Start unit test for deployment ..."
    #@ utest
    if [[ -z "$(which conda)" ]]; then
        error "Unit test for deployment requireds conda environment"
    fi

    # conda init

    progress "load conda and create temporary test conda environment ..."
    # condaroot=$(conda info | grep location | cut -d':' -f2)
    condaroot=$(dirname $(dirname $(which conda)))
    . $condaroot/etc/profile.d/conda.sh

    if [[ $verbose == 1 ]]; then
        conda create -n depTest python=3.12 -y
    else
        conda create -n depTest python=3.12 -y >&/dev/null
    fi

    if [[ $? != 0 ]]; then
        error "Failed to create depTest conda environment! Please check the current env-info manually!"
    fi
    conda activate depTest
    if [[ $CONDA_DEFAULT_ENV != "depTest" ]]; then
        error1utest "Failed to activate depTest environment"
    fi

    unset PYTHONPATH

    cd $scriptDir

    #@ .test-install
    progress "deploy via install mode"
    if [[ $verbose == 1 ]]; then
        ./deploy.Linux.sh
    else
        ./deploy.Linux.sh >&/dev/null
    fi
    if [[ $? != 0 ]]; then
        error1utest "Failed to deploy rdee-python via default install deploy-mode"
    fi
    python -c "import rdee"
    if [[ $? != 0 ]]; then
        error1utest "Failed to import rdee via default install deploy-mode"
    fi
    success "install mode passed"
    pip uninstall rdee -y >&/dev/null

    #@ .test-append
    progress "deploy via append mode"

    export PYTHONPATH=$scriptDir/tools
    ./deploy.Linux.sh -d append >&/dev/null
    python -c "import rdee"
    if [[ $? != 0 ]]; then
        error1utest "Failed to deploy rdee-python via default install deploy-mode"
    fi
    success "append mode passed"
    rm -f $scriptDir/tools/rdee
    unset PYTHONPATH

    #@ .test-setenv
    progress "deploy via setenv mode"

    ./deploy.Linux.sh -d setenv >&/dev/null
    if [[ ! -e $scriptDir/package/setenv.rdee-python.sh ]]; then
        error1utest "Failed to deploy rdee-python via setenv deploy-mode"
    fi
    ./deploy.Linux.sh -d setenv -p test.sh >&/dev/null
    . test.sh
    python -c "import rdee"
    if [[ $? != 0 ]]; then
        error1utest "Failed to deploy rdee-python via setenv deploy-mode with profile together"
    fi
    success "setenv mode passed"
    unset PYTHONPATH
    rm -rf package
    rm test.sh

    #@ .test-setenv+
    progress "deploy via setenv+ mode"

    ./deploy.Linux.sh -d setenv+ >&/dev/null
    if [[ $? -eq 0 ]]; then
        error1utest "Failed to deploy rdee-python via setenv+ deploy-mode, no -p ... but script exit with 0"
    fi
    ./deploy.Linux.sh -d setenv+ -p test2.sh >&/dev/null
    . test2.sh
    python -c "import rdee"
    if [[ $? != 0 ]]; then
        error1utest "Failed to deploy rdee-python via setenv deploy-mode with profile together"
    fi
    success "setenv+ mode passed"
    unset PYTHONPATH
    rm -rf package
    rm test2.sh

    #@ .test-module
    progress "deploy via module mode"

    ./deploy.Linux.sh -d module >&/dev/null
    if [[ ! -e $scriptDir/package/modulefiles ]]; then
        error1utest "Failed to deploy rdee-python via module deploy-mode"
    fi
    if module list 2>/dev/null; then
        ./deploy.Linux.sh -d module -p test2.sh >&/dev/null
        . test2.sh
        module load rdee
        python -c "import rdee"
        if [[ $? != 0 ]]; then
            error1utest "Failed to deploy rdee-python via module deploy-mode with profile together"
        fi
        module unload rdee
    fi
    rm test2.sh
    success "module mode passed"

    #@ .test-module+
    progress "deploy via module+ mode"

    ./deploy.Linux.sh -d module+ -m tools >&/dev/null
    if [[ ! -d tools/rdee-python ]]; then
        error1utest "Failed to deploy rdee-python via module+ deploy-mode"
    fi
    rm -f tools/rdee-python
    success "module+ mode passed"

    rm -rf package
fi
