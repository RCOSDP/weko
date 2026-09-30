
-- Add unique constraint
ALTER TABLE item_type_mapping
ADD CONSTRAINT uq_item_type_mapping_item_type_id UNIQUE (item_type_id);

-- Add foreign key constraint
ALTER TABLE item_type_mapping
ADD CONSTRAINT fk_item_type_mapping_item_type_id_item_type
FOREIGN KEY (item_type_id) REFERENCES item_type(id) ON DELETE CASCADE;

-- Drop indexes
DROP INDEX IF EXISTS idx_created_item_type_mapping;
DROP INDEX IF EXISTS idx_item_type_id_item_type_mapping;
