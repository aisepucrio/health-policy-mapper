
-- Renomear as tabelas existentes
ALTER TABLE approved_text_reports RENAME TO approved_scam_text;
ALTER TABLE approved_image_reports RENAME TO approved_scam_images;

-- Criar novas tabelas para ham
CREATE TABLE public.approved_ham_text (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  message TEXT NOT NULL,
  approved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  original_id UUID
);

CREATE TABLE public.approved_ham_images (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  image_url TEXT NOT NULL,
  file_name TEXT NOT NULL,
  file_size INTEGER,
  mime_type TEXT,
  approved_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
  original_id UUID
);

-- Habilitar RLS nas novas tabelas
ALTER TABLE public.approved_ham_text ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.approved_ham_images ENABLE ROW LEVEL SECURITY;

-- Criar políticas para as novas tabelas ham
CREATE POLICY "Admins can view approved ham text" 
  ON public.approved_ham_text 
  FOR SELECT 
  USING (is_admin());

CREATE POLICY "Admins can insert approved ham text" 
  ON public.approved_ham_text 
  FOR INSERT 
  WITH CHECK (is_admin());

CREATE POLICY "Admins can view approved ham images" 
  ON public.approved_ham_images 
  FOR SELECT 
  USING (is_admin());

CREATE POLICY "Admins can insert approved ham images" 
  ON public.approved_ham_images 
  FOR INSERT 
  WITH CHECK (is_admin());
