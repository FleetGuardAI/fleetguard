import api from './client';

/**
 * Fetch documents from the backend Document API.
 *
 * @param {object} params
 * @returns {Promise<Array>}
 */
export async function getDocuments(params = {}) {
  const listParams = {};
  if (params.storage_status) {
    listParams.storage_status = params.storage_status;
  }

  const documents = await api.documents.list(listParams) || [];

  if (params.search) {
    const q = params.search.toLowerCase();
    return documents.filter(d =>
      (d.original_filename && d.original_filename.toLowerCase().includes(q)) ||
      (d.storage_status && d.storage_status.toLowerCase().includes(q))
    );
  }

  return documents;
}

/**
 * Upload a document via the backend Document API.
 *
 * @param {File} file - The file to upload
 * @param {object} metadata - Document metadata (name, category, expiry_date, target_id, target_type)
 * @returns {Promise<object>}
 */
export async function uploadDocument(file, metadata = {}) {
  const formData = new FormData();
  formData.append('file', file);
  
  if (metadata.name) formData.append('name', metadata.name);
  if (metadata.category) formData.append('category', metadata.category);
  if (metadata.expiry_date) formData.append('expiry_date', metadata.expiry_date);
  if (metadata.target_id) formData.append('target_id', metadata.target_id);
  if (metadata.target_type) formData.append('target_type', metadata.target_type);
  
  return await api.documents.upload(formData);
}

/**
 * Get a document by ID.
 *
 * @param {string} documentId
 * @returns {Promise<object>}
 */
export async function getDocumentById(documentId) {
  return await api.documents.get(documentId);
}
