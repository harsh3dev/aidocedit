"use client";

import { useState, useEffect } from "react";
import { FormData, FormState, Template } from "@/lib/types";
import { FormField } from "@/components/ui/form-field";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { createDocument, fetchTemplates } from "@/lib/api";

export function DashboardForm() {
  const [availableTemplates, setAvailableTemplates] = useState<Template[]>(["Technical Blog", "Documentation", "Case Study"]);
  const [formData, setFormData] = useState<FormData>({
    userQuery: "",
    selectedTemplate: "Technical Blog",
  });

  const [formState, setFormState] = useState<FormState>({
    isLoading: false,
    errors: {},
  });
  
  useEffect(() => {
    async function loadTemplates() {
      try {
        const data = await fetchTemplates();
        if (data.templates && data.templates.length > 0) {
          setAvailableTemplates(data.templates);
          setFormData(prev => ({
            ...prev,
            selectedTemplate: data.templates[0]
          }));
        }
      } catch (error) {
        console.error("Error loading templates:", error);
      }
    }
    
    loadTemplates();
  }, []);

  const validateForm = (): boolean => {
    const errors: FormState["errors"] = {};

    if (!formData.userQuery || formData.userQuery.length < 10) {
      errors.userQuery = "Query must be at least 10 characters";
    }

    if (!formData.selectedTemplate) {
      errors.selectedTemplate = "Please select a template";
    }

    setFormState((prev) => ({ ...prev, errors }));
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setFormState({
      isLoading: true,
      errors: {},
    });

    try {
      const data = await createDocument({
        userQuery: formData.userQuery,
        selectedTemplate: formData.selectedTemplate,
      });
      
      console.log("Response data:", data);
      
      setFormData({
        userQuery: "",
        selectedTemplate: availableTemplates[0],
      });
      
      if (data.document_id) {
        window.location.href = `/edit/${data.document_id}`;
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      setFormState((prev) => ({
        ...prev,
        errors: {
          form: "An error occurred while submitting the form. Please try again.",
        },
      }));
    } finally {
      setFormState((prev) => ({
        ...prev,
        isLoading: false,
      }));
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleTemplateChange = (value: Template) => {
    setFormData((prev) => ({
      ...prev,
      selectedTemplate: value,
    }));
  };

  const isSubmitDisabled =
    formState.isLoading ||
    !formData.userQuery ||
    formData.userQuery.length < 10 ||
    !formData.selectedTemplate;

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <FormField
        id="userQuery"
        label="Your Query"
        error={formState.errors.userQuery}
      >
        <Input
          id="userQuery"
          name="userQuery"
          value={formData.userQuery}
          onChange={handleInputChange}
          placeholder="Enter your query (min. 10 characters)"
          className="w-full transition-all duration-200 focus-visible:ring-2"
          disabled={formState.isLoading}
        />
      </FormField>

      <FormField
        id="selectedTemplate"
        label="Template"
        error={formState.errors.selectedTemplate}
      >
        <Select
          value={formData.selectedTemplate}
          onValueChange={handleTemplateChange}
          disabled={formState.isLoading}
        >
          <SelectTrigger className="w-full transition-all duration-200 focus-visible:ring-2">
            <SelectValue placeholder="Select a template" />
          </SelectTrigger>
          <SelectContent>
            {availableTemplates.map((template) => (
              <SelectItem key={template} value={template}>{template}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </FormField>

      {formState.errors.form && (
        <p className="text-sm text-destructive">{formState.errors.form}</p>
      )}

      <Button
        type="submit"
        className="w-full transition-all duration-200 hover:scale-[1.02] active:scale-[0.98]"
        disabled={isSubmitDisabled}
      >
        {formState.isLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          "Submit"
        )}
      </Button>
    </form>
  );
}