export type Template = "blog" | "documentation";

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