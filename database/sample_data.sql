-- Sample data for testing the knowledge graph system

-- Insert sample customers
INSERT INTO customers (name, email) VALUES 
('Global Logistics Inc', 'contact@globallogistics.com'),
('TradeForward Solutions', 'info@tradeforward.com'),
('ShipRight International', 'ops@shipright.com');

-- Insert field definitions for logistics documents
INSERT INTO field_definitions (name, description, field_type, target_graph_label) VALUES 
('ShipperName', 'Name of the company sending the goods', 'text', 'LegalEntity'),
('ConsigneeName', 'Name of the company receiving the goods', 'text', 'LegalEntity'),
('HS_Code', 'Harmonized System code for product classification', 'code', 'HSCode'),
('Product', 'Description of the product being traded', 'text', 'Product'),
('Quantity', 'Quantity of goods', 'number', NULL),
('UnitPrice', 'Price per unit', 'number', NULL),
('TotalValue', 'Total value of shipment', 'number', NULL),
('OriginPort', 'Port of origin', 'text', 'Location'),
('DestinationPort', 'Port of destination', 'text', 'Location'),
('InvoiceNumber', 'Invoice reference number', 'text', NULL),
('BillOfLadingNumber', 'Bill of lading reference', 'text', NULL);

-- Insert sample documents
INSERT INTO documents (customer_id, document_type, document_number, file_path) VALUES 
(1, 'invoice', 'INV-2024-001', '/documents/invoices/inv-2024-001.pdf'),
(1, 'bill_of_lading', 'BOL-2024-045', '/documents/bol/bol-2024-045.pdf'),
(2, 'invoice', 'INV-2024-089', '/documents/invoices/inv-2024-089.pdf'),
(3, 'packing_list', 'PL-2024-012', '/documents/packing/pl-2024-012.pdf'),
(2, 'invoice', 'INV-2024-090', '/documents/invoices/inv-2024-090.pdf');

-- Insert sample document fields with OCR and processed values
INSERT INTO document_fields (document_id, field_definition_id, raw_value, normalized_value, hitl_value, confidence_score) VALUES 
-- Document 1 (INV-2024-001)
(1, 1, 'GLOBAL LOGISTICS INC.', 'Global Logistics Inc', NULL, 0.95),
(1, 2, 'ABC TRADING CO LTD', 'ABC Trading Co Ltd', NULL, 0.88),
(1, 3, '8703.23.0000', '8703.23.0000', NULL, 0.92),
(1, 4, 'Automobile parts - Engine components', 'Automobile parts - Engine components', NULL, 0.85),
(1, 5, '150', '150', NULL, 0.98),
(1, 6, '$25.50', '25.50', NULL, 0.91),
(1, 7, '$3,825.00', '3825.00', NULL, 0.89),

-- Document 2 (BOL-2024-045)
(2, 1, 'GLOBAL LOGISTICS INC.', 'Global Logistics Inc', NULL, 0.94),
(2, 2, 'XYZ IMPORT EXPORT', 'XYZ Import Export', 'XYZ Import & Export GmbH', 0.87),
(2, 8, 'Shanghai Port', 'Shanghai Port', 'Shanghai, China', 0.91),
(2, 9, 'Los Angeles Port', 'Los Angeles Port', 'Los Angeles, USA', 0.93),
(2, 10, 'BOL20240045', 'BOL20240045', NULL, 0.97),

-- Document 3 (INV-2024-089)
(3, 1, 'TRADEFORWARD SOLUTIONS', 'TradeForward Solutions', NULL, 0.96),
(3, 2, 'EURO DISTRIBUTORS SA', 'Euro Distributors SA', NULL, 0.89),
(3, 3, '6403.12.9000', '6403.12.9000', NULL, 0.93),
(3, 4, 'Leather shoes - Mens formal', 'Leather shoes - Mens formal', NULL, 0.86),
(3, 5, '200', '200', NULL, 0.99),
(3, 6, '€45.00', '45.00', NULL, 0.92),
(3, 7, '€9,000.00', '9000.00', NULL, 0.90),

-- Document 4 (PL-2024-012)
(4, 1, 'SHIPRIGHT INTERNATIONAL', 'ShipRight International', NULL, 0.95),
(4, 2, 'ASIA PACIFIC TRADING', 'Asia Pacific Trading', NULL, 0.88),
(4, 3, '8517.12.0000', '8517.12.0000', NULL, 0.91),
(4, 4, 'Smartphone accessories - Charging cables', 'Smartphone accessories - Charging cables', NULL, 0.84),
(4, 5, '500', '500', NULL, 0.97),

-- Document 5 (INV-2024-090)
(5, 1, 'TRADEFORWARD SOLUTIONS', 'TradeForward Solutions', NULL, 0.94),
(5, 2, 'GLOBAL RETAIL CHAIN', 'Global Retail Chain', NULL, 0.90),
(5, 3, '2204.21.0000', '2204.21.0000', NULL, 0.93),
(5, 4, 'Wine - Red wine bottled', 'Wine - Red wine bottled', NULL, 0.87),
(5, 5, '100', '100', NULL, 0.98),
(5, 6, '$12.50', '12.50', NULL, 0.91),
(5, 7, '$1,250.00', '1250.00', NULL, 0.89);
