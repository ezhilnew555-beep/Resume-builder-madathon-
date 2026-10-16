import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  UploadCloud,
  FileText,
  FileCheck,
  X,
  AlertCircle,
  CheckCircle2,
  ArrowRight,
  ShieldAlert,
  RefreshCw,
  FileCode,
  Layers,
  Sparkles,
  Info,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Badge } from '../components/common/Badge';
import { apiService } from '../services/api';
import type { LiveResumeUploadResponse, LiveResumeStatus } from '../types';
import { useAuth } from '../context/AuthContext';

export const ResumeUploadPage: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { user, getAccessToken } = useAuth();

  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<LiveResumeUploadResponse | null>(null);
  const [serviceStatus, setServiceStatus] = useState<LiveResumeStatus | null>(null);

  const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

  useEffect(() => {
    async function loadStatus() {
      try {
        const status = await apiService.fetchResumeStatus();
        setServiceStatus(status);
      } catch (err) {
        console.warn('Could not query resume parser backend status:', err);
      }
    }
    loadStatus();
  }, []);

  const validateAndSetFile = (file: File) => {
    setValidationError(null);
    setUploadResult(null);

    const validExtensions = ['.pdf', '.docx'];
    const fileName = file.name.toLowerCase();
    const isValidExtension = validExtensions.some((ext) => fileName.endsWith(ext));

    if (!isValidExtension) {
      setValidationError('Unsupported format. Please upload a standard PDF (.pdf) or Word document (.docx).');
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setValidationError(
        `File size (${(file.size / (1024 * 1024)).toFixed(2)} MB) exceeds the 5 MB limit. Please select a smaller document.`
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadAndExtract = async () => {
    if (!selectedFile) return;
    setIsUploading(true);
    setValidationError(null);

    try {
      const token = user ? await getAccessToken() : null;
      const res = await apiService.uploadResumeFileLive(selectedFile, token);
      setUploadResult(res);
      // Persist latest resume ID in session storage so other pages can link
      sessionStorage.setItem('latest_resume_id', res.resume_id);
      sessionStorage.setItem('latest_resume_filename', res.filename);
    } catch (err: any) {
      setValidationError(err?.message || 'Upload failed. Please check document formatting and try again.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="success" size="sm">Extracted Successfully</Badge>;
      case 'partial':
        return <Badge variant="warning" size="sm">Partial Extraction</Badge>;
      case 'ocr_unavailable':
        return <Badge variant="warning" size="sm">OCR Setup Required</Badge>;
      default:
        return <Badge variant="danger" size="sm">Extraction Failed</Badge>;
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Live Engine Diagnostic Bar */}
      <div className="p-3.5 bg-slate-900 text-white rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-xs">
        <div className="flex items-center space-x-2.5">
          <Sparkles className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>
            <strong>Phase 4 Pipeline:</strong> PyMuPDF vector parser & python-docx engine active.
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            PDF & DOCX Active
          </span>
          <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${
            serviceStatus?.ocr_fallback_available
              ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
              : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
          }`}>
            OCR: {serviceStatus?.ocr_fallback_available ? 'Ready' : 'Setup Required'}
          </span>
        </div>
      </div>

      <div className="text-left">
        <h2 className="text-xl sm:text-2xl font-bold text-slate-900 tracking-tight">
          Secure Resume Upload & Text Extraction
        </h2>
        <p className="text-slate-600 text-xs sm:text-sm mt-1">
          Upload your resume in PDF or DOCX format. CareerLens validates file signatures, performs paragraph & section segmentation, and prepares structured data for ATS analysis.
        </p>
      </div>

      {/* Upload Dropzone Container */}
      <Card padding="lg">
        {!selectedFile ? (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-2xl p-8 sm:p-12 text-center transition-all duration-150 flex flex-col items-center justify-center cursor-pointer ${
              dragActive
                ? 'border-indigo-600 bg-indigo-50/60'
                : 'border-slate-200 hover:border-indigo-300 hover:bg-slate-50/50 bg-slate-50/20'
            }`}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              onChange={handleChange}
              className="hidden"
            />

            <div className="w-14 h-14 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 shadow-xs">
              <UploadCloud className="w-7 h-7" />
            </div>

            <h3 className="text-sm sm:text-base font-bold text-slate-800">
              Drag & drop your resume file here, or{' '}
              <span className="text-indigo-600 hover:underline">browse files</span>
            </h3>

            <p className="text-xs text-slate-500 mt-1.5 max-w-md">
              Supports standard <strong>PDF (.pdf)</strong> and <strong>Microsoft Word (.docx)</strong> up to 5 MB.
            </p>

            <div className="flex flex-wrap items-center justify-center gap-2 mt-4">
              <Badge variant="outline" size="sm">PDF Document (PyMuPDF)</Badge>
              <Badge variant="outline" size="sm">DOCX Document (python-docx)</Badge>
              <Badge variant="outline" size="sm">Max 5 MB</Badge>
              <Badge variant="outline" size="sm">Strict Signature Checks</Badge>
            </div>
          </div>
        ) : (
          /* Staged & Extracted File Information Card */
          <div className="space-y-4">
            <div className="p-4 sm:p-5 rounded-xl border border-indigo-200 bg-indigo-50/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3.5">
                <div className="w-12 h-12 rounded-xl bg-indigo-600 text-white flex items-center justify-center shrink-0 shadow-sm">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-slate-900 break-all">{selectedFile.name}</h4>
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 mt-0.5">
                    <span className="font-mono">{formatFileSize(selectedFile.size)}</span>
                    <span>•</span>
                    <span className="uppercase text-[10px] font-semibold tracking-wider text-indigo-700 bg-indigo-100 px-1.5 py-0.2 rounded">
                      {selectedFile.name.endsWith('.pdf') ? 'PDF Document' : 'DOCX Document'}
                    </span>
                    {uploadResult && (
                      <>
                        <span>•</span>
                        {getStatusBadge(uploadResult.extraction_status)}
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 self-end sm:self-center">
                <Button
                  size="sm"
                  variant="outline"
                  icon={<RefreshCw className="w-3.5 h-3.5" />}
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                >
                  Replace
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  onChange={handleChange}
                  className="hidden"
                />
                <Button
                  size="sm"
                  variant="ghost"
                  icon={<X className="w-3.5 h-3.5 text-rose-600" />}
                  onClick={handleRemoveFile}
                  disabled={isUploading}
                >
                  Remove
                </Button>
              </div>
            </div>

            {/* Action Buttons: Upload or View Extracted Results */}
            {!uploadResult ? (
              <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-xs text-slate-500">
                  Ready for cryptographic validation, PyMuPDF/python-docx parsing, and section segmentation.
                </p>
                <Button
                  variant="primary"
                  size="md"
                  isLoading={isUploading}
                  icon={<UploadCloud className="w-4 h-4" />}
                  onClick={handleUploadAndExtract}
                >
                  Upload & Extract Text
                </Button>
              </div>
            ) : (
              /* Success & Extraction Report Card */
              <div className="p-4 sm:p-5 rounded-xl border border-emerald-200 bg-emerald-50/50 space-y-4">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-emerald-950">
                      Extraction Complete — {uploadResult.parser_method}
                    </h4>
                    <p className="text-xs text-emerald-900/80">
                      {uploadResult.status_message}
                    </p>
                  </div>
                </div>

                {/* Extraction Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                  <div className="p-3 bg-white rounded-lg border border-emerald-200/80">
                    <p className="text-[11px] font-medium text-slate-500">Pages</p>
                    <p className="text-base font-bold text-slate-900 font-mono mt-0.5">
                      {uploadResult.page_count}
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-emerald-200/80">
                    <p className="text-[11px] font-medium text-slate-500">Words Extracted</p>
                    <p className="text-base font-bold text-slate-900 font-mono mt-0.5">
                      {uploadResult.word_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-emerald-200/80">
                    <p className="text-[11px] font-medium text-slate-500">Characters</p>
                    <p className="text-base font-bold text-slate-900 font-mono mt-0.5">
                      {uploadResult.character_count.toLocaleString()}
                    </p>
                  </div>
                  <div className="p-3 bg-white rounded-lg border border-emerald-200/80">
                    <p className="text-[11px] font-medium text-slate-500">Sections Detected</p>
                    <p className="text-base font-bold text-slate-900 font-mono mt-0.5">
                      {uploadResult.detected_sections.length}
                    </p>
                  </div>
                </div>

                {/* Detected Sections Badges */}
                {uploadResult.detected_sections.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-indigo-600" /> Detected Structural Sections:
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {uploadResult.detected_sections.map((sectionKey) => (
                        <span
                          key={sectionKey}
                          className="px-2.5 py-1 rounded-md text-xs font-semibold bg-white border border-indigo-200 text-indigo-800 shadow-2xs capitalize"
                        >
                          {sectionKey.replace('_', ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Scanned / OCR guidance notice if needed */}
                {uploadResult.extraction_status === 'ocr_unavailable' && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
                    <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-amber-950">OCR Engine Prerequisite</p>
                      <p className="mt-0.5">
                        This PDF contains flattened raster images rather than selectable vector text.
                        To parse scanned documents, install Tesseract OCR on the server or export a standard vector PDF from Word / Google Docs.
                      </p>
                    </div>
                  </div>
                )}

                {/* Next Step CTA */}
                <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-emerald-200/60">
                  <span className="text-xs text-slate-600">
                    Extracted text and sections ready for inspection and ATS rule auditing.
                  </span>
                  <Button
                    size="sm"
                    variant="primary"
                    icon={<ArrowRight className="w-3.5 h-3.5" />}
                    iconPosition="right"
                    onClick={() => navigate(`/review?resumeId=${uploadResult.resume_id}`)}
                  >
                    View Extracted Sections & Review
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Validation Error Banner */}
        {validationError && (
          <div className="mt-4 p-3.5 rounded-xl border border-rose-200 bg-rose-50 text-rose-900 flex items-start justify-between gap-3 text-xs">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-rose-950">Upload & Extraction Rejected</p>
                <p className="mt-0.5">{validationError}</p>
              </div>
            </div>
            <Button
              size="sm"
              variant="outline"
              onClick={handleUploadAndExtract}
              icon={<RefreshCw className="w-3 h-3" />}
            >
              Retry
            </Button>
          </div>
        )}
      </Card>

      {/* Guidelines & Pre-check Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-800">
            <FileCode className="w-4 h-4 text-indigo-600" />
            Vector PDF Text Extraction
          </div>
          <p className="text-[11px] text-slate-500 leading-normal">
            Directly extracts vector font streams using PyMuPDF. Preserves paragraph boundaries, indentation, and header hierarchies without data loss.
          </p>
        </Card>

        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-800">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            Tesseract OCR Fallback
          </div>
          <p className="text-[11px] text-slate-500 leading-normal">
            Scanned or flattened image PDFs are automatically identified. If Tesseract is present on the host, optical character recognition is performed up to 5 pages.
          </p>
        </Card>

        <Card padding="sm">
          <div className="flex items-center gap-2 mb-1.5 text-xs font-semibold text-slate-800">
            <FileCheck className="w-4 h-4 text-emerald-600" />
            OpenXML DOCX Parsing
          </div>
          <p className="text-[11px] text-slate-500 leading-normal">
            Parses Word documents (.docx) via python-docx, extracting multi-column tables, skills matrices, and bullet hierarchies while blocking embedded macros.
          </p>
        </Card>
      </div>
    </div>
  );
};
