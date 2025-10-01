
-- Remove a tabela admin_users customizada
DROP TABLE IF EXISTS public.admin_users CASCADE;

-- Inserir o usuário admin diretamente na tabela auth.users do Supabase
-- Isso será feito através da interface do Supabase ou via signUp programaticamente
-- A tabela auth.users é gerenciada pelo Supabase e não pode ser modificada diretamente via SQL

-- Como alternativa, vamos criar uma função para identificar admins baseado no email
CREATE OR REPLACE FUNCTION public.is_admin(user_email text)
RETURNS boolean
LANGUAGE sql
STABLE
SECURITY DEFINER
AS $$
  SELECT user_email = 'admin@scamwatchbrasil.com';
$$;

-- Atualizar as políticas RLS para usar a função is_admin com base no email do usuário autenticado
-- Política para pending_text_reports (admins podem ver, atualizar e deletar)
DROP POLICY IF EXISTS "Authenticated users can view pending text reports" ON public.pending_text_reports;
DROP POLICY IF EXISTS "Authenticated users can update pending text reports" ON public.pending_text_reports;
DROP POLICY IF EXISTS "Authenticated users can delete pending text reports" ON public.pending_text_reports;

CREATE POLICY "Admins can view pending text reports" 
ON public.pending_text_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can update pending text reports" 
ON public.pending_text_reports 
FOR UPDATE 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can delete pending text reports" 
ON public.pending_text_reports 
FOR DELETE 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

-- Política para pending_image_reports (admins podem ver, atualizar e deletar)
DROP POLICY IF EXISTS "Authenticated users can view pending image reports" ON public.pending_image_reports;
DROP POLICY IF EXISTS "Authenticated users can update pending image reports" ON public.pending_image_reports;
DROP POLICY IF EXISTS "Authenticated users can delete pending image reports" ON public.pending_image_reports;

CREATE POLICY "Admins can view pending image reports" 
ON public.pending_image_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can update pending image reports" 
ON public.pending_image_reports 
FOR UPDATE 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can delete pending image reports" 
ON public.pending_image_reports 
FOR DELETE 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

-- Política para approved_text_reports (admins podem inserir e ver)
DROP POLICY IF EXISTS "Authenticated users can insert approved text reports" ON public.approved_text_reports;
DROP POLICY IF EXISTS "Authenticated users can view approved text reports" ON public.approved_text_reports;

CREATE POLICY "Admins can insert approved text reports" 
ON public.approved_text_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can view approved text reports" 
ON public.approved_text_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

-- Política para approved_image_reports (admins podem inserir e ver)
DROP POLICY IF EXISTS "Authenticated users can insert approved image reports" ON public.approved_image_reports;
DROP POLICY IF EXISTS "Authenticated users can view approved image reports" ON public.approved_image_reports;

CREATE POLICY "Admins can insert approved image reports" 
ON public.approved_image_reports 
FOR INSERT 
TO authenticated 
WITH CHECK (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

CREATE POLICY "Admins can view approved image reports" 
ON public.approved_image_reports 
FOR SELECT 
TO authenticated 
USING (public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));

-- Política para storage (admins podem ver imagens)
DROP POLICY IF EXISTS "Authenticated users can view images" ON storage.objects;

CREATE POLICY "Admins can view images" 
ON storage.objects 
FOR SELECT 
TO authenticated
USING (bucket_id = 'scam-images' AND public.is_admin((SELECT email FROM auth.users WHERE id = auth.uid())));
