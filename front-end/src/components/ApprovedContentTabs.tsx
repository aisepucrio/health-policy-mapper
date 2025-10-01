import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Download, FileText, Image as ImageIcon, Loader2, Eye, AlertTriangle, Shield } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface ApprovedTextReport {
  id: string;
  message: string;
  approved_at: string;
  original_id: string;
  spam: number;
  scam: number;
}

interface ApprovedImageReport {
  id: string;
  image_url: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  approved_at: string;
  original_id: string;
  spam: number;
  scam: number;
}

const ImageWithFallback: React.FC<{ 
  imageUrl: string; 
  fileName: string; 
  className?: string; 
}> = ({ imageUrl, fileName, className }) => {
  const [src, setSrc] = useState<string>('/placeholder.svg');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadImage = async () => {
      setIsLoading(true);
      try {
        if (imageUrl.startsWith('http')) {
          setSrc(imageUrl);
          setIsLoading(false);
          return;
        }
        
        const { data } = supabase.storage
          .from('scam-images')
          .getPublicUrl(imageUrl);
        
        if (!data.publicUrl) {
          const { data: downloadData, error } = await supabase.storage
            .from('scam-images')
            .download(imageUrl);
          
          if (error) {
            console.error('Erro ao fazer download:', error);
            throw error;
          }
          
          if (downloadData) {
            setSrc(URL.createObjectURL(downloadData));
            setIsLoading(false);
            return;
          }
        }
        
        setSrc(data.publicUrl);
      } catch (error) {
        console.error('Erro ao carregar imagem:', error);
        setSrc('/placeholder.svg');
      } finally {
        setIsLoading(false);
      }
    };

    loadImage();
  }, [imageUrl]);

  if (isLoading) {
    return (
      <div className={`${className} flex items-center justify-center bg-gray-100 rounded`}>
        <Loader2 className="h-4 w-4 animate-spin" />
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={fileName}
      className={className}
      onError={() => {
        console.error('Erro ao exibir imagem:', imageUrl);
        setSrc('/placeholder.svg');
      }}
    />
  );
};

