import React from 'react';
import { Shield, Heart, Github, Mail } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="w-full bg-card border-t border-border py-8 px-4 mt-12">
      <div className="max-w-4xl mx-auto">
        <div className="text-center space-y-4">
          <div className="flex items-center justify-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            <span className="font-semibold text-foreground">ScamWatch Brasil</span>
          </div>
          
          <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
            Uma iniciativa para combater golpes digitais no Brasil através da colaboração 
            da comunidade. Mantenha-se seguro e ajude outros a se protegerem.
          </p>
          
          <div className="flex items-center justify-center gap-6 pt-4">
            <a 
              href="mailto:contato@scamwatchbrasil.com" 
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              <Mail className="h-4 w-4" />
              Contato
            </a>
            <a 
              href="https://github.com/scamwatchbrasil" 
              className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary transition-colors"
            >
              <Github className="h-4 w-4" />
              GitHub
            </a>
          </div>
          
          <div className="pt-4 border-t border-border">
            <p className="text-xs text-muted-foreground flex items-center justify-center gap-1">
              Feito com <Heart className="h-3 w-3 text-destructive" /> para proteger nossa comunidade
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
};