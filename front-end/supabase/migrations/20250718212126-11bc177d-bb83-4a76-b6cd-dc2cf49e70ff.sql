
-- 1. Primeiro, remover todas as políticas RLS que dependem da função is_admin atual
DROP POLICY IF EXISTS "Admins can view pending text reports" ON public.pending_text_reports;
DROP POLICY IF EXISTS "Admins can update pending text reports" ON public.pending_text_reports;
DROP POLICY IF EXISTS "Admins can delete pending text reports" ON public.pending_text_reports;
DROP POLICY IF EXISTS "Admins can view pending image reports" ON public.pending_image_reports;
DROP POLICY IF EXISTS "Admins can update pending image reports" ON public.pending_image_reports;
DROP POLICY IF EXISTS "Admins can delete pending image reports" ON public.pending_image_reports;
DROP POLICY IF EXISTS "Admins can insert approved text reports" ON public.approved_text_reports;
DROP POLICY IF EXISTS "Admins can view approved text reports" ON public.approved_text_reports;
DROP POLICY IF EXISTS "Admins can insert approved image reports" ON public.approved_image_reports;
DROP POLICY IF EXISTS "Admins can view approved image reports" ON public.approved_image_reports;
DROP POLICY IF EXISTS "Admins can view images" ON storage.objects;

-- 2. Remover a função is_admin(text) atual que causa recursão infinita
DROP FUNCTION IF EXISTS public.is_admin(text);

-- 3. Criar nova função is_admin() sem parâmetros que usa auth.jwt() diretamente
CREATE OR REPLACE FUNCTION public.is_admin()
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT COALESCE((auth.jwt() ->> 'email'), '') = 'admin@scamwatchbrasil.com';
$$;

-- 4. Recriar todas as políticas RLS usando a nova função is_admin()

-- Políticas para pending_text_reports
CREATE POLICY "Admins can view pending text reports" 
ON public.pending_text_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin());

CREATE POLICY "Admins can update pending text reports" 
ON public.pending_text_reports 
FOR UPDATE 
TO authenticated 
USING (public.is_admin());

CREATE POLICY "Admins can delete pending text reports" 
ON public.pending_text_reports 
FOR DELETE 
TO authenticated 
USING (public.is_admin());

-- Políticas para pending_image_reports
CREATE POLICY "Admins can view pending image reports" 
ON public.pending_image_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin());

CREATE POLICY "Admins can update pending image reports" 
ON public.pending_image_reports 
FOR UPDATE 
TO authenticated 
USING (public.is_admin());

CREATE POLICY "Admins can delete pending image reports" 
ON public.pending_image_reports 
FOR DELETE 
TO authenticated 
USING (public.is_admin());

-- Políticas para approved_text_reports
CREATE POLICY "Admins can insert approved text reports" 
ON public.approved_text_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (public.is_admin());

CREATE POLICY "Admins can view approved text reports" 
ON public.approved_text_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin());

-- Políticas para approved_image_reports
CREATE POLICY "Admins can insert approved image reports" 
ON public.approved_image_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (public.is_admin());

CREATE POLICY "Admins can view approved image reports" 
ON public.approved_image_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin());

-- Política para storage
CREATE POLICY "Admins can view images" 
ON storage.objects 
FOR SELECT 
TO authenticated
USING (bucket_id = 'scam-images' AND public.is_admin());
