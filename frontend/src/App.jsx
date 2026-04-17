import { useState, useRef, useEffect } from 'react'

const PROGRESS_STEPS = [
{ message: 'Analisando documento...' },
{ message: 'Extraindo URLs, QR codes e CRMs...' },
{ message: 'Executando RPA no navegador...' },
{ message: 'Aguardando resposta da página de validação...' },
{ message: 'Processando resultado com IA...' },
]

const STEP_DURATIONS = [2500, 4000, 6000, 8000, Infinity]

function statusClass(status) {
if (!status) return 'inconclusivo'
return status
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/\s+/g, '-')
}

function StatusBadge({ status }) {
return (
    <div className={`status-badge status-${statusClass(status)}`}>
    <span className="status-icon">
        {status === 'VÁLIDO' ? '✓' : status === 'INVÁLIDO' ? '✗' : '?'}
    </span>
    {status}
    </div>
)
}

export default function App() {
const [appState, setAppState] = useState('idle')
const [file, setFile] = useState(null)
const [dragOver, setDragOver] = useState(false)
const [stepIndex, setStepIndex] = useState(0)
const [result, setResult] = useState(null)
const [errorMsg, setErrorMsg] = useState(null)
const fileInputRef = useRef()
const timerRef = useRef()

useEffect(() => {
    if (appState === 'processing') {
    setStepIndex(0)
    scheduleNext(0)
    }
    return () => clearTimeout(timerRef.current)
}, [appState])

function scheduleNext(idx) {
    if (idx >= STEP_DURATIONS.length - 1) return
    timerRef.current = setTimeout(() => {
    setStepIndex(idx + 1)
    scheduleNext(idx + 1)
    }, STEP_DURATIONS[idx])
}

function handleFile(f) {
    if (!f) return
    const allowed = ['application/pdf', 'image/jpeg', 'image/png']
    if (!allowed.includes(f.type)) {
    alert('Formato não suportado. Use PDF, JPG ou PNG.')
    return
    }
    setFile(f)
}

async function handleSubmit() {
    if (!file) return
    setAppState('processing')
    const formData = new FormData()
    formData.append('file', file)
    try {
    const res = await fetch('/validate', { method: 'POST', body: formData })
    clearTimeout(timerRef.current)
    if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Erro ao processar documento.')
    }
    setResult(await res.json())
    setAppState('done')
    } catch (e) {
    clearTimeout(timerRef.current)
    setErrorMsg(e.message)
    setAppState('error')
    }
}

function reset() {
    clearTimeout(timerRef.current)
    setAppState('idle'); setFile(null); setResult(null)
    setErrorMsg(null); setStepIndex(0)
}

return (
    <div className="app">
    <header className="app-header">
        <div className="header-content">
        <h1>Verificador de Assinaturas</h1>
        <p>Valide assinaturas digitais, CRMs e documentos autenticados automaticamente</p>
        </div>
    </header>
    <main className="app-main">

        {appState === 'idle' && (
        <div className="upload-section">
            <div
            className={`dropzone ${dragOver ? ' drag-over' : ''} ${file ? ' has-file' : ''}`}
            onClick={() => fileInputRef.current.click()}
            onDragOver={e => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={e => { e.preventDefault(); setDragOver(false); handleFile(e.dataTransfer.files[0]) }}
            >
            <input ref={fileInputRef} type="file" accept=".pdf,.jpg,.jpeg,.png"
                style={{ display: 'none' }} onChange={e => handleFile(e.target.files[0])} />
            {file ? (
                <><div className="file-thumb">📄</div>
                <p className="file-name">{file.name}</p>
                <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
                <p className="change-hint">Clique para trocar</p></>
            ) : (
                <><div className="upload-icon">⬆</div>
                <p className="dropzone-label">Arraste um arquivo ou <span className="link">clique para selecionar</span></p>
                <p className="dropzone-hint">PDF · JPG · PNG</p></>
            )}
            </div>
            {file && <button className="btn-primary" onClick={handleSubmit}>Validar Documento</button>}
        </div>
        )}

        {appState === 'processing' && (
        <div className="processing-section">
            <div className="spinner-ring" />
            <h2>Processando documento...</h2>
            <p className="file-label">{file?.name}</p>
            <ul className="steps-list">
            {PROGRESS_STEPS.map((step, i) => (
                <li key={i} className={`step ${i < stepIndex ? 'step-done' : i === stepIndex ? 'step-active' : 'step-pending'}`}>
                <span className="step-dot">
                    {i < stepIndex ? '✓' : i === stepIndex ? <span className="step-spinner" /> : '○'}
                </span>
                <span className="step-text">{step.message}</span>
                </li>
            ))}
            </ul>
        </div>
        )}

        {appState === 'done' && result && (
        <div className="result-section">
            <StatusBadge status={result.status_geral} />
            <div className="cards">
            {result.validacao_url && (
                <div className="card">
                <div className="card-header">
                    <h3>Validação por URL / QR Code</h3>
                    <StatusBadge status={result.validacao_url.status} />
                </div>
                <p><strong>URL validada:</strong> <a href={result.validacao_url.url_validada} target="_blank"
rel="noreferrer">{result.validacao_url.url_validada}</a></p>
                <p>{result.validacao_url.mensagem}</p>
                {result.validacao_url.screenshot && (
                    <div className="screenshot-wrap">
                    <p className="screenshot-label">Print da página de validação</p>
                    <img src={`data:image/png;base64,${result.validacao_url.screenshot}`} alt="Screenshot" className="screenshot"
/>
                    </div>
                )}
                </div>
            )}
            {result.validacao_crm && (
                <div className="card">
                <div className="card-header">
                    <h3>Validação de CRM</h3>
                    <StatusBadge status={result.validacao_crm.status} />
                </div>
                <p><strong>CRM:</strong> {result.validacao_crm.crm}</p>
                <p>{result.validacao_crm.mensagem}</p>
                {result.validacao_crm.dados?.nome && <p><strong>Profissional:</strong> {result.validacao_crm.dados.nome}</p>}
                {result.validacao_crm.dados?.uf   && <p><strong>Estado:</strong> {result.validacao_crm.dados.uf}</p>}
                </div>
            )}
            {result.validacao_govbr && (
                <div className="card">
                <div className="card-header">
                    <h3>Validação Gov.br / ICP-Brasil</h3>
                    <StatusBadge status={result.validacao_govbr.status} />
                </div>
                <p>{result.validacao_govbr.mensagem}</p>
                {result.validacao_govbr.screenshot && (
                    <div className="screenshot-wrap">
                    <p className="screenshot-label">Print da página de validação</p>
                    <img src={`data:image/png;base64,${result.validacao_govbr.screenshot}`} alt="Screenshot Gov.br"
className="screenshot" />
                    </div>
                )}
                </div>
            )}
            </div>
            <button className="btn-secondary" onClick={reset}>Validar outro documento</button>
        </div>
        )}

        {appState === 'error' && (
        <div className="error-section">
            <div className="error-icon">✗</div>
            <h2>Erro ao processar</h2>
            <p className="error-msg">{errorMsg}</p>
            <button className="btn-secondary" onClick={reset}>Tentar novamente</button>
        </div>
        )}

    </main>
    </div>
)
}