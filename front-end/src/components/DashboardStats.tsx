import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { FileText, Image as ImageIcon, Clock, AlertTriangle, Shield, Zap, BarChart3, TrendingUp } from 'lucide-react';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer } from 'recharts';

interface DashboardStatsProps {
  stats: {
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
  };
}

export const DashboardStats: React.FC<DashboardStatsProps> = ({ stats }) => {
  const totalApprovedTexts = stats.scamTexts + stats.hamTexts + stats.spamTexts;
  const totalApprovedImages = stats.scamImages + stats.hamImages + stats.spamImages;
  
  // Dados para gráfico de textos
  const textChartData = [
    {
      name: 'Ham',
      value: stats.hamTexts,
      fill: '#22c55e', // verde
    },
    {
      name: 'Spam + Scam',
      value: stats.spamScamTexts,
      fill: '#f97316', // laranja
    },
    {
      name: 'Apenas Spam',
      value: stats.spamTexts - stats.spamScamTexts,
      fill: '#eab308', // amarelo
    },
    {
      name: 'Apenas Scam',
      value: stats.scamTexts - stats.spamScamTexts,
      fill: '#ef4444', // vermelho
    },
  ];

  // Dados para gráfico de imagens
  const imageChartData = [
    {
      name: 'Ham',
      value: stats.hamImages,
      fill: '#22c55e', // verde
    },
    {
      name: 'Spam + Scam',
      value: stats.spamScamImages,
      fill: '#f97316', // laranja
    },
    {
      name: 'Apenas Spam',
      value: stats.spamImages - stats.spamScamImages,
      fill: '#eab308', // amarelo
    },
    {
      name: 'Apenas Scam',
      value: stats.scamImages - stats.spamScamImages,
      fill: '#ef4444', // vermelho
    },
  ];

  // Dados para gráfico consolidado
  const totalHam = stats.hamTexts + stats.hamImages;
  const totalProblematic = (stats.spamTexts + stats.scamTexts - stats.spamScamTexts) + (stats.spamImages + stats.scamImages - stats.spamScamImages);
  
  const consolidatedChartData = [
    {
      name: 'Ham (Legítimo)',
      value: totalHam,
      fill: '#22c55e', // verde
    },
    {
      name: 'Spam ou Scam',
      value: totalProblematic,
      fill: '#ef4444', // vermelho
    },
  ];

  const chartConfig = {
    ham: {
      label: 'Ham (Legítimo)',
      color: '#22c55e',
    },
    spamScam: {
      label: 'Spam + Scam',
      color: '#f97316',
    },
    spam: {
      label: 'Apenas Spam',
      color: '#eab308',
    },
    scam: {
      label: 'Apenas Scam',
      color: '#ef4444',
    },
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Pendentes
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3" />
                  Textos
                </span>
                <span className="font-bold">{stats.pendingTexts}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <ImageIcon className="h-3 w-3" />
                  Imagens
                </span>
                <span className="font-bold">{stats.pendingImages}</span>
              </div>
            </div>
            <Badge variant="outline" className="mt-2">
              <Clock className="h-3 w-3 mr-1" />
              Aguardando revisão
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Aprovados
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3" />
                  Textos
                </span>
                <span className="font-bold">{totalApprovedTexts}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <ImageIcon className="h-3 w-3" />
                  Imagens
                </span>
                <span className="font-bold">{totalApprovedImages}</span>
              </div>
            </div>
            <Badge variant="outline" className="mt-2 text-blue-600 border-blue-600">
              <BarChart3 className="h-3 w-3 mr-1" />
              Classificados
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Scam Aprovados
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-red-600" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3" />
                  Textos
                </span>
                <span className="font-bold">{stats.scamTexts}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <ImageIcon className="h-3 w-3" />
                  Imagens
                </span>
                <span className="font-bold">{stats.scamImages}</span>
              </div>
            </div>
            <Badge variant="outline" className="mt-2 text-red-600 border-red-600">
              <AlertTriangle className="h-3 w-3 mr-1" />
              Scam
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Spam Aprovados
            </CardTitle>
            <Zap className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3" />
                  Textos
                </span>
                <span className="font-bold">{stats.spamTexts}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <ImageIcon className="h-3 w-3" />
                  Imagens
                </span>
                <span className="font-bold">{stats.spamImages}</span>
              </div>
            </div>
            <Badge variant="outline" className="mt-2 text-orange-600 border-orange-600">
              <Zap className="h-3 w-3 mr-1" />
              Spam
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Ham Aprovados
            </CardTitle>
            <Shield className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <FileText className="h-3 w-3" />
                  Textos
                </span>
                <span className="font-bold">{stats.hamTexts}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-sm">
                  <ImageIcon className="h-3 w-3" />
                  Imagens
                </span>
                <span className="font-bold">{stats.hamImages}</span>
              </div>
            </div>
            <Badge variant="outline" className="mt-2 text-green-600 border-green-600">
              <Shield className="h-3 w-3 mr-1" />
              Ham (Legítimo)
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Gráfico de Mensagens de Texto Aprovadas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Mensagens de Texto Aprovadas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfig}
            className="h-[300px] w-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={textChartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="value" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          
          {/* Legenda personalizada para textos */}
          <div className="flex flex-wrap justify-center gap-6 mt-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-sm font-medium">Total Ham: {stats.hamTexts}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span className="text-sm font-medium">Total Spam: {stats.spamTexts}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-sm font-medium">Total Scam: {stats.scamTexts}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Gráfico de Imagens Aprovadas */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ImageIcon className="h-5 w-5" />
            Imagens Aprovadas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfig}
            className="h-[300px] w-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={imageChartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="value" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          
          {/* Legenda personalizada para imagens */}
          <div className="flex flex-wrap justify-center gap-6 mt-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-sm font-medium">Total Ham: {stats.hamImages}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded"></div>
              <span className="text-sm font-medium">Total Spam: {stats.spamImages}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-sm font-medium">Total Scam: {stats.scamImages}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Novo Gráfico Consolidado */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Visão Geral - Ham vs Problemáticas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ChartContainer
            config={chartConfig}
            className="h-[300px] w-full"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={consolidatedChartData}>
                <XAxis dataKey="name" />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="value" />
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
          
          {/* Legenda personalizada para gráfico consolidado */}
          <div className="flex flex-wrap justify-center gap-6 mt-4 pt-4 border-t">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded"></div>
              <span className="text-sm font-medium">Total Ham (Textos + Imagens): {totalHam}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded"></div>
              <span className="text-sm font-medium">Total Problemáticas (Spam ou Scam): {totalProblematic}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
