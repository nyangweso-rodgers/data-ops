SELECT EXISTS (
    SELECT FROM information_schema.tables 
    WHERE table_schema = %s 
    AND table_name = %s
);
