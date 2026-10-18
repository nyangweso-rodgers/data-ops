-- Update the assignment_start for a specific batch_id in the collection_officer_assignments table
UPDATE test.collection_officer_assignments
SET assignment_start = '2026-09-01 00:00:00'
WHERE batch_id = 'dd6f4020-0b67-4ee6-8d3b-9e0feb663575';

-- update assignment_end for the same batch_id to ensure the assignment period is correctly set
UPDATE test.collection_officer_assignments
SET assignment_end = '2026-09-30 23:59:59'
WHERE batch_id = 'dd6f4020-0b67-4ee6-8d3b-9e0feb663575';