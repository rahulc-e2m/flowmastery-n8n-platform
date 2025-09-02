#!/bin/bash

# Client API Load Testing Script for FlowMastery n8n Platform
# This script runs comprehensive load tests specifically for client management APIs

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
REPORTS_DIR="${PROJECT_DIR}/reports"

# Test configurations
LIGHT_LOAD_USERS=10
MODERATE_LOAD_USERS=25
HEAVY_LOAD_USERS=50

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if locust is installed
    if ! command -v locust &> /dev/null; then
        error "Locust is not installed. Please run: pip install -r requirements.txt"
        exit 1
    fi
    
    # Check if backend is running
    if ! curl -s "${BACKEND_URL}/health/" > /dev/null; then
        error "Backend is not accessible at ${BACKEND_URL}"
        error "Please ensure the FlowMastery backend is running"
        exit 1
    fi
    
    # Create reports directory
    mkdir -p "${REPORTS_DIR}"
    
    success "Prerequisites check passed"
}

# Test backend connectivity
test_connectivity() {
    log "Testing backend connectivity..."
    
    # Test basic health check
    if curl -s "${BACKEND_URL}/health/" | grep -q "healthy"; then
        success "Backend health check passed"
    else
        error "Backend health check failed"
        exit 1
    fi
    
    # Test API endpoints accessibility
    if curl -s "${BACKEND_URL}/api/v1/auth/status" > /dev/null; then
        success "API endpoints are accessible"
    else
        error "API endpoints are not accessible"
        exit 1
    fi
}

# Run client authentication load test
run_auth_load_test() {
    local users=$1
    local duration=$2
    local test_name=$3
    
    log "Running authentication load test: ${test_name}"
    log "Users: ${users}, Duration: ${duration}"
    
    locust \
        -f "${PROJECT_DIR}/tests/auth/test_auth_load.py" \
        --host="${BACKEND_URL}" \
        --users="${users}" \
        --spawn-rate=5 \
        --run-time="${duration}" \
        --headless \
        --html="${REPORTS_DIR}/auth_${test_name}_$(date +%Y%m%d_%H%M%S).html" \
        --csv="${REPORTS_DIR}/auth_${test_name}_$(date +%Y%m%d_%H%M%S)"
    
    if [ $? -eq 0 ]; then
        success "Authentication load test (${test_name}) completed successfully"
    else
        error "Authentication load test (${test_name}) failed"
        return 1
    fi
}

# Run client management load test
run_client_management_test() {
    local users=$1
    local duration=$2
    local test_name=$3
    
    log "Running client management load test: ${test_name}"
    log "Users: ${users}, Duration: ${duration}"
    
    locust \
        -f "${PROJECT_DIR}/tests/clients/test_client_management.py" \
        --host="${BACKEND_URL}" \
        --users="${users}" \
        --spawn-rate=3 \
        --run-time="${duration}" \
        --headless \
        --html="${REPORTS_DIR}/client_mgmt_${test_name}_$(date +%Y%m%d_%H%M%S).html" \
        --csv="${REPORTS_DIR}/client_mgmt_${test_name}_$(date +%Y%m%d_%H%M%S)"
    
    if [ $? -eq 0 ]; then
        success "Client management load test (${test_name}) completed successfully"
    else
        error "Client management load test (${test_name}) failed"
        return 1
    fi
}

# Run specific client API endpoint tests
run_client_api_tests() {
    log "Running specific client API endpoint tests..."
    
    # Test client creation performance
    log "Testing client creation API..."
    locust \
        -f "${PROJECT_DIR}/tests/clients/test_client_management.py" \
        --host="${BACKEND_URL}" \
        --users=20 \
        --spawn-rate=5 \
        --run-time="2m" \
        --headless \
        --tags="client_create" \
        --html="${REPORTS_DIR}/client_create_api_$(date +%Y%m%d_%H%M%S).html"
    
    # Test client listing performance
    log "Testing client listing API..."
    locust \
        -f "${PROJECT_DIR}/tests/clients/test_client_management.py" \
        --host="${BACKEND_URL}" \
        --users=30 \
        --spawn-rate=10 \
        --run-time="2m" \
        --headless \
        --tags="client_list" \
        --html="${REPORTS_DIR}/client_list_api_$(date +%Y%m%d_%H%M%S).html"
    
    # Test n8n configuration performance
    log "Testing n8n configuration API..."
    locust \
        -f "${PROJECT_DIR}/tests/clients/test_client_management.py" \
        --host="${BACKEND_URL}" \
        --users=15 \
        --spawn-rate=3 \
        --run-time="3m" \
        --headless \
        --tags="n8n_config" \
        --html="${REPORTS_DIR}/n8n_config_api_$(date +%Y%m%d_%H%M%S).html"
    
    success "Client API endpoint tests completed"
}

