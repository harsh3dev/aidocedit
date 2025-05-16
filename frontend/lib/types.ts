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
}

export interface WebSocketMessage {
  type: string;
  section_id?: string;
  section_name?: string;
  content?: string;
}

export interface FeedbackMessage {
  section_id: string;
  feedback_type: 'continue' | 'edit';
  edited_content?: string;
}