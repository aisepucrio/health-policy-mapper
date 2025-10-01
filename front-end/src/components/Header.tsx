import React from 'react';
import { Shield, AlertTriangle } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="w-full bg-gradient-hero text-primary-foreground py-8 px-4 shadow-elevation">
      <div className="max-w-4xl mx-auto text-center space-y-4 relative">
        <div className="absolute top-0 right-0">
          <a 
            href="/admin/login" 
            className="text-sm text-primary-foreground/80 hover:text-primary-foreground transition-colors"
          >
            Acesso Administrativo
          </a>
        </div>
        
        <div className="flex items-center justify-center gap-3 mb-4">
          <Shield className="h-8 w-8 animate-pulse-glow" />
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
            ScamWatch Brasil
          </h1>
          <AlertTriangle className="h-8 w-8 animate-pulse-glow" />
        </div>
        
        <p className="text-lg md:text-xl text-primary-foreground/90 max-w-3xl mx-auto leading-relaxed">
          Ajude a combater golpes e fraudes digitais no Brasil enviando mensagens ou imagens 
          de scam que você recebeu. Juntos, podemos proteger mais pessoas.
        </p>
        
        <div className="flex flex-wrap items-center justify-center gap-4 text-sm text-primary-foreground/80 pt-2">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-success rounded-full animate-pulse"></div>
            <span>Seguro e Anônimo</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-accent rounded-full animate-pulse"></div>
            <span>Rápido e Fácil</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-warning rounded-full animate-pulse"></div>
            <span>Proteção Coletiva</span>
          </div>
        </div>
      </div>
    </header>
  );
};