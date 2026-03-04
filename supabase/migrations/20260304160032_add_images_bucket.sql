INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'images',
    'images',
    false,
    10485760,  -- 10 MB in bytes (matching API upload_max_size_bytes)
    ARRAY['image/jpeg', 'image/png', 'image/webp']
)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Service role can upload images"
ON storage.objects
FOR INSERT
TO service_role
WITH CHECK (bucket_id = 'images');

CREATE POLICY "Anonymous users can read images"
ON storage.objects
FOR SELECT
TO anon
USING (bucket_id = 'images');

CREATE POLICY "Service role has full access to images"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'images');
