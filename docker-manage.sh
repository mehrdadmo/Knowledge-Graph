#!/bin/bash

# Logistics Knowledge Graph Docker Setup Script
# This script sets up and manages the Docker environment for the knowledge graph

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "docker-compose is not installed or not in PATH."
        exit 1
    fi
}

# Determine docker-compose command
DOCKER_COMPOSE=""
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Function to start services
start_services() {
    print_status "Starting all services..."
    $DOCKER_COMPOSE up -d
    print_success "All services started successfully!"
    
    print_status "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    if $DOCKER_COMPOSE ps | grep -q "unhealthy"; then
        print_warning "Some services may not be healthy yet. Check with: $DOCKER_COMPOSE ps"
    else
        print_success "All services are healthy!"
    fi
    
    print_status "Service URLs:"
    echo "  - PostgreSQL: localhost:5432"
    echo "  - Neo4j HTTP: http://localhost:7474"
    echo "  - Neo4j Bolt: bolt://localhost:7687"
    echo "  - GraphRAG API: http://localhost:8000"
    echo "  - Neo4j Browser (optional): http://localhost:7475"
}

# Function to stop services
stop_services() {
    print_status "Stopping all services..."
    $DOCKER_COMPOSE down
    print_success "All services stopped successfully!"
}

# Function to reset services (stop, remove volumes, start)
reset_services() {
    print_warning "This will remove all data from PostgreSQL and Neo4j!"
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing all containers and volumes..."
        $DOCKER_COMPOSE down -v
        print_success "All containers and volumes removed!"
        
        print_status "Starting fresh services..."
        $DOCKER_COMPOSE up -d
        print_success "Fresh services started successfully!"
    else
        print_status "Operation cancelled."
    fi
}

