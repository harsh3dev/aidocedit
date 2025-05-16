export type Template = "Technical Blog" | "Documentation" | "Case Study";

export interface FormData {
  userQuery: string;
  selectedTemplate: Template;
}

export interface FormState {
  isLoading: boolean;
  errors: {
    userQuery?: string;
    selectedTemplate?: string;
    form?: string;
  };
}

export interface Section {
  id: string;
  name: string;
  html: string;
  isEditable?: boolean;
}

export interface WebSocketMessage {
  type: string;
  section_id?: string;
  section_name?: string;
  content?: string;
  is_editable?: boolean;
}

export interface FeedbackMessage {
  section_id: string;
  feedback_type: 'continue' | 'edit';
  edited_content?: string;
}

export interface Document {
  id: string;
  user_query: string;
  template_type: Template;
  content_generated: boolean;
  sections: Section[];
}