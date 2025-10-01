
import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { LogOut, BarChart3, Clock, FileCheck } from 'lucide-react';
import { PendingReportsTable } from '@/components/PendingReportsTable';
import { ApprovedContentTabs } from '@/components/ApprovedContentTabs';
import { DashboardStats } from '@/components/DashboardStats';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';

interface DashboardStatsType {
  pendingTexts: number;
  pendingImages: number;
  scamTexts: number;
  scamImages: number;
  hamTexts: number;
  hamImages: number;
  spamTexts: number;
  spamImages: number;
  spamScamTexts: number;
  spamScamImages: number;
}

export const AdminDashboard: React.FC = () => {
  const { signOut } = useAuth();
  const [activeTab, setActiveTab] = useState('stats');
  const [pendingActiveTab, setPendingActiveTab] = useState('text');
  const [stats, setStats] = useState<DashboardStatsType>({
    pendingTexts: 0,
    pendingImages: 0,
    scamTexts: 0,
    scamImages: 0,
    hamTexts: 0,
    hamImages: 0,
    spamTexts: 0,
    spamImages: 0,
    spamScamTexts: 0,
    spamScamImages: 0,
  });

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      const [
        pendingTexts, 
        pendingImages, 
        approvedTexts,
        approvedImages
      ] = await Promise.all([
        supabase.from('pending_text_reports').select('id', { count: 'exact' }).eq('status', 'pending'),
        supabase.from('pending_image_reports').select('id', { count: 'exact' }).eq('status', 'pending'),
        supabase.from('approved_texts' as any).select('spam, scam', { count: 'exact' }),
        supabase.from('approved_images' as any).select('spam, scam', { count: 'exact' }),
      ]);

      // Count scam, spam and ham from approved content with safe fallbacks
      let scamTexts = 0;
      let scamImages = 0; 
      let hamTexts = 0;
      let hamImages = 0;
      let spamTexts = 0;
      let spamImages = 0;
      let spamScamTexts = 0;
      let spamScamImages = 0;

      if (approvedTexts.data && Array.isArray(approvedTexts.data)) {
        scamTexts = approvedTexts.data.filter((item: any) => item.scam === 1).length;
        spamTexts = approvedTexts.data.filter((item: any) => item.spam === 1).length;
        spamScamTexts = approvedTexts.data.filter((item: any) => item.spam === 1 && item.scam === 1).length;
        hamTexts = approvedTexts.data.filter((item: any) => item.spam === 0 && item.scam === 0).length;
      }

      if (approvedImages.data && Array.isArray(approvedImages.data)) {
        scamImages = approvedImages.data.filter((item: any) => item.scam === 1).length;
        spamImages = approvedImages.data.filter((item: any) => item.spam === 1).length;
        spamScamImages = approvedImages.data.filter((item: any) => item.spam === 1 && item.scam === 1).length;
        hamImages = approvedImages.data.filter((item: any) => item.spam === 0 && item.scam === 0).length;
      }

      setStats({
        pendingTexts: pendingTexts.count || 0,
        pendingImages: pendingImages.count || 0,
        scamTexts,
        scamImages,
        hamTexts,
        hamImages,
        spamTexts,
        spamImages,
        spamScamTexts,
        spamScamImages,
      });
    } catch (error) {
      console.error('Erro ao buscar estatísticas:', error);
    }
  };

  const handleSignOut = async () => {
    await signOut();
  };

  const handleStatsUpdate = () => {
    fetchStats();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold bg-gradient-primary bg-clip-text text-transparent">
              ScamWatchBrasil
            </h1>
            <p className="text-sm text-muted-foreground">Painel Administrativo</p>
          </div>
          <Button onClick={handleSignOut} variant="outline">
            <LogOut className="h-4 w-4 mr-2" />
            Sair
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="container py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-6">
            <TabsTrigger value="stats" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Métricas
            </TabsTrigger>
            <TabsTrigger value="pending" className="flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Pendentes
            </TabsTrigger>
            <TabsTrigger value="approved" className="flex items-center gap-2">
              <FileCheck className="h-4 w-4" />
              Aprovados
            </TabsTrigger>
          </TabsList>

          <TabsContent value="stats">
            <DashboardStats stats={stats} />
          </TabsContent>

          <TabsContent value="pending">
            <PendingReportsTable 
              onStatsUpdate={handleStatsUpdate} 
              activeTab={pendingActiveTab}
              onTabChange={setPendingActiveTab}
            />
          </TabsContent>

          <TabsContent value="approved">
            <ApprovedContentTabs />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};
