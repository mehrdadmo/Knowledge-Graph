-- OCR Integration Schema Updates
-- Add support for OCR document integration with Knowledge Graph

-- Add OCR-related columns to existing tables
ALTER TABLE customers 
ADD COLUMN IF NOT EXISTS ocr_user_id INTEGER,
ADD COLUMN IF NOT EXISTS ocr_username VARCHAR(255);

ALTER TABLE documents 
ADD COLUMN IF NOT EXISTS ocr_document_id INTEGER,
ADD COLUMN IF NOT EXISTS ocr_batch_id INTEGER,
ADD COLUMN IF NOT EXISTS ocr_confidence DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS ocr_method VARCHAR(100),
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'manual';

-- Add OCR-specific field definitions
INSERT INTO field_definitions (name, target_graph_label, description) VALUES 
('ShipperName', 'LegalEntity', 'Shipper/Consignor name from OCR'),
('ConsigneeName', 'LegalEntity', 'Consignee name from OCR'),
('NotifyPartyName', 'LegalEntity', 'Notify party name from OCR'),
('ProductDescription', 'Product', 'Product description from OCR'),
('OriginPort', 'Location', 'Port of loading from OCR'),
('DestinationPort', 'Location', 'Port of discharge from OCR'),
('CountryOfOrigin', 'Location', 'Country of origin from OCR'),
('HSCode', 'HSCode', 'HS/Tariff code from OCR'),
('VesselName', 'LegalEntity', 'Vessel name from OCR'),
('VoyageNumber', 'Document', 'Voyage number from OCR'),
('ContainerNumber', 'Document', 'Container number from OCR'),
('SealNumber', 'Document', 'Seal number from OCR'),
('ReferenceNumber', 'Document', 'Reference number from OCR'),
('InvoiceNumber', 'Document', 'Invoice number from OCR'),
('BillOfLadingNumber', 'Document', 'Bill of Lading number from OCR'),
('PackingListNumber', 'Document', 'Packing list number from OCR'),
('InsurancePolicy', 'Document', 'Insurance policy number from OCR'),
('RegistrationNumber', 'Document', 'Registration number from OCR'),
('InspectionDate', 'Document', 'Inspection date from OCR'),
('InspectionPlace', 'Location', 'Inspection place from OCR')
ON CONFLICT (name) DO NOTHING;

-- Create OCR sync tracking table
CREATE TABLE IF NOT EXISTS ocr_sync_log (
    id SERIAL PRIMARY KEY,
    ocr_document_id INTEGER NOT NULL,
    kg_document_id INTEGER,
    sync_status VARCHAR(20) DEFAULT 'pending',
    sync_started_at TIMESTAMP,
    sync_completed_at TIMESTAMP,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_ocr_sync_log_ocr_doc_id ON ocr_sync_log(ocr_document_id);
CREATE INDEX IF NOT EXISTS idx_ocr_sync_log_status ON ocr_sync_log(sync_status);
CREATE INDEX IF NOT EXISTS idx_documents_ocr_id ON documents(ocr_document_id);
CREATE INDEX IF NOT EXISTS idx_customers_ocr_user_id ON customers(ocr_user_id);

-- Add CDC functions for OCR integration
CREATE OR REPLACE FUNCTION notify_ocr_document_sync()
RETURNS TRIGGER AS $$
BEGIN
    -- Send notification when OCR document is synced to KG
    PERFORM pg_notify(
        'ocr_document_synced',
        json_build_object(
            'ocr_document_id', NEW.ocr_document_id,
            'kg_document_id', NEW.id,
            'sync_status', 'synced',
            'timestamp', CURRENT_TIMESTAMP
        )::text
    );
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add trigger for OCR document sync
DROP TRIGGER IF EXISTS trigger_ocr_document_sync ON documents;
CREATE TRIGGER trigger_ocr_document_sync
    AFTER UPDATE ON documents
    FOR EACH ROW
    WHEN (NEW.ocr_document_id IS NOT NULL AND OLD.ocr_document_id IS NULL)
    EXECUTE FUNCTION notify_ocr_document_sync();

-- Add function to handle OCR field corrections
CREATE OR REPLACE FUNCTION handle_ocr_field_correction()
RETURNS TRIGGER AS $$
BEGIN
    -- When an OCR field gets HITL correction, notify the system
    IF OLD.hitl_value IS NULL AND NEW.hitl_value IS NOT NULL THEN
        PERFORM pg_notify(
            'ocr_field_corrected',
            json_build_object(
                'document_id', NEW.document_id,
                'field_name', fd.name,
                'old_value', OLD.normalized_value,
                'new_value', NEW.hitl_value,
                'timestamp', CURRENT_TIMESTAMP
            )::text
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create view for OCR integration status
CREATE OR REPLACE VIEW ocr_integration_status AS
SELECT 
    c.name as customer_name,
    c.ocr_user_id,
    COUNT(d.id) as total_documents,
    COUNT(CASE WHEN d.ocr_document_id IS NOT NULL THEN 1 END) as ocr_documents,
    COUNT(CASE WHEN d.ocr_document_id IS NOT NULL AND d.sync_status = 'synced' THEN 1 END) as synced_documents,
    ROUND(
        COUNT(CASE WHEN d.ocr_document_id IS NOT NULL AND d.sync_status = 'synced' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(CASE WHEN d.ocr_document_id IS NOT NULL THEN 1 END), 0), 
        2
    ) as sync_percentage,
    MAX(d.created_at) as last_document_date
FROM customers c
LEFT JOIN documents d ON c.id = d.customer_id
WHERE c.ocr_user_id IS NOT NULL
GROUP BY c.id, c.name, c.ocr_user_id
ORDER BY c.name;

-- Create function to get OCR document statistics
CREATE OR REPLACE FUNCTION get_ocr_statistics()
RETURNS TABLE(
    total_ocr_documents BIGINT,
    synced_documents BIGINT,
    pending_sync BIGINT,
    failed_sync BIGINT,
    sync_percentage DECIMAL(5,2),
    last_sync_time TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(osl.id) as total_ocr_documents,
        COUNT(CASE WHEN osl.sync_status = 'completed' THEN 1 END) as synced_documents,
        COUNT(CASE WHEN osl.sync_status = 'pending' THEN 1 END) as pending_sync,
        COUNT(CASE WHEN osl.sync_status = 'failed' THEN 1 END) as failed_sync,
        ROUND(
            COUNT(CASE WHEN osl.sync_status = 'completed' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(osl.id), 0), 
            2
        ) as sync_percentage,
        MAX(osl.sync_completed_at) as last_sync_time
    FROM ocr_sync_log osl;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON ocr_sync_log TO your_app_user;
-- GRANT SELECT ON ocr_integration_status TO your_app_user;
-- GRANT EXECUTE ON FUNCTION get_ocr_statistics() TO your_app_user;
