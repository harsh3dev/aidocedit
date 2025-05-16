
const sectionChunks = [
  `<div data-section="Heading"><h1>Understanding REST APIs: A Beginner's Guide</h1></div>`,
  `<div data-section="Introduction"><p>REST (Representational State Transfer) APIs are the backbone of modern web applications. They provide a standardized way for web clients to communicate with servers using HTTP methods. This guide will walk you through the basics of REST APIs and how to use them effectively in your applications.</p></div>`,
  `<div data-section="Key Concepts"><h2>Key Concepts in REST</h2><ul><li><strong>Resources</strong>: Everything is a resource that can be accessed via a unique URI</li><li><strong>HTTP Methods</strong>: Using standard HTTP verbs (GET, POST, PUT, DELETE) for operations</li><li><strong>Stateless</strong>: Each request contains all information needed to complete it</li></ul></div>`,
  `<div data-section="Code Example"><h3>Making a REST API Request</h3><pre><code>// Example GET request using fetch
fetch('https://api.example.com/users')
  .then(response => response.json())
  .then(data => console.log(data))
  .catch(error => console.error('Error:', error));</code></pre></div>`,
  `<div data-section="Best Practices"><h2>REST API Best Practices</h2><p>When designing your REST APIs, consider these best practices:</p><ul><li>Use nouns for resource endpoints</li><li>Properly implement HTTP status codes</li><li>Implement pagination for large data sets</li><li>Version your API</li></ul></div>`,
];

let index = 0;

export async function getNextSection(): Promise<string | null> {
  if (index >= sectionChunks.length) return null;
  const section = sectionChunks[index++];
  
  const delay = Math.floor(Math.random() * 1200) + 800;
  await new Promise((res) => setTimeout(res, delay));
  
  return section;
}

export function resetStream(): void {
  index = 0;
}
