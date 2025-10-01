
import React, { useCallback, useState } from 'react';
import { Upload, X, Image as ImageIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFileSelect: (files: File[]) => void;
  selectedFiles: File[];
  disabled?: boolean;
}

const MAX_FILES = 10;

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  selectedFiles,
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [previews, setPreviews] = useState<string[]>([]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragOver(true);
    }
  }, [disabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    if (disabled) return;

    const files = Array.from(e.dataTransfer.files);
    const imageFiles = files.filter(file => file.type.startsWith('image/'));
    
    if (imageFiles.length > 0) {
      handleFileSelection(imageFiles);
    }
  }, [disabled]);

  const handleFileSelection = useCallback((files: File[]) => {
    const validFiles = files.filter(file => file.type.startsWith('image/'));
    const remainingSlots = MAX_FILES - selectedFiles.length;
    const filesToAdd = validFiles.slice(0, remainingSlots);
    
    const newFiles = [...selectedFiles, ...filesToAdd];
    onFileSelect(newFiles);
    
    // Create previews for new files
    const newPreviews = [...previews];
    filesToAdd.forEach((file, index) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const previewIndex = selectedFiles.length + index;
        newPreviews[previewIndex] = e.target?.result as string;
        setPreviews([...newPreviews]);
      };
      reader.readAsDataURL(file);
    });
  }, [onFileSelect, selectedFiles, previews]);

  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files ? Array.from(e.target.files) : [];
    if (files.length > 0) {
      handleFileSelection(files);
    }
    // Reset input value to allow selecting the same files again
    e.target.value = '';
  }, [handleFileSelection]);

  const removeFile = useCallback((index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    const newPreviews = previews.filter((_, i) => i !== index);
    onFileSelect(newFiles);
    setPreviews(newPreviews);
  }, [selectedFiles, previews, onFileSelect]);

  const removeAllFiles = useCallback(() => {
    onFileSelect([]);
    setPreviews([]);
  }, [onFileSelect]);

  const canAddMoreFiles = selectedFiles.length < MAX_FILES;

  return (
    <div className="w-full space-y-4">
      {/* Upload Area */}
      <div
        className={cn(
          "relative border-2 border-dashed rounded-lg p-6 transition-all duration-200",
          isDragOver
            ? "border-primary bg-primary/5 shadow-glow"
            : "border-border bg-card hover:border-primary/50 hover:bg-primary/5",
          disabled && "opacity-50 cursor-not-allowed",
          "min-h-[200px] flex flex-col items-center justify-center"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFiles.length === 0 ? (
          <>
            <Upload className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">
              Arraste imagens aqui
            </h3>
            <p className="text-sm text-muted-foreground mb-4 text-center">
              Ou clique no botão abaixo para selecionar múltiplos arquivos
            </p>
            <label className="cursor-pointer">
              <input
                type="file"
                className="hidden"
                accept="image/*"
                multiple
                onChange={handleFileInputChange}
                disabled={disabled}
              />
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                <ImageIcon className="h-4 w-4" />
                Selecionar Imagens
              </div>
            </label>
          </>
        ) : (
          <div className="w-full">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-medium text-foreground">
                {selectedFiles.length} imagem{selectedFiles.length !== 1 ? 's' : ''} selecionada{selectedFiles.length !== 1 ? 's' : ''}
              </h4>
              <button
                onClick={removeAllFiles}
                className="text-sm text-destructive hover:bg-destructive/10 px-3 py-1 rounded-md transition-colors"
              >
                Remover todas
              </button>
            </div>
            
            {/* Preview Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
              {selectedFiles.map((file, index) => (
                <div key={index} className="relative group">
                  {previews[index] && (
                    <img
                      src={previews[index]}
                      alt={`Preview ${index + 1}`}
                      className="w-full h-24 object-cover rounded-md shadow-elevation"
                    />
                  )}
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded-md flex items-center justify-center">
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1 text-white hover:text-destructive transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="mt-1">
                    <p className="text-xs font-medium text-foreground truncate">
                      {file.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Add more files button - only show if under limit */}
            {canAddMoreFiles && (
              <label className="cursor-pointer inline-block">
                <input
                  type="file"
                  className="hidden"
                  accept="image/*"
                  multiple
                  onChange={handleFileInputChange}
                  disabled={disabled}
                />
                <div className="inline-flex items-center gap-2 px-3 py-2 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors">
                  <ImageIcon className="h-4 w-4" />
                  Adicionar mais imagens ({MAX_FILES - selectedFiles.length} restante{MAX_FILES - selectedFiles.length !== 1 ? 's' : ''})
                </div>
              </label>
            )}

            {/* Max files reached message */}
            {!canAddMoreFiles && (
              <p className="text-sm text-muted-foreground">
                Limite máximo de {MAX_FILES} imagens atingido
              </p>
            )}
          </div>
        )}
      </div>
      
      {/* File Format Info */}
      <div className="text-xs text-muted-foreground text-center">
        Formatos aceitos: JPEG, PNG • Tamanho máximo: 10MB por arquivo • Máximo {MAX_FILES} arquivos por envio
      </div>
    </div>
  );
};
