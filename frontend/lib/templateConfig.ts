export const TEMPLATE_SECTION_CONFIG = {
  "Technical Blog": {
    "Title": false,  
    "Introduction": true,
    "Background": true,
    "Key Features": true,
    "Use Cases": true,
    "Summary": true,
    "Conclusion": true
  },
  "Documentation": {
    "Heading": false,  
    "Subheading": false,
    "Overview": true,
    "Installation": true,
    "Usage": true,
    "Configuration": true, 
    "Troubleshooting": true,
    "FAQ": true
  },
  "Case Study": {
    "Company Background": false,  
    "Problem Statement": true,
    "Solution Implemented": true,
    "Results Achieved": true,
    "Lessons Learned": true
  }
};

export function isSectionEditable(template: string, sectionName: string): boolean {
  if (!TEMPLATE_SECTION_CONFIG[template as keyof typeof TEMPLATE_SECTION_CONFIG]) {
    return true; 
  }
  
  const templateConfig = TEMPLATE_SECTION_CONFIG[template as keyof typeof TEMPLATE_SECTION_CONFIG];
  return templateConfig[sectionName as keyof typeof templateConfig] ?? true; 
}
