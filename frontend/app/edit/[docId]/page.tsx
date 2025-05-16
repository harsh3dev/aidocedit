/* eslint-disable @typescript-eslint/no-explicit-any */

'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useParams } from 'next/navigation';
import EditableSection from '@/components/EditableSection';
import { ArrowDown, CheckCircle2, PencilLine } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { websocketService } from '@/lib/websocketService';
import { isSectionEditable } from '@/lib/templateConfig';

export default function DocumentEditor() {
  const params = useParams();
  const docId = params?.docId as string;
  
  const [sections, setSections] = useState<{ id: string; name: string; html: string; is_editable?: boolean }[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [editableMap, setEditableMap] = useState<Record<string, boolean>>({});
  const [isComplete, setIsComplete] = useState(false);
  const [streamEnded, setStreamEnded] = useState(false);
  const [processingSection, setProcessingSection] = useState<string | null>(null);
  const [documentComplete, setDocumentComplete] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("Technical Blog");

  const handleSectionContent = useCallback((data: any) => {
    if (data.type === 'section_content' && data.section_id && data.section_name && data.content) {
      if (data.template) {
        setSelectedTemplate(data.template);
      }
      
      const isExplicitlyEditable = data.is_editable !== undefined;
      const sectionEditability = isExplicitlyEditable
        ? data.is_editable
        : isSectionEditable(selectedTemplate, data.section_name);
      
      const newSection = {
        id: data.section_id,
        name: data.section_name,
        html: data.content,
        is_editable: sectionEditability,
      };
      
      setSections((prev) => [...prev, newSection]);
      
      setEditableMap((prev) => ({
        ...prev,
        [newSection.id]: false,
      }));
      
      setProcessingSection(null);
      setCurrentIndex((prev) => prev + 1);
      setIsLoading(false);
    } else if (data.type === 'stream_end') {
      setStreamEnded(true);
      setProcessingSection(null);
    } else if (data.type === 'document_complete') {
      setDocumentComplete(true);
      setStreamEnded(true);
      setIsComplete(true);
      setProcessingSection(null);
    } else if (data.type === 'template_info' && data.template) {
      setSelectedTemplate(data.template);
    }
  }, [selectedTemplate]);

  const handleStreamEnd = useCallback(() => {
    setStreamEnded(true);
  }, []);

  useEffect(() => {
    if (!docId) {
      return;
    }
    
    websocketService.connect(docId);
    websocketService.addEventListener('section_content', handleSectionContent);
    websocketService.addEventListener('stream_end', handleStreamEnd);
    websocketService.addEventListener('document_complete', () => {
      setDocumentComplete(true);
      setStreamEnded(true);
      setIsComplete(true);
      setProcessingSection(null);
    });
    
    websocketService.addEventListener('template_info', (data) => {
      if (data.template) {
        setSelectedTemplate(data.template);
      }
    });
    
    websocketService.sendMessage({
      type: 'init',
      document_id: docId,
    });
    
    return () => {
      websocketService.disconnect();
      websocketService.removeEventListener('section_content', handleSectionContent);
      websocketService.removeEventListener('stream_end', handleStreamEnd);
      websocketService.removeEventListener('document_complete', () => {});
      websocketService.removeEventListener('template_info', () => {});
    };
  }, [docId, handleSectionContent, handleStreamEnd]);
  

  const handleContinue = useCallback(() => {
    if (currentIndex > 0 && currentIndex <= sections.length) {
      const currentSection = sections[currentIndex - 1];
      if (currentSection) {
        setProcessingSection(currentSection.id);
        
        websocketService.sendMessage({
          type: 'feedback',
          section_id: currentSection.id,
          feedback_type: 'continue',
        });
      }
    }
    
    setEditableMap((prev) => ({
      ...prev,
      [sections[currentIndex - 1]?.id]: false,
    }));
    
    if (streamEnded && currentIndex >= sections.length) {
      setIsComplete(true);
    }
  }, [currentIndex, sections, streamEnded]);
  
  const handleMakeChanges = useCallback(() => {
    setEditableMap((prev) => ({
      ...prev,
      [sections[currentIndex - 1]?.id]: true,
    }));
  }, [currentIndex, sections]);

  const handleSectionUpdate = useCallback((index: number, html: string) => {
    const sectionToUpdate = sections[index];
    if (!sectionToUpdate) return;
    
    setSections((prev) =>
      prev.map((section, i) => (i === index ? { ...section, html } : section))
    );
    
    websocketService.sendMessage({
      type: 'feedback',
      section_id: sectionToUpdate.id,
      feedback_type: 'edit',
      edited_content: html,
    });
  }, [sections]);

  return (
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">
          Document Editor {docId ? `#${docId}` : ''}
        </h1>
        <p className="text-gray-600 mt-1">
          Review AI-generated content section by section
        </p>
      </div>
      
      <div className="space-y-4">
        {sections.map((section, index) => (
          <EditableSection
            key={`${section.id}-${index}`}
            sectionName={section.name}
            content={section.html}
            editable={!!section.is_editable && !!editableMap[section.id]}
            onUpdate={(html) => handleSectionUpdate(index, html)}
            className={index === currentIndex - 1 ? "" : ""}
          />
        ))}
      </div>

      {!isComplete && sections.length > 0 && currentIndex > 0 && currentIndex <= sections.length && !documentComplete && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-2">Feedback for &quot;{sections[currentIndex - 1]?.name}&quot;</h3>
          
          <div className="flex flex-wrap gap-3">
            <Button
              onClick={handleContinue}
              className="bg-green-600 hover:bg-green-700"
              disabled={isLoading || processingSection !== null}
            >
              <CheckCircle2 className="mr-2 h-4 w-4" />
              {isLoading ? 'Loading...' : processingSection !== null ? 'Processing...' : 'Continue'}
            </Button>
            
            {sections[currentIndex - 1]?.is_editable && (
              <Button
                onClick={handleMakeChanges}
                variant="outline"
                disabled={isLoading || !!editableMap[sections[currentIndex - 1]?.id] || processingSection !== null}
              >
                <PencilLine className="mr-2 h-4 w-4" />
                Make Changes
              </Button>
            )}
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center my-6">
          <div className="animate-bounce bg-blue-500 p-2 w-10 h-10 ring-1 ring-blue-200 shadow-lg rounded-full flex items-center justify-center">
            <ArrowDown className="h-6 w-6 text-white" />
          </div>
        </div>
      )}

    </div>
  );
}