export const ApprovedContentTabs: React.FC = () => {
  const [approvedTextReports, setApprovedTextReports] = useState<ApprovedTextReport[]>([]);
  const [approvedImageReports, setApprovedImageReports] = useState<ApprovedImageReport[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchApprovedContent();
  }, []);

  const fetchApprovedContent = async () => {
    setLoading(true);
    
    try {
      // Use direct queries with type casting to bypass TypeScript restrictions
      const textQuery = supabase
        .from('approved_texts' as any)
        .select('*')
        .order('approved_at', { ascending: false });
      
      const imageQuery = supabase
        .from('approved_images' as any)
        .select('*')
        .order('approved_at', { ascending: false });

      const [textResponse, imageResponse] = await Promise.all([
        textQuery,
        imageQuery
      ]);

      if (textResponse.error) {
        console.error('Error fetching approved texts:', textResponse.error);
      } else {
        // Only set state if we have valid data and it's an array without errors
        if (textResponse.data && Array.isArray(textResponse.data) && 
            textResponse.data.length > 0 && 
            !textResponse.data.some((item: any) => item.error || typeof item === 'string')) {
          setApprovedTextReports(textResponse.data as unknown as ApprovedTextReport[]);
        } else if (textResponse.data && Array.isArray(textResponse.data) && textResponse.data.length === 0) {
          setApprovedTextReports([]);
        }
      }

      if (imageResponse.error) {
        console.error('Error fetching approved images:', imageResponse.error);
      } else {
        // Only set state if we have valid data and it's an array without errors
        if (imageResponse.data && Array.isArray(imageResponse.data) && 
            imageResponse.data.length > 0 && 
            !imageResponse.data.some((item: any) => item.error || typeof item === 'string')) {
          setApprovedImageReports(imageResponse.data as unknown as ApprovedImageReport[]);
        } else if (imageResponse.data && Array.isArray(imageResponse.data) && imageResponse.data.length === 0) {
          setApprovedImageReports([]);
        }
      }

      // Show error only if both queries fail
      if (textResponse.error && imageResponse.error) {
        throw new Error('Failed to load approved content');
      }

    } catch (error: any) {
      toast({
        title: "Erro ao carregar conteúdo aprovado",
        description: "Verifique se as tabelas approved_texts e approved_images existem no banco de dados",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const convertImageToBase64 = async (imageUrl: string): Promise<string> => {
    try {
      if (imageUrl.startsWith('http')) {
        const response = await fetch(imageUrl);
        const blob = await response.blob();
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(blob);
        });
      }
      
      const { data: downloadData, error } = await supabase.storage
        .from('scam-images')
        .download(imageUrl);
      
      if (error) throw error;
      
      if (downloadData) {
        return new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(downloadData);
        });
      }
      
      return '';
    } catch (error) {
      console.error('Erro ao converter imagem para base64:', error);
      return '';
    }
  };

  const downloadCSV = (data: any[], filename: string, headers: string[]) => {
    const csvContent = [
      headers,
      ...data.map(item => headers.map(header => {
        const key = header.toLowerCase().replace(/\s+/g, '_')
          .replace(/[áàãâä]/g, 'a').replace(/[éèêë]/g, 'e')
          .replace(/[íìîï]/g, 'i').replace(/[óòõôö]/g, 'o')
          .replace(/[úùûü]/g, 'u').replace(/[ç]/g, 'c');
        const value = item[key] || '';
        return typeof value === 'string' ? `"${value.replace(/"/g, '""')}"` : value;
      }))
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    if (link.download !== undefined) {
      const url = URL.createObjectURL(blob);
      link.setAttribute('href', url);
      link.setAttribute('download', filename);
      link.style.visibility = 'hidden';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const downloadTextCSV = () => {
    const dataForExport = approvedTextReports.map(r => ({
      id: r.id,
      mensagem: r.message,
      spam: r.spam,
      scam: r.scam,
      data_de_aprovacao: formatDate(r.approved_at),
      id_original: r.original_id
    }));

    downloadCSV(
      dataForExport,
      'textos-aprovados.csv',
      ['ID', 'Mensagem', 'Spam', 'Scam', 'Data de Aprovação', 'ID Original']
    );
  };

  const downloadImageCSVWithBase64 = async () => {
    toast({
      title: "Processando imagens",
      description: "Convertendo imagens para base64. Isso pode demorar alguns instantes...",
    });

    const dataWithBase64 = await Promise.all(
      approvedImageReports.map(async (report) => ({
        id: report.id,
        nome_do_arquivo: report.file_name,
        url_da_imagem: report.image_url,
        tamanho: formatFileSize(report.file_size || 0),
        tipo_mime: report.mime_type || 'Não especificado',
        spam: report.spam,
        scam: report.scam,
        data_de_aprovacao: formatDate(report.approved_at),
        id_original: report.original_id,
        imagem_base64: await convertImageToBase64(report.image_url)
      }))
    );

    downloadCSV(
      dataWithBase64,
      'imagens-aprovadas.csv',
      ['ID', 'Nome do Arquivo', 'URL da Imagem', 'Tamanho', 'Tipo MIME', 'Spam', 'Scam', 'Data de Aprovação', 'ID Original', 'Imagem Base64']
    );

    toast({
      title: "Download concluído",
      description: "CSV com imagens foi baixado com sucesso!",
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('pt-BR');
  };

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getClassificationBadge = (spam: number, scam: number) => {
    const badges = [];
    
    if (spam === 1) {
      badges.push(
        <Badge key="spam" variant="outline" className="text-orange-600 border-orange-600 mr-1">
          Spam
        </Badge>
      );
    }
    
    if (scam === 1) {
      badges.push(
        <Badge key="scam" variant="outline" className="text-red-600 border-red-600 mr-1">
          <AlertTriangle className="h-3 w-3 mr-1" />
          Scam
        </Badge>
      );
    }

    if (spam === 0 && scam === 0) {
      badges.push(
        <Badge key="ham" variant="outline" className="text-green-600 border-green-600 mr-1">
          <Shield className="h-3 w-3 mr-1" />
          Legítimo
        </Badge>
      );
    }

    return badges.length > 0 ? badges : (
      <Badge variant="outline" className="text-gray-600 border-gray-600">
        Sem classificação
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <Tabs defaultValue="text" className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="text" className="flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Textos ({approvedTextReports.length})
        </TabsTrigger>
        <TabsTrigger value="image" className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          Imagens ({approvedImageReports.length})
        </TabsTrigger>
      </TabsList>

      <TabsContent value="text">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-500" />
                  Textos Aprovados
                </CardTitle>
                <CardDescription>
                  Mensagens classificadas pelos administradores.
                </CardDescription>
              </div>
              <Button onClick={downloadTextCSV} variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Baixar CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {approvedTextReports.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Nenhum texto aprovado.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Ações</TableHead>
                    <TableHead>Mensagem</TableHead>
                    <TableHead>Classificação</TableHead>
                    <TableHead>Data de Aprovação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {approvedTextReports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <Eye className="h-4 w-4 mr-2" />
                              Ampliar
                            </Button>
                          </DialogTrigger>
                          <DialogContent className="max-w-2xl">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2">
                                Texto Aprovado
                              </DialogTitle>
                            </DialogHeader>
                            <div className="mt-4">
                              <div className="bg-muted p-4 rounded-lg">
                                <p className="whitespace-pre-wrap">{report.message}</p>
                              </div>
                              <div className="mt-4 space-y-2">
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-medium">Classificação:</span>
                                  {getClassificationBadge(report.spam, report.scam)}
                                </div>
                                <div className="text-sm text-muted-foreground">
                                  <p>Aprovado em: {formatDate(report.approved_at)}</p>
                                </div>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                      <TableCell className="max-w-md">
                        <div 
                          className="truncate cursor-pointer hover:bg-muted p-2 rounded transition-colors" 
                          title="Clique para ver mensagem completa"
                        >
                          <Dialog>
                            <DialogTrigger asChild>
                              <span>{report.message}</span>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl">
                              <DialogHeader>
                                <DialogTitle>Mensagem Completa</DialogTitle>
                              </DialogHeader>
                              <div className="mt-4">
                                <div className="bg-muted p-4 rounded-lg">
                                  <p className="whitespace-pre-wrap">{report.message}</p>
                                </div>
                                <div className="mt-4 space-y-2">
                                  <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium">Classificação:</span>
                                    {getClassificationBadge(report.spam, report.scam)}
                                  </div>
                                  <div className="text-sm text-muted-foreground">
                                    <p>Aprovado em: {formatDate(report.approved_at)}</p>
                                  </div>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </TableCell>
                      <TableCell>
                        {getClassificationBadge(report.spam, report.scam)}
                      </TableCell>
                      <TableCell>{formatDate(report.approved_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="image">
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <ImageIcon className="h-5 w-5 text-blue-500" />
                  Imagens Aprovadas
                </CardTitle>
                <CardDescription>
                  Imagens classificadas pelos administradores.
                </CardDescription>
              </div>
              <Button onClick={downloadImageCSVWithBase64} variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Baixar CSV
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {approvedImageReports.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Nenhuma imagem aprovada.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Preview</TableHead>
                    <TableHead>Nome do Arquivo</TableHead>
                    <TableHead>Classificação</TableHead>
                    <TableHead>Tamanho</TableHead>
                    <TableHead>Data de Aprovação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {approvedImageReports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell>
                        <Dialog>
                          <DialogTrigger asChild>
                            <div className="relative group cursor-pointer">
                              <ImageWithFallback
                                imageUrl={report.image_url}
                                fileName={report.file_name}
                                className="w-16 h-16 object-cover rounded border"
                              />
                              <div className="absolute inset-0 bg-black bg-opacity-50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center rounded">
                                <Eye className="h-6 w-6 text-white" />
                              </div>
                            </div>
                          </DialogTrigger>
                          <DialogContent className="max-w-4xl">
                            <DialogHeader>
                              <DialogTitle className="flex items-center gap-2">
                                {report.file_name}
                              </DialogTitle>
                            </DialogHeader>
                            <div className="mt-4 flex justify-center">
                              <ImageWithFallback
                                imageUrl={report.image_url}
                                fileName={report.file_name}
                                className="max-w-full max-h-[70vh] object-contain rounded border"
                              />
                            </div>
                            <div className="mt-4 space-y-2">
                              <div className="flex items-center gap-2">
                                <span className="text-sm font-medium">Classificação:</span>
                                {getClassificationBadge(report.spam, report.scam)}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                <p>Tamanho: {formatFileSize(report.file_size || 0)}</p>
                                <p>Tipo: {report.mime_type || 'Não especificado'}</p>
                                <p>Aprovado em: {formatDate(report.approved_at)}</p>
                              </div>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                      <TableCell>{report.file_name}</TableCell>
                      <TableCell>
                        {getClassificationBadge(report.spam, report.scam)}
                      </TableCell>
                      <TableCell>{formatFileSize(report.file_size || 0)}</TableCell>
                      <TableCell>{formatDate(report.approved_at)}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
};
