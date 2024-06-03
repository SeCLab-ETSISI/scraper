#!/bin/bash
malware_directory="$(pwd)/../malware"
reports_directory="$(pwd)/../reports"
csv_directory="$(pwd)/../csv"
csv_mlw_directory="$(pwd)/../csv/malware"
csv_reports_directory="$(pwd)/../csv/reports"
# List of repositories to be scraped
repos=(
    "https://github.com/blackorbird/APT_REPORT.git" # reports
    "https://github.com/CyberMonitor/APT_CyberCriminal_Campagin_Collections.git" # reports
    "https://github.com/cyber-research/APTMalware.git" # binaries
    "https://github.com/GiuseppeLaurenza/dAPTaset.git" # reports & binaries
    "https://github.com/StrangerealIntel/EternalLiberty.git" # APTs group Names
)
repos_malware=(
    "APTMalware"
)
# List of report repositories
repos_reports=(
    "APT_REPORT"
    "APT_CyberCriminal_Campagin_Collections"
)
# check not pdf files
search_not_pdf_files() {
    local repo_path=$1
    cd "$repo_path" || exit
    # Recursively find all files that are application/pdf and not found by using find with iname *.pdf
    find . -type f -exec file --mime-type {} + | grep -E ": application/pdf" | cut -d ':' -f 1 | while read -r pdf_file; do
        # Checking if the found file path does not end with .pdf
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
            #mod_date=$(git log -1 --format="%ci" -- "$pdf_file")
            sha256=$(sha256sum "$file" | cut -d ' ' -f 1)
            report_name=$(basename "$file")
            new_path="$target_directory/$sha256.pdf"
            cp "$file" "$new_path"
            echo "$report_name|$new_path|$sha256|||$file" >> "$csv_file"
        fi
    done
}

destination_folder="$(pwd)/../github"
# Create necessary directories
mkdir -p "$destination_folder"
# Clone all repositories
for repo in "${repos[@]}"; do
    repo_name=$(basename -s .git "$repo")
    git clone "$repo" "$destination_folder/$repo_name"
done

# Process reports repositories
for repo_name in "${repos_reports[@]}"; do
    repo_path="$destination_folder/$repo_name"
    echo "Searching not pdf reports for $repo_name"
    search_not_pdf_files "$repo_path"
    echo "Search ended for $repo_name"
    echo "> Generating reports CSV for $repo_name"
    generate_reports_csv "$repo_path" "$reports_directory" "$csv_reports_directory/${repo_name}.csv"
done

for repo_name in "${repos_malware[@]}"; do
    repo_path="$destination_folder/$repo_name"
    if [ "$repo_name" = "APTMalware" ]; then
        repo_path="$repo_path/samples/"
        for binary_path in $repo_path*; do
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
