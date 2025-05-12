-- Seed initial data for Rella Analytics DB

-- Locations
INSERT INTO locations (name, address) VALUES
('Rella Aesthetics - Napa', NULL),
('Rella Aesthetics', NULL);

-- Treatment Categories (from BOULEVARD_CATEGORY_MAPPING)
INSERT INTO treatment_categories (name, description) VALUES
('Injectables', 'Injectable treatments including Botox, Dysport, and dermal fillers'),
('Facials', 'Various facial treatments including HydraFacial and microdermabrasion'),
('Laser', 'Laser treatments including hair removal and skin resurfacing'),
('Retail/Skincare', 'Retail skincare products and memberships'),
('Wellness/Weight Loss', 'Weight loss treatments and wellness services'),
('IV Therapy', 'Various IV therapy treatments'),
('Other Services', 'Additional services including PRP and RF Microneedling'),
('Consultation/Followup', 'Initial consultations and follow-up appointments'),
('Membership/Account Adjustment', 'Membership fees and account adjustments'),
('Uncategorized', 'Items not yet categorized'); 