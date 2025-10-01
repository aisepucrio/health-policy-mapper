import React from 'react';
import { Header } from '@/components/Header';
import { ScamReportForm } from '@/components/ScamReportForm';
import { Footer } from '@/components/Footer';

const Index = () => {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      
      <main className="flex-1 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <ScamReportForm />
        </div>
      </main>
      
      <Footer />
    </div>
  );
};

export default Index;
