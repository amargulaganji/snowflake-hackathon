import { useState, useEffect } from 'react';
import { Upload, FileText, Search, RefreshCw } from 'lucide-react';
import axios from 'axios';

interface Document {
  document_id: string;
  title: string;
  file_name: string;
  file_type: string;
  document_type: string;
  member_id: string | null;
  category: string;
  issuing_authority: string | null;
  version: string | null;
  effective_date: string | null;
  processing_status: string;
  ingested_at: string;
}

const CATEGORIES = ['All', 'Clinical', 'Policy', 'Regulatory', 'Legal'];
const STATUS_COLORS: Record<string, string> = {
  uploaded: '#B26A00',
  parsed: '#1565C0',
  chunked: '#6A1B9A',
  indexed: '#2E7D32',
  ready: '#2E7D32',
  failed: '#C62828',
};

export function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [uploading, setUploading] = useState(false);

  const fetchDocuments = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (category !== 'All') params.category = category.toLowerCase();
      const { data } = await axios.get('/documents', { params });
      setDocuments(data);
    } catch { setDocuments([]); }
    setLoading(false);
  };

  useEffect(() => { fetchDocuments(); }, [category]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const form = new FormData();
      form.append('file', file);
      await axios.post('/documents/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } });
      await fetchDocuments();
    } catch (err) {
      console.error('Upload failed', err);
    }
    setUploading(false);
    e.target.value = '';
  };

  const filtered = documents.filter((d) =>
    !search || d.title?.toLowerCase().includes(search.toLowerCase()) || d.file_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="page-container">
      <div className="page-header">
        <h2><FileText size={20} /> Documents</h2>
        <p className="page-subtitle">Upload and manage clinical, policy, regulatory, and legal documents</p>
      </div>

      <div className="page-toolbar">
        <div className="filter-chips-row">
          {CATEGORIES.map((cat) => (
            <button key={cat} className={`filter-chip ${category === cat ? 'filter-chip-active' : ''}`} onClick={() => setCategory(cat)}>
              {cat}
            </button>
          ))}
        </div>
        <div className="toolbar-right">
          <div className="search-box">
            <Search size={14} />
            <input type="text" placeholder="Search documents..." value={search} onChange={(e) => setSearch(e.target.value)} />
          </div>
          <label className="upload-btn">
            <Upload size={14} />
            <span>{uploading ? 'Uploading...' : 'Upload'}</span>
            <input type="file" accept=".pdf,.txt,.docx" onChange={handleUpload} style={{ display: 'none' }} disabled={uploading} />
          </label>
        </div>
      </div>

      {loading ? (
        <div className="page-loading">Loading documents...</div>
      ) : filtered.length === 0 ? (
        <div className="page-empty">
          <FileText size={48} strokeWidth={1} />
          <p>No documents found. Upload a document to get started.</p>
        </div>
      ) : (
        <div className="documents-list">
          {filtered.map((doc) => (
            <div key={doc.document_id} className="document-row">
              <div className="doc-icon"><FileText size={20} /></div>
              <div className="doc-info">
                <div className="doc-title">{doc.title || doc.file_name}</div>
                <div className="doc-meta">
                  {doc.document_type && <span className="doc-type-badge">{doc.document_type}</span>}
                  <span>{doc.file_type?.toUpperCase()}</span>
                  {doc.member_id && <span>Member: {doc.member_id}</span>}
                  {doc.issuing_authority && <span>{doc.issuing_authority}</span>}
                  {doc.version && <span>v{doc.version}</span>}
                </div>
              </div>
              <div className="doc-status">
                <span className="status-dot" style={{ background: STATUS_COLORS[doc.processing_status] || '#999' }} />
                <span className="status-label">{doc.processing_status}</span>
              </div>
              {doc.processing_status === 'failed' && (
                <button className="retry-btn" onClick={fetchDocuments}><RefreshCw size={14} /></button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
