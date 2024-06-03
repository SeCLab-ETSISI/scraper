#!/bin/bash

# Function to download files for each year from 2010 to 2024
download_files_vx() {
    target_directory=$1
    base_url="https://samples.vx-underground.org/APTs/Yearly%20Archives/"
    mkdir -p "$target_directory"
    for year in {2009..2024}; do
        url="${base_url}${year}.7z"
        filename="$target_directory/$(basename $url)"
        curl -o "$filename" "$url"
        7z x "$filename" -pinfected -o"$target_directory" -y  > /dev/null 2>&1
        rm "$filename" # Remove the 7z file after extraction
    done
}

extract_malware(){
    folder_path=$1
    find "$folder_path" -type d -name "Samples" | while read -r samples_dir; do
        for binary_path in "$samples_dir"/*; do
            if [ -f "$binary_path" ]; then
                target_directory=$(dirname "$binary_path")
                7z x "$binary_path" -p"infected" -o"$target_directory"
                rm "$binary_path"
            fi
        done
    done
}

generate_malware_csv(){
    folder_path=$1
    target_directory=$2
    csv_directory=$3
    echo "filepath|sha256|md5|sha1|campaign|year|original_path|original_name" > "$csv_directory/vx_underground.csv"
    find "$folder_path" -type d -name "Samples" | while read -r samples_dir; do
        year=$(basename "$(dirname "$samples_dir")")
        campaign=$(basename "$(dirname "$(dirname "$samples_dir")")")
        for binary_path in "$samples_dir"/*; do
            # if file ends with .7z, skip
            if [[ ! "$binary_path" == *.7z ]]; then
                if [ -f "$binary_path" ]; then
                    sha256=$(sha256sum "$binary_path" | cut -d ' ' -f 1)
                    md5=$(md5sum "$binary_path" | cut -d ' ' -f 1)
                    sha1=$(sha1sum "$binary_path" | cut -d ' ' -f 1)
                    original_name=$(basename "$binary_path")
                    # now move the file to the target directory and rename it to the sha256 hash
                    new_path="$target_directory/$sha256"
                    cp "$binary_path" "$new_path"
                    echo "$new_path|$sha256|$md5|$sha1|$campaign|$year|$binary_path|$original_name" >> "$csv_directory/vx_underground.csv"
                fi
            fi
            
        done
    done
}

generate_reports_csv(){
    folder_path=$1
    target_directory=$2
    csv_directory=$3
    # Create the CSV file
    echo "report_name|filepath|sha256|campaign|year|original_path" > "$csv_directory/vx_underground.csv"
    find "$folder_path" -type d -name "Paper" | while read -r paper_dir; do
        year=$(basename "$(dirname "$paper_dir")")
        campaign=$(basename "$(dirname "$(dirname "$paper_dir")")")
        for paper_path in "$paper_dir"/*; do
            if [ -f "$paper_path" ]; then
                sha256=$(sha256sum "$paper_path" | cut -d ' ' -f 1)
                report_name=$(basename "$paper_path")
                # now move the file to the target directory and rename it to the sha256 hash
                new_path="$target_directory/$sha256"
                cp "$paper_path" "$new_path"
                echo "$report_name|$new_path|$sha256|$campaign|$year|$paper_path" >> "$csv_directory/vx_underground.csv"
            fi
            
        done
    done

}
malware_directory="$(pwd)/../malware"
reports_directory="$(pwd)/../reports"
csv_directory="$(pwd)/../csv"
csv_mlw_directory="$(pwd)/../csv/malware"
csv_reports_directory="$(pwd)/../csv/reports"

folder_path="$(pwd)/../vx_underground"
############################################
mkdir -p "$folder_path"
mkdir -p "$malware_directory"
mkdir -p "$reports_directory"
mkdir -p "$csv_directory"
mkdir -p "$csv_mlw_directory"
mkdir -p "$csv_reports_directory"
############################################


# Main script execution
echo ">Downloading and extracting files to $folder_path"
download_files_vx "$folder_path"
extract_malware "$folder_path"

echo ">Generating malware CSV in $csv_mlw_directory"
generate_malware_csv "$folder_path" "$malware_directory" "$csv_mlw_directory"

echo ">Generating reports CSV in $csv_reports_directory"
generate_reports_csv "$folder_path" "$reports_directory" "$csv_reports_directory"



echo "Extraction and CSV generation completed."
