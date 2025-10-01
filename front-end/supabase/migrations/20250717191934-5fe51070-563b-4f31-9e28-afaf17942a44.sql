-- Create enum for report status
CREATE TYPE public.report_status AS ENUM ('pending', 'approved', 'rejected');

-- Create pending text reports table
CREATE TABLE public.pending_text_reports (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    status report_status NOT NULL DEFAULT 'pending'
);

-- Create approved text reports table
CREATE TABLE public.approved_text_reports (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    approved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    original_id UUID -- Reference to original pending report
);

-- Create pending image reports table
CREATE TABLE public.pending_image_reports (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    image_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    status report_status NOT NULL DEFAULT 'pending'
);

-- Create approved image reports table
CREATE TABLE public.approved_image_reports (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    image_url TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    approved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    original_id UUID -- Reference to original pending report
);

-- Create admin users table
CREATE TABLE public.admin_users (
    id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Enable RLS on all tables
ALTER TABLE public.pending_text_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approved_text_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pending_image_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approved_image_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admin_users ENABLE ROW LEVEL SECURITY;

-- Create policies for public access to submit reports
CREATE POLICY "Anyone can insert pending text reports" 
ON public.pending_text_reports 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Anyone can insert pending image reports" 
ON public.pending_image_reports 
FOR INSERT 
WITH CHECK (true);

-- Create policies for admin access
CREATE POLICY "Authenticated users can view pending text reports" 
ON public.pending_text_reports 
FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can update pending text reports" 
ON public.pending_text_reports 
FOR UPDATE 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can delete pending text reports" 
ON public.pending_text_reports 
FOR DELETE 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can view pending image reports" 
ON public.pending_image_reports 
FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can update pending image reports" 
ON public.pending_image_reports 
FOR UPDATE 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can delete pending image reports" 
ON public.pending_image_reports 
FOR DELETE 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can insert approved text reports" 
ON public.approved_text_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (true);

CREATE POLICY "Authenticated users can view approved text reports" 
ON public.approved_text_reports 
FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can insert approved image reports" 
ON public.approved_image_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (true);

CREATE POLICY "Authenticated users can view approved image reports" 
ON public.approved_image_reports 
FOR SELECT 
TO authenticated 
USING (true);

CREATE POLICY "Authenticated users can view admin users" 
ON public.admin_users 
FOR SELECT 
TO authenticated 
USING (true);

-- Create storage bucket for scam images
INSERT INTO storage.buckets (id, name, public) 
VALUES ('scam-images', 'scam-images', false);

-- Create storage policies
CREATE POLICY "Anyone can upload images" 
ON storage.objects 
FOR INSERT 
WITH CHECK (bucket_id = 'scam-images');

CREATE POLICY "Authenticated users can view images" 
ON storage.objects 
FOR SELECT 
TO authenticated
USING (bucket_id = 'scam-images');

-- Insert default admin user (password should be hashed in production)
-- For now, using a simple approach - in production this should be properly hashed
INSERT INTO public.admin_users (email, password_hash) 
VALUES ('admin@scamwatchbrasil.com', crypt('admin123', gen_salt('bf')));

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for admin users table
CREATE TRIGGER update_admin_users_updated_at
    BEFORE UPDATE ON public.admin_users
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();