#!/bin/bash

# Auto-discovery script for bank transactions enrichment
# Dynamically discovers bank config files and prompts user for selection

set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to discover bank config files
discover_banks() {
    local banks=()

    while IFS= read -r -d '' config_file; do
        local dir
        dir=$(dirname "$config_file")
        local filename
        filename=$(basename "$config_file")
        dir=${dir#"$SCRIPT_DIR"/}
        banks+=("$dir:$filename:$config_file")
    done < <(find "$SCRIPT_DIR" -type f -name '*_bank_rules.yaml' -print0)

    printf '%s\n' "${banks[@]}"
}

# Function to display menu and get user selection
display_menu() {
    local banks=("$@")
    local count=${#banks[@]}

    echo -e "${BLUE}==========================================" >&2
    echo "Transaction Enrichment - Bank Selection" >&2
    echo "==========================================${NC}" >&2
    echo "" >&2
    echo "Available banks:" >&2
    echo "" >&2

    for i in "${!banks[@]}"; do
        IFS=':' read -r bank_folder config_file _abs_path <<< "${banks[$i]}"
        printf "  %2d) %s (%s)\n" $((i + 1)) "$bank_folder" "$config_file" >&2
    done

    echo "" >&2
    printf "  %2d) All banks\n" $((count + 1)) >&2
    echo "" >&2
    read -p "Select option (enter number): " choice

    printf '%s\n' "$choice"
}

# Function to validate choice
validate_choice() {
    local choice=$1
    local max=$2

    if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt "$max" ]; then
        return 1
    fi
    return 0
}

# Main execution
echo -e "${BLUE}Discovering bank configurations...${NC}"
echo ""

# Get discovered banks
DISCOVERED_BANKS=()
while IFS= read -r bank_entry; do
    [[ -n "$bank_entry" ]] && DISCOVERED_BANKS+=("$bank_entry")
done < <(discover_banks)

if [[ ${#DISCOVERED_BANKS[@]} -eq 0 ]]; then
    echo -e "${RED}✗ No bank configurations found.${NC}"
    echo "Expected to find YAML config files in *_transactions directories."
    exit 1
fi

# Display menu and get selection
CHOICE=$(display_menu "${DISCOVERED_BANKS[@]}")
TOTAL=${#DISCOVERED_BANKS[@]}
MAX_CHOICE=$((TOTAL + 1))

if ! validate_choice "$CHOICE" "$MAX_CHOICE"; then
    echo -e "${RED}✗ Invalid selection.${NC}"
    exit 1
fi

# Determine which banks to process
SELECTED_BANKS=()
if [[ $CHOICE -eq $MAX_CHOICE ]]; then
    # All banks selected
    SELECTED_BANKS=("${DISCOVERED_BANKS[@]}")
    echo -e "${GREEN}✓ Processing all $TOTAL bank(s)${NC}"
else
    # Single bank selected
    SELECTED_BANKS=("${DISCOVERED_BANKS[$((CHOICE - 1))]}")
    echo -e "${GREEN}✓ Processing 1 bank${NC}"
fi

echo ""
echo -e "${BLUE}=========================================="
echo "Starting Enrichment"
echo "==========================================${NC}"
echo ""

# Counters
SUCCESS=0
FAILED=0

# Process selected banks
for bank_config in "${SELECTED_BANKS[@]}"; do
    IFS=':' read -r bank_folder config_file config_path <<< "$bank_config"

    # Check if config file exists
    if [[ ! -f "$config_path" ]]; then
        echo -e "${RED}✗ FAILED${NC}: $config_path not found"
        ((FAILED++))
        continue
    fi

    echo -n "Processing ${bank_folder}... "

    # Run the enrichment
    if python "$SCRIPT_DIR/main.py" -f "$config_path" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ SUCCESS${NC}"
        ((SUCCESS++))
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
    fi
done

echo ""
echo -e "${BLUE}=========================================="
echo "Summary:"
echo -e "  Total:    ${#SELECTED_BANKS[@]}"
echo -e "  ${GREEN}Success: $SUCCESS${NC}"
echo -e "  ${RED}Failed:  $FAILED${NC}"
echo "==========================================${NC}"
echo ""

# Exit with error code if any bank failed
if [[ $FAILED -gt 0 ]]; then
    exit 1
fi

exit 0
