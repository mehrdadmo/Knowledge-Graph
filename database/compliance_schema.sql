-- Compliance Engine Database Schema
-- Track compliance checks, results, and reports

-- Compliance rules table
CREATE TABLE IF NOT EXISTS compliance_rules (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    enabled BOOLEAN DEFAULT TRUE,
    parameters JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance reports table
CREATE TABLE IF NOT EXISTS compliance_reports (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id),
    document_number VARCHAR(255),
    overall_status VARCHAR(20) NOT NULL CHECK (overall_status IN ('COMPLIANT', 'NON_COMPLIANT', 'WARNING', 'PENDING_REVIEW', 'ERROR')),
    total_rules_checked INTEGER NOT NULL,
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    report_data JSONB NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance results table (detailed results for each rule)
CREATE TABLE IF NOT EXISTS compliance_results (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES compliance_reports(id),
    rule_id VARCHAR(50) NOT NULL REFERENCES compliance_rules(id),
    status VARCHAR(20) NOT NULL CHECK (status IN ('COMPLIANT', 'NON_COMPLIANT', 'WARNING', 'PENDING_REVIEW', 'ERROR')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO')),
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    entity_id VARCHAR(255),
    entity_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sanctions lists table
CREATE TABLE IF NOT EXISTS sanctions_lists (
    id SERIAL PRIMARY KEY,
    list_name VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    version VARCHAR(50),
    effective_date DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Sanctioned entities table
CREATE TABLE IF NOT EXISTS sanctioned_entities (
    id SERIAL PRIMARY KEY,
    sanctions_list_id INTEGER REFERENCES sanctions_lists(id),
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    country_code VARCHAR(2),
    identification_number VARCHAR(100),
    sanction_type VARCHAR(50),
    additional_info JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watchlists table
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    list_name VARCHAR(100) NOT NULL,
    source VARCHAR(100) NOT NULL,
    risk_level VARCHAR(20) CHECK (risk_level IN ('HIGH', 'MEDIUM', 'LOW')),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Watchlist entities table
CREATE TABLE IF NOT EXISTS watchlist_entities (
    id SERIAL PRIMARY KEY,
    watchlist_id INTEGER REFERENCES watchlists(id),
    entity_name VARCHAR(255) NOT NULL,
    entity_type VARCHAR(50),
    country_code VARCHAR(2),
    risk_score INTEGER CHECK (risk_score >= 0 AND risk_score <= 100),
    reason_for_listing TEXT,
    additional_info JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade restrictions table
CREATE TABLE IF NOT EXISTS trade_restrictions (
    id SERIAL PRIMARY KEY,
    restriction_type VARCHAR(50) NOT NULL, -- 'HS_CODE', 'COUNTRY', 'PRODUCT'
    restriction_value VARCHAR(255) NOT NULL,
    country_code VARCHAR(2),
    description TEXT,
    severity VARCHAR(20) CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    effective_date DATE,
    expiry_date DATE,
    source VARCHAR(100),
    additional_requirements JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- IBAN validation cache table
CREATE TABLE IF NOT EXISTS iban_validation_cache (
    id SERIAL PRIMARY KEY,
    iban VARCHAR(34) NOT NULL UNIQUE,
    country_code VARCHAR(2) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    validation_details JSONB DEFAULT '{}',
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days')
);

-- Document compliance status table (quick lookup)
CREATE TABLE IF NOT EXISTS document_compliance_status (
    document_id INTEGER PRIMARY KEY REFERENCES documents(id),
    last_compliance_check TIMESTAMP,
    overall_status VARCHAR(20) NOT NULL CHECK (overall_status IN ('COMPLIANT', 'NON_COMPLIANT', 'WARNING', 'PENDING_REVIEW', 'ERROR')),
    critical_issues INTEGER DEFAULT 0,
    high_issues INTEGER DEFAULT 0,
    medium_issues INTEGER DEFAULT 0,
    low_issues INTEGER DEFAULT 0,
    last_report_id INTEGER REFERENCES compliance_reports(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Compliance alerts table
CREATE TABLE IF NOT EXISTS compliance_alerts (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'FALSE_POSITIVE')),
    acknowledged_by VARCHAR(255),
    acknowledged_at TIMESTAMP,
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_compliance_reports_document_id ON compliance_reports(document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_status ON compliance_reports(overall_status);
CREATE INDEX IF NOT EXISTS idx_compliance_reports_generated_at ON compliance_reports(generated_at);

CREATE INDEX IF NOT EXISTS idx_compliance_results_report_id ON compliance_results(report_id);
CREATE INDEX IF NOT EXISTS idx_compliance_results_rule_id ON compliance_results(rule_id);
CREATE INDEX IF NOT EXISTS idx_compliance_results_status ON compliance_results(status);

CREATE INDEX IF NOT EXISTS idx_sanctioned_entities_name ON sanctioned_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_sanctioned_entities_country ON sanctioned_entities(country_code);
CREATE INDEX IF NOT EXISTS idx_sanctioned_entities_list ON sanctioned_entities(sanctions_list_id);

CREATE INDEX IF NOT EXISTS idx_watchlist_entities_name ON watchlist_entities(entity_name);
CREATE INDEX IF NOT EXISTS idx_watchlist_entities_risk ON watchlist_entities(risk_score);
CREATE INDEX IF NOT EXISTS idx_watchlist_entities_list ON watchlist_entities(watchlist_id);

CREATE INDEX IF NOT EXISTS idx_trade_restrictions_type ON trade_restrictions(restriction_type);
CREATE INDEX IF NOT EXISTS idx_trade_restrictions_value ON trade_restrictions(restriction_value);
CREATE INDEX IF NOT EXISTS idx_trade_restrictions_country ON trade_restrictions(country_code);

CREATE INDEX IF NOT EXISTS idx_iban_validation_iban ON iban_validation_cache(iban);
CREATE INDEX IF NOT EXISTS idx_iban_validation_country ON iban_validation_cache(country_code);
CREATE INDEX IF NOT EXISTS idx_iban_validation_expires ON iban_validation_cache(expires_at);

CREATE INDEX IF NOT EXISTS idx_document_compliance_status ON document_compliance_status(overall_status);
CREATE INDEX IF NOT EXISTS idx_compliance_alerts_document ON compliance_alerts(document_id);
CREATE INDEX IF NOT EXISTS idx_compliance_alerts_status ON compliance_alerts(status);
CREATE INDEX IF NOT EXISTS idx_compliance_alerts_severity ON compliance_alerts(severity);

-- Insert default compliance rules
INSERT INTO compliance_rules (id, name, description, category, severity) VALUES
('IBAN_FORMAT', 'IBAN Format Validation', 'Validate IBAN format and checksum', 'FINANCIAL', 'HIGH'),
('IBAN_COUNTRY_SANCTION', 'IBAN Country Sanctions Check', 'Check if IBAN country is under sanctions', 'SANCTIONS', 'CRITICAL'),
('COMPANY_ID_FORMAT', 'Company ID Format Validation', 'Validate company registration number format', 'IDENTIFICATION', 'MEDIUM'),
('TAX_ID_VALIDATION', 'Tax ID Validation', 'Validate tax identification numbers', 'FINANCIAL', 'HIGH'),
('ENTITY_SANCTION_LIST', 'Entity Sanctions Screening', 'Screen entities against sanctions lists', 'SANCTIONS', 'CRITICAL'),
('WATCHLIST_SCREENING', 'Watchlist Screening', 'Screen entities against watchlists', 'SANCTIONS', 'HIGH'),
('HS_CODE_RESTRICTION', 'HS Code Trade Restrictions', 'Check if HS codes have trade restrictions', 'TRADE', 'HIGH'),
('DUAL_USE_GOODS', 'Dual-Use Goods Check', 'Check for dual-use goods restrictions', 'TRADE', 'CRITICAL'),
('EMBARGO_COUNTRY', 'Embargo Country Check', 'Check for embargoed countries', 'SANCTIONS', 'CRITICAL'),
('REQUIRED_FIELDS', 'Required Fields Validation', 'Ensure all required fields are present', 'DOCUMENT', 'MEDIUM'),
('DATE_CONSISTENCY', 'Date Consistency Check', 'Validate date consistency across document', 'DOCUMENT', 'LOW'),
('AMOUNT_THRESHOLD', 'Transaction Amount Threshold', 'Check if amounts exceed reporting thresholds', 'FINANCIAL', 'HIGH'),
('CURRENCY_VALIDATION', 'Currency Code Validation', 'Validate ISO currency codes', 'FINANCIAL', 'MEDIUM')
ON CONFLICT (id) DO NOTHING;

-- Create function to update document compliance status
CREATE OR REPLACE FUNCTION update_document_compliance_status()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO document_compliance_status (
        document_id, 
        last_compliance_check, 
        overall_status, 
        critical_issues, 
        high_issues, 
        medium_issues, 
        low_issues, 
        last_report_id
    ) VALUES (
        NEW.document_id,
        NEW.generated_at,
        NEW.overall_status,
        NEW.critical_issues,
        NEW.high_issues,
        NEW.medium_issues,
        NEW.low_issues,
        NEW.id
    )
    ON CONFLICT (document_id) 
    DO UPDATE SET
        last_compliance_check = NEW.generated_at,
        overall_status = NEW.overall_status,
        critical_issues = NEW.critical_issues,
        high_issues = NEW.high_issues,
        medium_issues = NEW.medium_issues,
        low_issues = NEW.low_issues,
        last_report_id = NEW.id,
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for compliance status updates
DROP TRIGGER IF EXISTS trigger_update_compliance_status ON compliance_reports;
CREATE TRIGGER trigger_update_compliance_status
    AFTER INSERT ON compliance_reports
    FOR EACH ROW
    EXECUTE FUNCTION update_document_compliance_status();

-- Create function to create compliance alerts for critical issues
CREATE OR REPLACE FUNCTION create_compliance_alerts()
RETURNS TRIGGER AS $$
BEGIN
    -- Create alerts for critical and high severity issues
    IF NEW.overall_status IN ('NON_COMPLIANT', 'WARNING') THEN
        INSERT INTO compliance_alerts (document_id, alert_type, severity, title, message, details)
        SELECT 
            NEW.document_id,
            'COMPLIANCE_VIOLATION',
            CASE 
                WHEN NEW.critical_issues > 0 THEN 'CRITICAL'
                WHEN NEW.high_issues > 0 THEN 'HIGH'
                ELSE 'MEDIUM'
            END,
            'Compliance Issues Detected',
            format('Document %s has compliance issues: %s critical, %s high, %s medium', 
                    NEW.document_number, NEW.critical_issues, NEW.high_issues, NEW.medium_issues),
            json_build_object(
                'report_id', NEW.id,
                'critical_issues', NEW.critical_issues,
                'high_issues', NEW.high_issues,
                'medium_issues', NEW.medium_issues
            );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for compliance alerts
DROP TRIGGER IF EXISTS trigger_create_compliance_alerts ON compliance_reports;
CREATE TRIGGER trigger_create_compliance_alerts
    AFTER INSERT ON compliance_reports
    FOR EACH ROW
    EXECUTE FUNCTION create_compliance_alerts();

-- Create view for compliance dashboard
CREATE OR REPLACE VIEW compliance_dashboard AS
SELECT 
    dr.document_id,
    d.document_number,
    d.customer_id,
    c.name as customer_name,
    dr.overall_status,
    dr.critical_issues,
    dr.high_issues,
    dr.medium_issues,
    dr.low_issues,
    dr.last_compliance_check,
    COUNT(ca.id) as open_alerts,
    MAX(ca.severity) as highest_alert_severity
FROM document_compliance_status dr
JOIN documents d ON dr.document_id = d.id
JOIN customers c ON d.customer_id = c.id
LEFT JOIN compliance_alerts ca ON dr.document_id = ca.document_id AND ca.status = 'OPEN'
GROUP BY dr.document_id, d.document_number, d.customer_id, c.name, 
         dr.overall_status, dr.critical_issues, dr.high_issues, 
         dr.medium_issues, dr.low_issues, dr.last_compliance_check
ORDER BY 
    CASE 
        WHEN dr.overall_status = 'NON_COMPLIANT' THEN 1
        WHEN dr.overall_status = 'WARNING' THEN 2
        WHEN dr.overall_status = 'PENDING_REVIEW' THEN 3
        ELSE 4
    END,
    dr.critical_issues DESC, dr.high_issues DESC;

-- Create view for compliance statistics
CREATE OR REPLACE VIEW compliance_statistics AS
SELECT 
    COUNT(*) as total_documents,
    COUNT(CASE WHEN overall_status = 'COMPLIANT' THEN 1 END) as compliant_documents,
    COUNT(CASE WHEN overall_status = 'NON_COMPLIANT' THEN 1 END) as non_compliant_documents,
    COUNT(CASE WHEN overall_status = 'WARNING' THEN 1 END) as warning_documents,
    COUNT(CASE WHEN overall_status = 'PENDING_REVIEW' THEN 1 END) as pending_documents,
    ROUND(
        COUNT(CASE WHEN overall_status = 'COMPLIANT' THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        2
    ) as compliance_percentage,
    SUM(critical_issues) as total_critical_issues,
    SUM(high_issues) as total_high_issues,
    SUM(medium_issues) as total_medium_issues,
    SUM(low_issues) as total_low_issues
FROM document_compliance_status;

-- Grant permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON compliance_rules TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON compliance_reports TO your_app_user;
-- GRANT SELECT, INSERT, UPDATE ON compliance_results TO your_app_user;
-- GRANT SELECT ON compliance_dashboard TO your_app_user;
-- GRANT SELECT ON compliance_statistics TO your_app_user;
