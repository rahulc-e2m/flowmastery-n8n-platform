#!/bin/bash

# Metrics Load Testing Script
# Usage: ./run_metrics_tests.sh [test_type]
# Test types: quick, comprehensive, stress, cache, admin, all

set -e

# Configuration
LOCUST_HOST="http://localhost:8000"
REPORTS_DIR="./reports"

# Ensure reports directory exists
mkdir -p $REPORTS_DIR

# Function to run locust test
run_test() {
    local test_file=$1
    local users=$2
    local spawn_rate=$3
    local run_time=$4
    local test_name=$5
    local csv_prefix=$6
    
    echo "🚀 Running $test_name..."
    echo "   Users: $users | Spawn Rate: $spawn_rate | Duration: $run_time"
    
    python -m locust \
        -f "$test_file" \
        --host="$LOCUST_HOST" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="$run_time" \
        --headless \
        --csv="$REPORTS_DIR/${csv_prefix}_$(date +%Y%m%d_%H%M%S)" \
        --html="$REPORTS_DIR/${csv_prefix}_$(date +%Y%m%d_%H%M%S).html" \
        --only-summary
}

# Test configurations
case "${1:-comprehensive}" in
    "quick")
        echo "🏃‍♂️ Running Quick Metrics Test (5 users, 30 seconds)"
        run_test "tests/metrics/test_metrics_load.py" 5 1 "30s" "Quick Metrics Test" "metrics_quick"
        ;;
    
    "comprehensive")
        echo "🔍 Running Comprehensive Metrics Test (15 users, 2 minutes)"
        run_test "tests/metrics/test_metrics_load.py" 15 3 "120s" "Comprehensive Metrics Test" "metrics_comprehensive"
        ;;
    
    "stress")
        echo "💪 Running Metrics Stress Test (50 users, 5 minutes)"
        run_test "tests/metrics/test_metrics_load.py" 50 10 "300s" "Metrics Stress Test" "metrics_stress"
        ;;
    
    "cache")
        echo "⚡ Running Cache Performance Test (25 users, 90 seconds)"
        run_test "tests/metrics/test_metrics_load.py" 25 5 "90s" "Cache Performance Test" "metrics_cache"
        ;;
    
    "admin")
        echo "👑 Running Admin-focused Test (10 users, 2 minutes)"
        run_test "tests/metrics/test_metrics_load.py" 10 2 "120s" "Admin Metrics Test" "metrics_admin"
        ;;
    
    "all")
        echo "🎯 Running All Metrics Tests..."
        
        echo "1/5 - Quick Test"
        run_test "tests/metrics/test_metrics_load.py" 5 1 "30s" "Quick Metrics Test" "metrics_quick"
        
        echo "2/5 - Admin Test"
        run_test "tests/metrics/test_metrics_load.py" 10 2 "60s" "Admin Metrics Test" "metrics_admin"
        
        echo "3/5 - Cache Test"
        run_test "tests/metrics/test_metrics_load.py" 25 5 "90s" "Cache Performance Test" "metrics_cache"
        
        echo "4/5 - Comprehensive Test"
        run_test "tests/metrics/test_metrics_load.py" 15 3 "120s" "Comprehensive Metrics Test" "metrics_comprehensive"
        
        echo "5/5 - Stress Test"
        run_test "tests/metrics/test_metrics_load.py" 50 10 "180s" "Metrics Stress Test" "metrics_stress"
        ;;
    
    *)
        echo "❌ Unknown test type: $1"
        echo "Available test types:"
        echo "  quick        - 5 users, 30 seconds"
        echo "  comprehensive - 15 users, 2 minutes"
        echo "  stress       - 50 users, 5 minutes"
        echo "  cache        - 25 users, 90 seconds"
        echo "  admin        - 10 users, 2 minutes"
        echo "  all          - Run all tests in sequence"
        echo ""
        echo "Usage: $0 [test_type]"
        exit 1
        ;;
esac

echo "✅ Metrics load testing completed!"
echo "📊 Reports saved in: $REPORTS_DIR"
echo ""
echo "🔍 To view detailed results:"
echo "   - Open HTML reports in browser"
echo "   - Check CSV files for raw data"
echo "   - Review console output above"