# Function to show service status
show_status() {
    print_status "Service Status:"
    $DOCKER_COMPOSE ps
    
    print_status "\nService Health:"
    $DOCKER_COMPOSE ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

# Function to initialize the knowledge graph
init_kg() {
    print_status "Initializing knowledge graph..."
    $DOCKER_COMPOSE exec kg_sync python cli.py init
    print_success "Knowledge graph initialized!"
}

# Function to sync all data
sync_all() {
    print_status "Syncing all data to knowledge graph..."
    $DOCKER_COMPOSE exec kg_sync python cli.py sync --all
    print_success "Data sync completed!"
}

# Function to test connections
test_connections() {
    print_status "Testing database connections..."
    $DOCKER_COMPOSE exec kg_sync python cli.py test-connection
}

# Function to test GraphRAG API
test_api() {
    print_status "Testing GraphRAG API..."
    
    # Check if API is accessible
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "GraphRAG API is accessible!"
        
        # Run API tests
        if [ -f "samples/test_graphrag_api.py" ]; then
            print_status "Running comprehensive API tests..."
            $DOCKER_COMPOSE exec kg_api python samples/test_graphrag_api.py
        else
            print_warning "API test script not found"
        fi
    else
        print_error "GraphRAG API is not accessible on http://localhost:8000"
        print_status "Make sure the API service is running:"
        echo "  docker-compose logs kg_api"
    fi
}

# Function to access interactive query client
interactive_query() {
    print_status "Starting interactive query client..."
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        $DOCKER_COMPOSE exec kg_api python samples/interactive_query.py
    else
        print_error "GraphRAG API is not accessible"
        print_status "Start services first: ./docker-manage.sh start"
    fi
}

# Function to show API logs
api_logs() {
    print_status "Showing API logs..."
    $DOCKER_COMPOSE logs -f kg_api
}

# Function to show real-time sync logs
realtime_logs() {
    print_status "Showing real-time sync logs..."
    $DOCKER_COMPOSE logs -f kg_realtime
}

# Function to show sync status
show_sync_status() {
    print_status "Showing sync status..."
    $DOCKER_COMPOSE exec kg_sync python cli.py status
}

# Function to access CLI
access_cli() {
    print_status "Accessing CLI in kg_sync container..."
    $DOCKER_COMPOSE exec -it kg_sync python cli.py --help
}

# Function to show logs
show_logs() {
    service=$1
    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        $DOCKER_COMPOSE logs -f
    else
        print_status "Showing logs for $service..."
        $DOCKER_COMPOSE logs -f "$service"
    fi
}

# Function to start with browser
start_with_browser() {
    print_status "Starting services with Neo4j browser..."
    $DOCKER_COMPOSE --profile browser up -d
    print_success "Services started with browser!"
    print_status "Neo4j Browser: http://localhost:7475"
}

# Main menu
case "${1:-}" in
    "start")
        check_docker
        check_docker_compose
        start_services
        ;;
    "stop")
        check_docker
        check_docker_compose
        stop_services
        ;;
    "restart")
        check_docker
        check_docker_compose
        stop_services
        sleep 5
        start_services
        ;;
    "reset")
        check_docker
        check_docker_compose
        reset_services
        ;;
    "status")
        check_docker
        check_docker_compose
        show_status
        ;;
    "init")
        check_docker
        check_docker_compose
        init_kg
        ;;
    "sync")
        check_docker
        check_docker_compose
        sync_all
        ;;
    "test")
        check_docker
        check_docker_compose
        test_connections
        ;;
    "api-test")
        check_docker
        check_docker_compose
        test_api
        ;;
    "query")
        check_docker
        check_docker_compose
        interactive_query
        ;;
    "api-logs")
        check_docker
        check_docker_compose
        api_logs
        ;;
    "realtime-logs")
        check_docker
        check_docker_compose
        realtime_logs
        ;;
    "sync-status")
        check_docker
        check_docker_compose
        show_sync_status
        ;;
    "cli")
        check_docker
        check_docker_compose
        access_cli
        ;;
    "logs")
        check_docker
        check_docker_compose
        show_logs "$2"
        ;;
    "browser")
        check_docker
        check_docker_compose
        start_with_browser
        ;;
    "ocr-sync")
        echo "🔄 Syncing OCR document to Knowledge Graph..."
        if [ -z "$2" ]; then
            echo "Usage: $0 ocr-sync <document_id>"
            exit 1
        fi
        docker-compose exec kg_ocr_integration python ocr_integration.py --sync-document $2
        ;;
    "ocr-batch")
        echo "📦 Batch syncing OCR documents..."
        limit=${2:-10}
        docker-compose exec kg_ocr_integration python ocr_integration.py --batch-sync $limit
        ;;
    "ocr-status")
        echo "📊 OCR Integration Status..."
        docker-compose exec kg_ocr_integration python ocr_integration.py --status
        ;;
    "ocr-test")
        echo "🧪 Testing OCR Integration..."
        docker-compose exec kg_ocr_integration python ../samples/test_ocr_integration.py --test
        ;;
    "ocr-demo")
        echo "🎮 OCR Integration Interactive Demo..."
        docker-compose exec kg_ocr_integration python ../samples/test_ocr_integration.py --demo
        ;;
    "help"|"")
        echo "🚀 Logistics Knowledge Graph - Complete Platform"
        echo "==============================================="
        echo
        echo "Usage: $0 [COMMAND]"
        echo
        echo "# �️ Compliance Engine Commands"
        echo "  compliance-check <document_id>    Check document compliance"
        echo "  compliance-test                  Test compliance engine"
        echo "  compliance-rules                 List compliance rules"
        echo "  compliance-iban <iban>           Validate IBAN"
        echo "  compliance-dashboard             Show compliance dashboard"
        echo
        echo "# 🔄 OCR Integration Commands"
        echo "  ocr-sync <document_id>          Sync OCR document to Knowledge Graph"
        echo "  ocr-batch [limit]               Batch sync OCR documents (default: 10)"
        echo "  ocr-status                      Show OCR Integration Status"
        echo "  ocr-test                        Test OCR Integration End-to-End"
        echo "  ocr-demo                        OCR Integration Interactive Demo"
        echo
        echo "# 🤖 GraphRAG API Commands"
        echo "  start                           Start all services including OCR & Compliance"
        echo "  stop                            Stop all services"
        echo "  restart                         Restart all services"
        echo "  reset                           Reset all services (removes data)"
        echo "  status                          Show service status"
        echo "  init                            Initialize knowledge graph"
        echo "  sync                            Sync all data to knowledge graph"
        echo "  test                            Test database connections"
        echo "  api-test                        Test GraphRAG API endpoints"
        echo "  query                           Interactive query client"
        echo
        echo "# 📊 Monitoring Commands"
        echo "  logs [service]                  Show logs for all or specific service"
        echo "  api-logs                        Show GraphRAG API logs"
        echo "  realtime-logs                   Show real-time CDC logs"
        echo "  sync-logs                       Show sync service logs"
        echo "  compliance-logs                 Show compliance engine logs"
        echo "  browser                         Open Neo4j Browser"
        echo
        echo "# 🎯 Quick Start"
        echo "  1. ./docker-manage.sh start"
        echo "  2. ./docker-manage.sh init"
        echo "  3. ./docker-manage.sh compliance-test"
        echo "  4. ./docker-manage.sh compliance-check 12345"
        echo "  5. ./docker-manage.sh query"
        echo
        echo "# 🌐 Access Points"
        echo "  GraphRAG API: http://localhost:8000"
        echo "  Compliance API: http://localhost:8001"
        echo "  API Docs: http://localhost:8000/docs"
        echo "  Compliance Docs: http://localhost:8001/docs"
        echo "  Neo4j Browser: http://localhost:7474"
        echo "  PostgreSQL: localhost:5432"
        echo "  help          Show this help message"
        echo
        echo "Examples:"
        echo "  $0 start                    # Start all services"
        echo "  $0 init                     # Initialize the knowledge graph"
        echo "  $0 api-test                 # Test GraphRAG API"
        echo "  $0 query                    # Interactive query client"
        echo "  $0 logs postgres            # Show PostgreSQL logs"
        echo "  $0 browser                  # Start with Neo4j browser"
        echo
        echo "Service URLs:"
        echo "  - GraphRAG API: http://localhost:8000"
        echo "  - Neo4j Browser: http://localhost:7474"
        echo "  - API Docs: http://localhost:8000/docs"
        ;;
    *)
        print_error "Unknown command: $1"
        echo "Use '$0 help' for available commands."
        exit 1
        ;;
esac
