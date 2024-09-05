if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "The script can only be sourced rather than executed"
    exit 0
fi

if [[ -z "$1" || "$1" != "unload" ]]; then

export PYTHONPATH=/mnt/d/recRoot/GitRepos/rdee-python/deploy/../src:$PYTHONPATH


else

function rmep(){
    local rst
    rst=$(echo :${!1} | sed "s|:$2||g")
    if [[ "$rst" =~ ^: ]]; then
        export $1="${rst:1}"
    else
        export $1="${rst}"
    fi
}

rmep PYTHONPATH /mnt/d/recRoot/GitRepos/rdee-python/deploy/../src


fi
