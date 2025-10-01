
import React, { useState, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText, Image as ImageIcon, Send, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { TextInput } from './TextInput';
import { FileUpload } from './FileUpload';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { supabase } from '@/integrations/supabase/client';

type ReportType = 'text' | 'image';
type SubmissionState = 'idle' | 'loading' | 'success' | 'error';

export const ScamReportForm: React.FC = () => {
  const [reportType, setReportType] = useState<ReportType>('text');
  const [textMessage, setTextMessage] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [submissionState, setSubmissionState] = useState<SubmissionState>('idle');
  const { toast } = useToast();

  const isValidImageFile = (file: File): boolean => {
    const validTypes = ['image/jpeg', 'image/jpg', 'image/png'];
    return validTypes.includes(file.type);
  };

  const isFormValid = useCallback(() => {
    if (reportType === 'text') {
      return textMessage.trim().length > 0;
    }
    return selectedFiles.length > 0 && selectedFiles.every(file => isValidImageFile(file));
  }, [reportType, textMessage, selectedFiles]);

  const resetForm = useCallback(() => {
    setTextMessage('');
    setSelectedFiles([]);
    setSubmissionState('idle');
  }, []);

  const submitTextMessage = async (message: string) => {
    const { error } = await supabase
      .from('pending_text_reports')
      .insert([{ message: message.trim() }]);

    if (error) {
      throw new Error(error.message);
    }
  };

  const submitImages = async (files: File[]) => {
    const invalidFiles = files.filter(file => !isValidImageFile(file));
    if (invalidFiles.length > 0) {
      throw new Error('Alguns arquivos têm formato inválido. Use apenas JPG, JPEG ou PNG.');
    }

    const uploadedImages = [];

    // Upload each file
    for (const [index, file] of files.entries()) {
      const fileExt = file.name.split('.').pop();
      const fileName = `${Math.random()}.${fileExt}`;
      const filePath = `${fileName}`;

      const { error: uploadError } = await supabase.storage
        .from('scam-images')
        .upload(filePath, file);

      if (uploadError) {
        throw new Error(`Erro ao fazer upload do arquivo ${index + 1}: ${uploadError.message}`);
      }

      // Get the public URL
      const { data: { publicUrl } } = supabase.storage
        .from('scam-images')
        .getPublicUrl(filePath);

      uploadedImages.push({
        image_url: publicUrl,
        file_name: file.name,
        file_size: file.size,
        mime_type: file.type
      });
    }

    // Save all images metadata to pending table
    const { error: dbError } = await supabase
      .from('pending_image_reports')
      .insert(uploadedImages);

    if (dbError) {
      throw new Error(dbError.message);
    }
  };

  const handleSubmit = async () => {
    if (!isFormValid()) return;

    setSubmissionState('loading');

    try {
      if (reportType === 'text') {
        await submitTextMessage(textMessage);
      } else {
        await submitImages(selectedFiles);
      }

      setSubmissionState('success');
      const fileCount = selectedFiles.length;
      toast({
        title: "Sucesso!",
        description: reportType === 'text' 
          ? "Seu relato foi enviado com sucesso. Nossa equipe irá analisar e aprovar o conteúdo em breve!"
          : `${fileCount} imagem${fileCount !== 1 ? 's foram enviadas' : ' foi enviada'} com sucesso. Nossa equipe irá analisar e aprovar o conteúdo em breve!`,
        className: "bg-success text-success-foreground"
      });

      setTimeout(() => {
        resetForm();
      }, 2000);

    } catch (error: any) {
      console.error('Erro ao enviar:', error);
      setSubmissionState('error');
      
      toast({
        title: "Erro no envio",
        description: error.message || "Ocorreu um erro ao enviar seu relato. Por favor, tente novamente mais tarde.",
        variant: "destructive"
      });

      setTimeout(() => {
        setSubmissionState('idle');
      }, 3000);
    }
  };

  const getSubmitButtonContent = () => {
    switch (submissionState) {
      case 'loading':
        return (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Enviando...
          </>
        );
      case 'success':
        return (
          <>
            <CheckCircle className="h-4 w-4" />
            Enviado com sucesso!
          </>
        );
      case 'error':
        return (
          <>
            <AlertCircle className="h-4 w-4" />
            Erro no envio
          </>
        );
      default:
        return (
          <>
            <Send className="h-4 w-4" />
            Reportar Golpe
          </>
        );
    }
  };

  const getSubmitButtonVariant = () => {
    switch (submissionState) {
      case 'success':
        return 'success';
      case 'error':
        return 'destructive';
      default:
        return 'hero';
    }
  };

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-elevation">
      <CardHeader className="text-center space-y-2">
        <CardTitle className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
          Reportar Golpe Digital
        </CardTitle>
        <CardDescription className="text-muted-foreground">
          Escolha como deseja reportar o golpe que você recebeu
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-6">
        <Tabs 
          value={reportType} 
          onValueChange={(value) => setReportType(value as ReportType)}
          className="w-full"
        >
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger 
              value="text" 
              className="flex items-center gap-2"
            >
              <FileText className="h-4 w-4" />
              Mensagem de Texto
            </TabsTrigger>
            <TabsTrigger 
              value="image" 
              className="flex items-center gap-2"
            >
              <ImageIcon className="h-4 w-4" />
              Prints de Tela
            </TabsTrigger>
          </TabsList>

          <TabsContent value="text" className="space-y-4 animate-fade-in">
            <TextInput
              value={textMessage}
              onChange={setTextMessage}
              disabled={submissionState === 'loading'}
            />
          </TabsContent>

          <TabsContent value="image" className="space-y-4 animate-fade-in">
            <FileUpload
              selectedFiles={selectedFiles}
              onFileSelect={setSelectedFiles}
              disabled={submissionState === 'loading'}
            />
          </TabsContent>
        </Tabs>

        <div className="pt-4">
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid() || submissionState === 'loading'}
            variant={getSubmitButtonVariant()}
            size="lg"
            className={cn(
              "w-full transition-all duration-200",
              submissionState === 'success' && "animate-pulse-glow"
            )}
          >
            {getSubmitButtonContent()}
          </Button>

          {submissionState === 'idle' && !isFormValid() && (
            <p className="text-sm text-muted-foreground text-center mt-2">
              {reportType === 'text' 
                ? 'Digite uma mensagem para continuar'
                : 'Selecione pelo menos uma imagem válida (JPG, JPEG, PNG) para continuar'
              }
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