# Run performance baseline test
run_baseline_test() {
    log "Running baseline performance test..."
    
    locust \
        -f "${PROJECT_DIR}/tests/clients/test_client_management.py" \
        --host="${BACKEND_URL}" \
        --users=5 \
        --spawn-rate=1 \
        --run-time="1m" \
        --headless \
        --html="${REPORTS_DIR}/baseline_$(date +%Y%m%d_%H%M%S).html" \
        --csv="${REPORTS_DIR}/baseline_$(date +%Y%m%d_%H%M%S)"
    
    success "Baseline test completed"
}

# Main execution function
main() {
    log "Starting FlowMastery Client API Load Testing"
    log "============================================="
    
    # Check prerequisites
    check_prerequisites
    test_connectivity
    
    # Run baseline test first
    run_baseline_test
    
    case "${1:-all}" in
        "quick")
            log "Running quick client API tests..."
            run_auth_load_test 10 "2m" "quick"
            run_client_management_test 10 "2m" "quick"
            ;;
        "auth")
            log "Running authentication-focused tests..."
            run_auth_load_test 15 "3m" "focused"
            run_auth_load_test 30 "5m" "moderate"
            ;;
        "client")
            log "Running client management-focused tests..."
            run_client_management_test 15 "3m" "focused"
            run_client_api_tests
            ;;
        "stress")
            log "Running stress tests..."
            run_auth_load_test 50 "5m" "stress"
            run_client_management_test 50 "5m" "stress"
            ;;
        "all"|*)
            log "Running comprehensive client API load tests..."
            
            # Authentication tests
            log "Phase 1: Authentication Load Tests"
            run_auth_load_test ${LIGHT_LOAD_USERS} "2m" "light"
            run_auth_load_test ${MODERATE_LOAD_USERS} "3m" "moderate"
            
            # Client management tests
            log "Phase 2: Client Management Load Tests"
            run_client_management_test ${LIGHT_LOAD_USERS} "3m" "light"
            run_client_management_test ${MODERATE_LOAD_USERS} "5m" "moderate"
            
            # Specific API tests
            log "Phase 3: Specific API Endpoint Tests"
            run_client_api_tests
            
            # Heavy load test
            log "Phase 4: Heavy Load Test"
            run_client_management_test ${HEAVY_LOAD_USERS} "8m" "heavy"
            ;;
    esac
    
    # Generate summary report
    log "Generating test summary..."
    echo "# FlowMastery Client API Load Test Summary" > "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    echo "## Test Execution Date: $(date)" >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    echo "## Backend URL: ${BACKEND_URL}" >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    echo "## Test Type: ${1:-all}" >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    echo "" >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    echo "### Generated Reports:" >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md"
    ls -la "${REPORTS_DIR}"/*.html 2>/dev/null | tail -10 >> "${REPORTS_DIR}/test_summary_$(date +%Y%m%d_%H%M%S).md" || true
    
    success "All client API load tests completed successfully!"
    log "Reports generated in: ${REPORTS_DIR}"
    log "View HTML reports in your browser for detailed results"
}

# Handle script arguments
case "${1:-}" in
    "-h"|"--help")
        echo "FlowMastery Client API Load Testing Script"
        echo ""
        echo "Usage: $0 [test_type]"
        echo ""
        echo "Test Types:"
        echo "  quick    - Quick smoke tests (2 minutes each)"
        echo "  auth     - Authentication-focused tests"
        echo "  client   - Client management-focused tests"
        echo "  stress   - High-load stress tests"
        echo "  all      - Comprehensive test suite (default)"
        echo ""
        echo "Environment Variables:"
        echo "  BACKEND_URL - Backend URL (default: http://localhost:8000)"
        echo ""
        echo "Example:"
        echo "  $0 quick"
        echo "  BACKEND_URL=http://localhost:8080 $0 client"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac