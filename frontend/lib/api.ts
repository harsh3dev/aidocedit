const API_URL = 'http://localhost:8000';

export async function fetchTemplates() {
  try {
    const response = await fetch(`${API_URL}/templates/`);
    if (!response.ok) {
      throw new Error('Failed to fetch templates');
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching templates:', error);
    return {
      templates: ["Technical Blog", "Documentation", "Case Study"]
    };
  }
}

export async function createDocument(data: { userQuery: string; selectedTemplate: string }) {
  const response = await fetch(`${API_URL}/generate/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      userQuery: data.userQuery,
      selectedTemplate: data.selectedTemplate,
    }),
  });

  if (!response.ok) {
    throw new Error('Network response was not ok');
  }
  
  return await response.json();
}
