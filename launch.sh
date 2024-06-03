#!/bin/bash

# absolute path for current script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
scrapers_dir="$script_dir/scrapers"


# scripts may be bash or python
launch_scripts() {
    for script in "$scrapers_dir"/*; do
        if [[ -f "$script" ]]; then
            case "$script" in
                *.sh)
                    echo "Launching Bash script: $script"
                    bash "$script"
                    ;;
                *.py)
                    echo "Launching Python script: $script"
                    python3 "$script"
                    ;;
                *)
                    echo "Unknown script type: $script"
                    ;;
            esac
        fi
    done
}

launch_scripts

