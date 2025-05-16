export function parseHtmlSections(html: string): {
  sectionName: string;
  content: string;
}[] {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;
  
  const divs = tempDiv.querySelectorAll('div[data-section]');
  
  return Array.from(divs).map((div) => ({
    sectionName: div.getAttribute('data-section') || '',
    content: div.innerHTML,
  }));
}


export function combineSections(
  sections: { sectionName: string; content: string }[]
): string {
  return sections
    .map(
      (section) =>
        `<div data-section="${section.sectionName}">${section.content}</div>`
    )
    .join('\n');
}
