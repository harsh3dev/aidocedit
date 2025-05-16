
# Enhanced template sections with editability configuration
TEMPLATE_SECTIONS = {
    "Technical Blog": [
        {"name": "Title", "editable": False},
        {"name": "Introduction", "editable": True},
        {"name": "Background", "editable": True},
        {"name": "Key Features", "editable": True},
        {"name": "Use Cases", "editable": True},
        {"name": "Conclusion", "editable": True}
    ],
    "Documentation": [
        {"name": "Heading", "editable": False},
        {"name": "Overview", "editable": True},
        {"name": "Installation", "editable": True},
        {"name": "Usage", "editable": True},
        {"name": "Configuration", "editable": True},
        {"name": "Troubleshooting", "editable": True},
        {"name": "FAQ", "editable": True}
    ],
    "Case Study": [
        {"name": "Company Background", "editable": False},
        {"name": "Problem Statement", "editable": True},
        {"name": "Solution Implemented", "editable": True},
        {"name": "Results Achieved", "editable": True},
        {"name": "Lessons Learned", "editable": True}
    ]
}

# For backward compatibility, get a flat list of section names
def get_section_names(template_name):
    if template_name not in TEMPLATE_SECTIONS:
        return []
    return [section["name"] for section in TEMPLATE_SECTIONS[template_name]]

# Get editability status for a section
def is_section_editable(template_name, section_name):
    if template_name not in TEMPLATE_SECTIONS:
        return True  # Default to editable
    
    for section in TEMPLATE_SECTIONS[template_name]:
        if section["name"] == section_name:
            return section.get("editable", True)  # Default to editable if not specified
    
    return True  # Default to editable if section not found
