#!/bin/bash

malware_directory="$(pwd)/../malware"
reports_directory="$(pwd)/../reports"
csv_directory="$(pwd)/../csv"
csv_mlw_directory="$(pwd)/../csv/malware"
csv_reports_directory="$(pwd)/../csv/reports"


mkdir -p "$folder_path"
mkdir -p "$malware_directory"
mkdir -p "$reports_directory"
mkdir -p "$csv_directory"
mkdir -p "$csv_mlw_directory"
mkdir -p "$csv_reports_directory"
