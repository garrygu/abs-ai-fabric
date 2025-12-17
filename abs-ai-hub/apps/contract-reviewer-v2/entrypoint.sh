#!/bin/bash
# Entrypoint script for Contract Reviewer v2
# Handles database migrations before starting the application

set -e

echo "🚀 Starting Contract Reviewer v2"

# Function to wait for PostgreSQL
wait_for_postgres() {
    local max_attempts=30
    local attempt=0
    
    echo "⏳ Waiting for PostgreSQL to be ready..."
    
    until PGPASSWORD="${POSTGRES_PASSWORD}" pg_isready -h "${POSTGRES_HOST:-document-hub-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-hub_user}" -d "${POSTGRES_DB:-document_hub}" > /dev/null 2>&1; do
        attempt=$((attempt + 1))
        
        if [ $attempt -ge $max_attempts ]; then
            echo "❌ PostgreSQL is not ready after $max_attempts attempts"
            exit 1
        fi
        
        echo "  Attempt $attempt/$max_attempts - PostgreSQL not ready yet, waiting..."
        sleep 2
    done
    
    echo "✅ PostgreSQL is ready"
}

# Function to run migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    
    if python -c "import migrate_add_source_type" 2>/dev/null; then
        python migrate_add_source_type.py
        echo "✅ Migrations completed"
    else
        echo "⚠️ Migration script not found, skipping..."
    fi
}

# Main execution
main() {
    # Wait for PostgreSQL
    wait_for_postgres
    
    # Run migrations
    run_migrations
    
    # Start the application
    echo "🚀 Starting application..."
    exec "$@"
}

# Run main function
main "$@"




