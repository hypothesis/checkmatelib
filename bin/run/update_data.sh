#!/bin/sh

echo "Updating suffix file"
export SUFFIX_URL=https://publicsuffix.org/list/public_suffix_list.dat
export SUFFIX_FILE=src/checkmatelib/resource/data/public_suffix_list.dat

echo "// From: ${SUFFIX_URL}" > $SUFFIX_FILE
curl $SUFFIX_URL >> $SUFFIX_FILE

echo "Updating TLD file"
export TLD_URL=https://data.iana.org/TLD/tlds-alpha-by-domain.txt
export TLD_FILE=src/checkmatelib/resource/data/valid_top_level_domains.txt

echo "# From: ${TLD_URL}" > $TLD_FILE
curl $TLD_URL >> $TLD_FILE
