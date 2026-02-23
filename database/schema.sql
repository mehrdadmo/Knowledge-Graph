-- Logistics and Trade Knowledge Graph SQL Schema
-- This schema supports the document processing pipeline for knowledge graph construction

-- Customers table: Logistics firms using the system
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Documents table: Processed documents (invoices, shipping documents, etc.)
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    document_type VARCHAR(100) NOT NULL, -- 'invoice', 'bill_of_lading', 'packing_list', etc.
    document_number VARCHAR(255), -- e.g., "Invoice #55"
    file_path VARCHAR(500),
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Field definitions: Template for different types of fields that can be extracted
CREATE TABLE field_definitions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE, -- 'ShipperName', 'ConsigneeName', 'HS_Code', 'Product', 'Price', etc.
    description TEXT,
    field_type VARCHAR(50) NOT NULL, -- 'text', 'number', 'date', 'code'
    target_graph_label VARCHAR(100), -- 'LegalEntity', 'HSCode', 'Product', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Document fields: Extracted field values from documents
CREATE TABLE document_fields (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    field_definition_id INTEGER NOT NULL REFERENCES field_definitions(id),
    raw_value TEXT, -- Original OCR extracted value
    normalized_value TEXT, -- Cleaned/processed value
    hitl_value TEXT, -- Human-in-the-loop corrected value (prioritized over normalized)
    confidence_score DECIMAL(3,2), -- OCR confidence 0.00-1.00
    hitl_finished_at TIMESTAMP, -- When human-in-the-loop correction was completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, field_definition_id)
);

-- Indexes for performance
CREATE INDEX idx_documents_customer_id ON documents(customer_id);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_document_fields_document_id ON document_fields(document_id);
CREATE INDEX idx_document_fields_field_definition_id ON document_fields(field_definition_id);
CREATE INDEX idx_document_fields_hitl_finished_at ON document_fields(hitl_finished_at);
CREATE INDEX idx_field_definitions_name ON field_definitions(name);

-- CDC (Change Data Capture) Setup
-- pg_notify is built-in function, no extension needed

-- Function to trigger notification when hitl_finished_at is updated
CREATE OR REPLACE FUNCTION notify_hitl_finished()
RETURNS TRIGGER AS $$
BEGIN
    -- Only notify if hitl_finished_at was actually set/updated
    IF NEW.hitl_finished_at IS NOT NULL AND (OLD.hitl_finished_at IS NULL OR NEW.hitl_finished_at != OLD.hitl_finished_at) THEN
        PERFORM pg_notify(
            'hitl_finished',
            json_build_object(
                'document_id', NEW.document_id,
                'field_id', NEW.id,
                'field_name', (SELECT name FROM field_definitions WHERE id = NEW.field_definition_id),
                'hitl_value', NEW.hitl_value,
                'finished_at', NEW.hitl_finished_at
            )::text
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically send notifications on hitl_finished_at updates
CREATE TRIGGER trigger_hitl_finished
    AFTER UPDATE ON document_fields
    FOR EACH ROW
    EXECUTE FUNCTION notify_hitl_finished();

-- Function to trigger notification when new documents are created
CREATE OR REPLACE FUNCTION notify_document_created()
RETURNS TRIGGER AS $$
BEGIN
    PERFORM pg_notify(
        'document_created',
        json_build_object(
            'document_id', NEW.id,
            'customer_id', NEW.customer_id,
            'document_type', NEW.document_type,
            'document_number', NEW.document_number,
            'created_at', NEW.created_at
        )::text
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for new document notifications
CREATE TRIGGER trigger_document_created
    AFTER INSERT ON documents
    FOR EACH ROW
    EXECUTE FUNCTION notify_document_created();

-- Function to get the best value (prioritizing hitl_value over normalized_value over raw_value)
CREATE OR REPLACE FUNCTION get_best_field_value(
    p_raw_value TEXT,
    p_normalized_value TEXT, 
    p_hitl_value TEXT
) RETURNS TEXT AS $$
BEGIN
    IF p_hitl_value IS NOT NULL AND p_hitl_value != '' THEN
        RETURN p_hitl_value;
    ELSIF p_normalized_value IS NOT NULL AND p_normalized_value != '' THEN
        RETURN p_normalized_value;
    ELSE
        RETURN p_raw_value;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- View for easy access to document fields with best values
CREATE VIEW document_fields_view AS
SELECT 
    df.id,
    df.document_id,
    d.document_number,
    d.customer_id,
    c.name as customer_name,
    fd.name as field_name,
    fd.target_graph_label,
    get_best_field_value(df.raw_value, df.normalized_value, df.hitl_value) as best_value,
    df.raw_value,
    df.normalized_value,
    df.hitl_value,
    df.confidence_score,
    df.created_at
FROM document_fields df
JOIN documents d ON df.document_id = d.id
JOIN customers c ON d.customer_id = c.id
JOIN field_definitions fd ON df.field_definition_id = fd.id;
