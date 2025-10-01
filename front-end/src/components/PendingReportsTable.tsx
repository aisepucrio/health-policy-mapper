import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Checkbox } from '@/components/ui/checkbox';
import { Trash2, FileText, Image as ImageIcon, Loader2, Eye, Zap, AlertTriangle } from 'lucide-react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface PendingTextReport {
  id: string;
  message: string;
  created_at: string;
  status: string;
}

interface PendingImageReport {
  id: string;
  image_url: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  status: string;
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

interface PendingReportsTableProps {
  onStatsUpdate: () => void;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export const PendingReportsTable: React.FC<PendingReportsTableProps> = ({ 
  onStatsUpdate, 
  activeTab = 'text',
  onTabChange 
}) => {
  const [pendingTextReports, setPendingTextReports] = useState<PendingTextReport[]>([]);
  const [pendingImageReports, setPendingImageReports] = useState<PendingImageReport[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    fetchPendingReports();
  }, []);

  const fetchPendingReports = async () => {
    setLoading(true);
    
    try {
      const [textResponse, imageResponse] = await Promise.all([
        supabase
          .from('pending_text_reports')
          .select('*')
          .eq('status', 'pending')
          .order('created_at', { ascending: false }),
        supabase
          .from('pending_image_reports')
          .select('*')
          .eq('status', 'pending')
          .order('created_at', { ascending: false })
      ]);

      if (textResponse.error) {
        console.error('Error fetching pending text reports:', textResponse.error);
        throw textResponse.error;
      }

      if (imageResponse.error) {
        console.error('Error fetching pending image reports:', imageResponse.error);
        throw imageResponse.error;
      }

      setPendingTextReports(textResponse.data || []);
      setPendingImageReports(imageResponse.data || []);
    } catch (error: any) {
      toast({
        title: "Erro ao carregar relatórios pendentes",
        description: error.message,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClassifyAndApprove = async (
    id: string, 
    type: 'text' | 'image', 
    isSpam: boolean, 
    isScam: boolean
  ) => {
    try {
      const spamValue = isSpam ? 1 : 0;
      const scamValue = isScam ? 1 : 0;

      if (type === 'text') {
        const report = pendingTextReports.find(r => r.id === id);
        if (!report) return;

        await supabase.from('approved_texts' as any).insert({
          message: report.message,
          original_id: report.id,
          spam: spamValue,
          scam: scamValue
        });

        await supabase
          .from('pending_text_reports')
          .update({ status: 'approved' })
          .eq('id', id);
      } else {
        const report = pendingImageReports.find(r => r.id === id);
        if (!report) return;

        await supabase.from('approved_images' as any).insert({
          image_url: report.image_url,
          file_name: report.file_name,
          file_size: report.file_size,
          mime_type: report.mime_type,
          original_id: report.id,
          spam: spamValue,
          scam: scamValue
        });

        await supabase
          .from('pending_image_reports')
          .update({ status: 'approved' })
          .eq('id', id);
      }

      toast({
        title: "Conteúdo classificado e aprovado",
        description: `${type === 'text' ? 'Texto' : 'Imagem'} aprovado com sucesso!`,
      });

      await fetchPendingReports();
      onStatsUpdate();
    } catch (error: any) {
      console.error('Erro ao classificar e aprovar:', error);
      toast({
        title: "Erro ao classificar conteúdo",
        description: error.message,
        variant: "destructive",
      });
    }
  };

  const handleDelete = async (id: string, type: 'text' | 'image') => {
    try {
      if (type === 'text') {
        await supabase
          .from('pending_text_reports')
          .delete()
          .eq('id', id);
      } else {
        await supabase
          .from('pending_image_reports')
          .delete()
          .eq('id', id);
      }

      toast({
        title: "Conteúdo deletado",
        description: `${type === 'text' ? 'Texto' : 'Imagem'} removido com sucesso!`,
      });

      await fetchPendingReports();
      onStatsUpdate();
    } catch (error: any) {
      console.error('Erro ao deletar:', error);
      toast({
        title: "Erro ao deletar conteúdo",
        description: error.message,
        variant: "destructive",
      });
    }
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

  const ClassificationControls: React.FC<{
    reportId: string;
    type: 'text' | 'image';
  }> = ({ reportId, type }) => {
    const [isSpam, setIsSpam] = useState(false);
    const [isScam, setIsScam] = useState(false);

    const handleSpamChange = (checked: boolean | "indeterminate") => {
      setIsSpam(checked === true);
    };

    const handleScamChange = (checked: boolean | "indeterminate") => {
      setIsScam(checked === true);
    };

    const handleSubmit = () => {
      handleClassifyAndApprove(reportId, type, isSpam, isScam);
    };

    return (
      <div className="flex items-center gap-4">
        <div className="flex items-center space-x-2">
          <Checkbox
            id={`spam-${reportId}`}
            checked={isSpam}
            onCheckedChange={handleSpamChange}
          />
          <label
            htmlFor={`spam-${reportId}`}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-1"
          >
            <Zap className="h-3 w-3 text-orange-600" />
            Spam
          </label>
        </div>
        
        <div className="flex items-center space-x-2">
          <Checkbox
            id={`scam-${reportId}`}
            checked={isScam}
            onCheckedChange={handleScamChange}
          />
          <label
            htmlFor={`scam-${reportId}`}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 flex items-center gap-1"
          >
            <AlertTriangle className="h-3 w-3 text-red-600" />
            Scam
          </label>
        </div>

        <Button onClick={handleSubmit} size="sm">
          Classificar
        </Button>

        <Button
          onClick={() => handleDelete(reportId, type)}
          variant="outline"
          size="sm"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
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
    <Tabs value={activeTab} onValueChange={onTabChange} className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="text" className="flex items-center gap-2">
          <FileText className="h-4 w-4" />
          Textos ({pendingTextReports.length})
        </TabsTrigger>
        <TabsTrigger value="image" className="flex items-center gap-2">
          <ImageIcon className="h-4 w-4" />
          Imagens ({pendingImageReports.length})
        </TabsTrigger>
      </TabsList>

      <TabsContent value="text">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-blue-500" />
              Textos Pendentes
            </CardTitle>
            <CardDescription>
              Mensagens aguardando classificação pelos administradores.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingTextReports.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Nenhum texto pendente para revisão.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Mensagem</TableHead>
                    <TableHead>Data de Criação</TableHead>
                    <TableHead>Classificação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingTextReports.map((report) => (
                    <TableRow key={report.id}>
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
                                <div className="mt-4 text-sm text-muted-foreground">
                                  <p>Criado em: {formatDate(report.created_at)}</p>
                                </div>
                              </div>
                            </DialogContent>
                          </Dialog>
                        </div>
                      </TableCell>
                      <TableCell>{formatDate(report.created_at)}</TableCell>
                      <TableCell>
                        <ClassificationControls reportId={report.id} type="text" />
                      </TableCell>
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
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5 text-blue-500" />
              Imagens Pendentes
            </CardTitle>
            <CardDescription>
              Imagens aguardando classificação pelos administradores.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {pendingImageReports.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Nenhuma imagem pendente para revisão.
              </p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Preview</TableHead>
                    <TableHead>Nome do Arquivo</TableHead>
                    <TableHead>Tamanho</TableHead>
                    <TableHead>Data de Criação</TableHead>
                    <TableHead>Classificação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {pendingImageReports.map((report) => (
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
                              <DialogTitle>{report.file_name}</DialogTitle>
                            </DialogHeader>
                            <div className="mt-4 flex justify-center">
                              <ImageWithFallback
                                imageUrl={report.image_url}
                                fileName={report.file_name}
                                className="max-w-full max-h-[70vh] object-contain rounded border"
                              />
                            </div>
                            <div className="mt-4 text-sm text-muted-foreground">
                              <p>Tamanho: {formatFileSize(report.file_size || 0)}</p>
                              <p>Tipo: {report.mime_type || 'Não especificado'}</p>
                              <p>Criado em: {formatDate(report.created_at)}</p>
                            </div>
                          </DialogContent>
                        </Dialog>
                      </TableCell>
                      <TableCell>{report.file_name}</TableCell>
                      <TableCell>{formatFileSize(report.file_size || 0)}</TableCell>
                      <TableCell>{formatDate(report.created_at)}</TableCell>
                      <TableCell>
                        <ClassificationControls reportId={report.id} type="image" />
                      </TableCell>
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
