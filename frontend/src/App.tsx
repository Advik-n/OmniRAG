import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BookOpen, FileText, MessageSquare, Palette, Send, Settings, Trash2, Upload } from 'lucide-react';
import './style.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

type DocumentItem = { id: number; filename: string; status: string; pages: number; chunks: number };
type HistoryItem = { id: number; kind: string; prompt: string; response: string; created_at: string };
type Config = { roles: Record<string, string>; themes: string[]; workspace: { role: string; theme: string; system_prompt: string } };

const themeClass: Record<string, string> = {
  Nebula: 'theme-nebula', Aurora: 'theme-aurora', Midnight: 'theme-midnight', Cyberpunk: 'theme-cyberpunk',
  Sakura: 'theme-sakura', Solar: 'theme-solar', Ocean: 'theme-ocean', Matrix: 'theme-matrix',
};

function App() {
  const [active, setActive] = useState('Chat');
  const [config, setConfig] = useState<Config>();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [prompt, setPrompt] = useState('Summarize the uploaded content in a clean structured format.');
  const [answer, setAnswer] = useState('Upload lecture notes, a PDF, PPTX, DOCX, TXT, CSV, or a question paper. Then ask for a summary or answers.');
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState('General Assistant');
  const [theme, setTheme] = useState('Nebula');
  const [systemPrompt, setSystemPrompt] = useState('');

  const appTheme = useMemo(() => themeClass[theme] || themeClass.Nebula, [theme]);

  async function loadAll() {
    const [cfg, docs, old] = await Promise.all([
      fetch(`${API}/config`).then(r => r.json()),
      fetch(`${API}/documents`).then(r => r.json()),
      fetch(`${API}/history`).then(r => r.json()),
    ]);
    setConfig(cfg); setDocuments(docs); setHistory(old);
    setRole(cfg.workspace.role); setTheme(cfg.workspace.theme); setSystemPrompt(cfg.workspace.system_prompt || '');
  }

  useEffect(() => { loadAll().catch(() => setAnswer('Backend is not reachable. Start FastAPI on port 8000.')); }, []);

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    if (!e.target.files?.length) return;
    const form = new FormData();
    Array.from(e.target.files).forEach(file => form.append('files', file));
    setLoading(true); setAnswer('Uploading and reading documents...');
    const response = await fetch(`${API}/documents`, { method: 'POST', body: form });
    const uploaded = await response.json();
    await loadAll(); setLoading(false);
    const failed = uploaded.filter((doc: DocumentItem) => doc.status.startsWith('failed'));
    setAnswer(failed.length ? `Some files failed:\n${failed.map((doc: DocumentItem) => `- ${doc.filename}: ${doc.status}`).join('\n')}` : 'Documents uploaded and indexed. Click Summarize or ask a question.');
    e.target.value = '';
  }

  async function run(mode: 'chat' | 'summarize' | 'answer-questions') {
    setLoading(true);
    const label = mode === 'summarize' ? 'summary' : mode === 'answer-questions' ? 'answers' : 'answer';
    setAnswer(`Generating ${label}...`);
    const response = await fetch(`${API}/${mode}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt, top_k: 30 }) });
    const data = await response.json();
    setAnswer(data.answer || data.summary || 'No response was generated.');
    await loadAll(); setLoading(false);
  }

  async function saveSettings() {
    const response = await fetch(`${API}/settings`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ role, theme, system_prompt: systemPrompt }) });
    const updated = await response.json();
    setRole(updated.role); setTheme(updated.theme); setSystemPrompt(updated.system_prompt || '');
    setAnswer('Settings saved. Theme and role are active for future responses.');
  }

  async function removeHistory(id?: number) {
    await fetch(`${API}/history${id ? `/${id}` : ''}`, { method: 'DELETE' });
    await loadAll();
  }

  async function removeDocument(id: number) {
    await fetch(`${API}/documents/${id}`, { method: 'DELETE' });
    await loadAll();
  }

  return <main className={`app ${appTheme}`}>
    <aside className="sidebar">
      <h1><BookOpen /> OmniRAG</h1>
      {['Chat', 'History', 'Settings'].map(item => <button key={item} className={active === item ? 'nav active' : 'nav'} onClick={() => setActive(item)}>{item === 'Chat' ? <MessageSquare /> : item === 'History' ? <FileText /> : <Settings />}{item}</button>)}
      <label className="upload"><Upload /> Upload PDF / PPTX / Docs<input type="file" multiple onChange={upload} /></label>
      <div className="doc-list"><h3>Documents</h3>{documents.length === 0 && <p>No documents uploaded.</p>}{documents.map(doc => <div className="doc" key={doc.id}><span>{doc.filename}<small>{doc.status} · {doc.chunks} chunks</small></span><button onClick={() => removeDocument(doc.id)}><Trash2 /></button></div>)}</div>
    </aside>
    <section className="content">
      <header className="hero"><span>Simple document chat and summarizer</span><h2>Upload. Summarize. Answer questions.</h2><p>No workspace switching. No unnecessary tools. Focused on clean summaries and accurate answers from your uploaded content.</p></header>
      {active === 'Chat' && <div className="panel"><textarea value={prompt} onChange={e => setPrompt(e.target.value)} placeholder="Ask a question or request a summary..." /><div className="actions"><button disabled={loading} onClick={() => run('summarize')}>Summarize</button><button disabled={loading} onClick={() => run('answer-questions')}>Answer Questions</button><button disabled={loading} onClick={() => run('chat')}><Send /> Ask</button></div><article className="answer">{answer}</article></div>}
      {active === 'History' && <div className="panel"><div className="row"><h2>Chat History</h2><button onClick={() => removeHistory()}>Clear all</button></div>{history.length === 0 && <p>No chat history yet.</p>}{history.map(item => <article className="history" key={item.id}><div className="row"><strong>{item.kind}: {item.prompt}</strong><button onClick={() => removeHistory(item.id)}><Trash2 /></button></div><pre>{item.response}</pre></article>)}</div>}
      {active === 'Settings' && <div className="panel settings"><label>Theme <select value={theme} onChange={e => setTheme(e.target.value)}>{(config?.themes || []).map(name => <option key={name}>{name}</option>)}</select></label><label>Role <select value={role} onChange={e => setRole(e.target.value)}>{Object.keys(config?.roles || {}).map(name => <option key={name}>{name}</option>)}</select></label><label>Custom instructions <textarea value={systemPrompt} onChange={e => setSystemPrompt(e.target.value)} /></label><button onClick={saveSettings}><Palette /> Save Settings</button></div>}
    </section>
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
