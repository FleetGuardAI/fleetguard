import { mockDocuments } from '@/data/mockData';

let localDocuments = [...mockDocuments];

export async function getDocuments(params = {}) {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...localDocuments];
      if (params.search) {
        const q = params.search.toLowerCase();
        filtered = filtered.filter(d =>
          d.name.toLowerCase().includes(q) ||
          d.target_name.toLowerCase().includes(q)
        );
      }
      resolve(filtered);
    }, 500);
  });
}

export async function uploadDocument(data) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const newDoc = {
        id: localDocuments.length + 1,
        status: 'active',
        file_url: 'https://example.com/uploaded_file.pdf',
        ...data
      };
      localDocuments.unshift(newDoc);
      resolve(newDoc);
    }, 600);
  });
}
