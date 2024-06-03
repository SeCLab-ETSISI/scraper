#!/bin/bash

# Get the directory of the current script
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Define the base directory relative to the script directory
base_directory="$script_dir/.."

# Define the directories relative to the base directory
malware_directory="$base_directory/malware"
reports_directory="$base_directory/reports"
csv_directory="$base_directory/csv"
csv_mlw_directory="$csv_directory/malware"
csv_reports_directory="$csv_directory/reports"
destination_folder="$base_directory/github"

# Malware repositories
repos_malware=(
    "https://github.com/cyber-research/APTMalware.git"
)

# Report repositories
repos_reports=(
    "https://github.com/blackorbird/APT_REPORT.git"
    "https://github.com/CyberMonitor/APT_CyberCriminal_Campagin_Collections.git"
)

# Function to check and create directory
create_directory_if_not_exists() {
    local directory=$1
    if [ ! -d "$directory" ]; then
        mkdir -p "$directory"
        echo "Created directory: $directory"
    fi
}

# Check for non-PDF files
search_not_pdf_files() {
    local repo_path=$1
    cd "$repo_path" || exit
    find . -type f -exec file --mime-type {} + | grep -E ": application/pdf" | cut -d ':' -f 1 | while read -r pdf_file; do
        if [[ ! "$pdf_file" == *.pdf ]]; then
            echo "File without .pdf extension found: $pdf_file"
        fi
    done
}

# Function to generate malware CSV
generate_malware_csv() {
    local folder_path=$1
    local target_directory=$2
    local csv_file=$3

    echo "filepath|sha256|md5|sha1|campaign|year|original_path|original_name" > "$csv_file"
    find "$folder_path" -type f | while read -r file; do
        if [ -f "$file" ]; then
            sha256=$(sha256sum "$file" | cut -d ' ' -f 1)
            md5=$(md5sum "$file" | cut -d ' ' -f 1)
            sha1=$(sha1sum "$file" | cut -d ' ' -f 1)
            original_name=$(basename "$file")
            new_path="$target_directory/$sha256"
            cp "$file" "$new_path"
            echo "$new_path|$sha256|$md5|$sha1|||$file|$original_name" >> "$csv_file"
        fi
    done
}

# Function to generate reports CSV
generate_reports_csv() {
    local folder_path=$1
    local target_directory=$2
    local csv_file=$3

    echo "report_name|filepath|sha256|campaign|year|original_path" > "$csv_file"
    find "$folder_path" -type f -iname "*.pdf" | while read -r file; do
        if [ -f "$file" ]; then
            sha256=$(sha256sum "$file" | cut -d ' ' -f 1)
            report_name=$(basename "$file")
            new_path="$target_directory/$sha256.pdf"
            cp "$file" "$new_path"
            echo "$report_name|$new_path|$sha256|||$file" >> "$csv_file"
        fi
    done
}

# Create necessary directories
create_directory_if_not_exists "$malware_directory"
create_directory_if_not_exists "$reports_directory"
create_directory_if_not_exists "$csv_directory"
create_directory_if_not_exists "$csv_mlw_directory"
create_directory_if_not_exists "$csv_reports_directory"
create_directory_if_not_exists "$destination_folder"

# Clone all malware repositories
for repo in "${repos_malware[@]}"; do
    repo_name=$(basename -s .git "$repo")
    git clone "$repo" "$destination_folder/$repo_name"
done

# Clone all reports repositories
for repo in "${repos_reports[@]}"; do
    repo_name=$(basename -s .git "$repo")
    git clone "$repo" "$destination_folder/$repo_name"
done

# Process reports repositories
for repo in "${repos_reports[@]}"; do
    repo_name=$(basename -s .git "$repo")
    repo_path="$destination_folder/$repo_name"
    echo "Searching not pdf reports for $repo_name"
    search_not_pdf_files "$repo_path"
    echo "Search ended for $repo_name"
    echo "> Generating reports CSV for $repo_name"
    generate_reports_csv "$repo_path" "$reports_directory" "$csv_reports_directory/${repo_name}.csv"
done

# Process malware repositories
for repo in "${repos_malware[@]}"; do
    repo_name=$(basename -s .git "$repo")
    repo_path="$destination_folder/$repo_name"
    if [ "$repo_name" = "APTMalware" ]; then
        repo_path="$repo_path/samples/"
        for binary_path in "$repo_path"*; do
            if [ -f "$binary_path" ]; then
                target_directory=$(dirname "$binary_path")
                unzip -P infected "$binary_path" -d "$target_directory"
                rm "$binary_path"
            fi
        done
    fi
    echo "> Generating malware CSV for $repo_path"
    generate_malware_csv "$repo_path" "$malware_directory" "$csv_mlw_directory/${repo_name}.csv"
done

echo "Processing and CSV generation completed."
