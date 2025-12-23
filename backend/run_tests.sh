#!/bin/bash
# Test runner script for categorized testing
# Usage: ./run_tests.sh [category] [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default options
COVERAGE=false
VERBOSE=false
CATEGORY=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--category)
            CATEGORY="$2"
            shift 2
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --category CATEGORY    Run tests by category (unit, api, utils, ai, auth, file_upload, service)"
            echo "  --coverage                 Run with coverage report"
            echo "  -v, --verbose              Verbose output"
            echo "  -h, --help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 -c unit                 Run unit tests"
            echo "  $0 -c api --coverage       Run API tests with coverage"
            echo "  $0 -c auth -v              Run auth tests verbosely"
            echo ""
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ -n "$CATEGORY" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $CATEGORY"
    echo -e "${BLUE}Running tests for category: ${CATEGORY}${NC}"
else
    echo -e "${BLUE}Running all tests${NC}"
fi

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing --cov-report=html"
    echo -e "${YELLOW}Coverage report will be generated${NC}"
fi

# Run the tests
echo -e "${GREEN}Executing: $PYTEST_CMD${NC}"
echo ""

$PYTEST_CMD

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Tests passed!${NC}"
    if [ "$COVERAGE" = true ]; then
        echo -e "${GREEN}Coverage report: htmlcov/index.html${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}✗ Tests failed (exit code: $EXIT_CODE)${NC}"
fi

exit $EXIT_CODE

