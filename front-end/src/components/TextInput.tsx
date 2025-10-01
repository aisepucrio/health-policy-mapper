import React from 'react';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

interface TextInputProps {
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export const TextInput: React.FC<TextInputProps> = ({
  value,
  onChange,
  disabled = false,
  placeholder = "Cole a mensagem de texto do golpe aqui..."
}) => {
  return (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">
          Mensagem do Golpe
        </label>
        <Textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={cn(
            "min-h-[200px] resize-none",
            "focus:shadow-glow transition-all duration-200",
            "text-base"
          )}
        />
      </div>
      
      {/* Character count and helper text */}
      <div className="flex justify-between items-center text-xs text-muted-foreground">
        <div>
          {value.length > 0 ? `${value.length} caracteres` : 'Digite ou cole o texto da mensagem suspeita'}
        </div>
        {value.length > 1000 && (
          <div className="text-warning">
            Mensagem muito longa
          </div>
        )}
      </div>
    </div>
  );
};