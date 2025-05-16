
import React, { useEffect } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { cn } from '@/lib/utils';

type EditableSectionProps = {
  sectionName: string;
  content: string;
  editable: boolean;
  onUpdate: (html: string) => void;
  className?: string;
};

export default function EditableSection({
  sectionName,
  content,
  editable,
  onUpdate,
  className,
}: EditableSectionProps) {
  const editor = useEditor({
    extensions: [StarterKit],
    content,
    editable,
    onUpdate: ({ editor }) => {
      if (editable) {
        onUpdate(editor.getHTML());
      }
    },
  });

  useEffect(() => {
    if (editor && content !== editor.getHTML()) {
      editor.commands.setContent(content);
    }
  }, [content, editor]);

  useEffect(() => {
    if (editor && editor.isEditable !== editable) {
      editor.setEditable(editable);
    }
  }, [editable, editor]);

  return (
    <div 
      className={cn(
        "my-4 rounded-lg transition-all duration-200",
        editable ? "border-2 border-blue-400 shadow-md" : "border border-gray-200",
        className
      )}
    >
      <div className="flex items-center justify-between bg-gray-50 px-4 py-2 rounded-t-lg border-b border-gray-200">
        <h3 className="text-sm font-medium text-gray-700">{sectionName}</h3>
        <span 
          className={cn(
            "text-xs px-2 py-1 rounded-full",
            editable 
              ? "bg-blue-100 text-blue-800" 
              : "bg-gray-100 text-gray-600"
          )}
        >
          {editable ? "Editing" : "Read-only"}
        </span>
      </div>
      
      <div className={cn(
        "px-4 py-3 prose prose-sm max-w-none",
        editable ? "bg-white" : "bg-gray-50"
      )}>
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
