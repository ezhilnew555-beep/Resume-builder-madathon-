import React, { useState, useEffect, useRef } from 'react';
import {
  Sparkles,
  Send,
  X,
  Bot,
  User,
  Shield,
  RefreshCw,
  ChevronRight,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { apiService } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import type { LiveAssistantChatMessage } from '../../types';

interface AIAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  resumeId?: string | null;
  matchId?: string | null;
  verificationId?: string | null;
}

export const AIAssistantDrawer: React.FC<AIAssistantDrawerProps> = ({
  isOpen,
  onClose,
  resumeId,
  matchId,
  verificationId,
}) => {
  const { session } = useAuth();
  const token = session?.access_token || null;

  const [messages, setMessages] = useState<LiveAssistantChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! I am your CareerLens Career Assistant. I am grounded directly in your uploaded resume diagnostics, ATS score breakdown, and job matches. Ask me anything about your report findings, bullet rewrites, or skill gap strategies!',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [referencedReports, setReferencedReports] = useState<string[]>([]);
  const [suggestedFollowups, setSuggestedFollowups] = useState<string[]>([
    'How do I add quantified metrics to my bullets?',
    'What are my highest priority missing qualifications?',
    'How does CareerLens calculate my ATS score?',
  ]);
  const [lastProvider, setLastProvider] = useState<string>('deterministic_engine');
  const [isAiGenerated, setIsAiGenerated] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen]);

  if (!isOpen) return null;

  const handleSendMessage = async (queryText?: string) => {
    const textToSend = (queryText || inputMessage).trim();
    if (!textToSend || loading) return;

    const userMsg: LiveAssistantChatMessage = { role: 'user', content: textToSend };
    const updatedHistory = [...messages, userMsg];
    setMessages(updatedHistory);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await apiService.sendAssistantChatLive(
        {
          message: textToSend,
          history: updatedHistory.slice(-6),
          resume_id: resumeId || null,
          match_id: matchId || null,
          verification_id: verificationId || null,
        },
        token
      );

      setMessages((prev) => [...prev, { role: 'assistant', content: response.reply }]);
      setReferencedReports(response.referenced_reports || []);
      setSuggestedFollowups(response.suggested_followups || []);
      setLastProvider(response.provider);
      setIsAiGenerated(response.is_ai_generated);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Unable to retrieve advice at this moment: ${err.message || 'Network error'}. Please try again shortly.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end animate-fadeIn">
      <div className="w-full max-w-lg bg-white h-full shadow-2xl flex flex-col border-l border-slate-200">
        {/* Header */}
        <div className="p-4 border-b border-slate-200 bg-slate-900 text-white flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-indigo-500/20 border border-indigo-400/40 flex items-center justify-center text-indigo-300">
              <Bot className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-semibold text-white">CareerLens AI Assistant</h3>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/30 text-indigo-200 font-mono">
                  Phase 8
                </span>
              </div>
              <p className="text-xs text-slate-400 flex items-center mt-0.5">
                <Shield className="w-3 h-3 text-emerald-400 mr-1" />
                Grounded strictly in your reports
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Context bar */}
        <div className="bg-slate-50 border-b border-slate-200 px-4 py-2 text-xs text-slate-600 flex items-center justify-between flex-wrap gap-1">
          <div className="flex items-center space-x-1.5">
            <span className="font-medium text-slate-700">Active Context:</span>
            {resumeId && (
              <span className="bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded text-[11px] font-mono">
                Resume: {resumeId.slice(0, 8)}
              </span>
            )}
            {matchId && (
              <span className="bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded text-[11px] font-mono">
                Match: {matchId.slice(0, 8)}
              </span>
            )}
            {!resumeId && !matchId && (
              <span className="text-slate-500 italic">General Career Advisory</span>
            )}
            {referencedReports.map((r, i) => (
              <span key={i} className="bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded text-[10px]">
                {r}
              </span>
            ))}
          </div>
          <span className="text-[10px] text-slate-400">
            Engine: {lastProvider.replace('_', ' ')}
          </span>
        </div>

        {/* Message Thread */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-slate-50/50">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`flex items-start space-x-2.5 ${
                msg.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-indigo-600 text-white'
                }`}
              >
                {msg.role === 'user' ? (
                  <User className="w-4 h-4" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
              </div>
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white rounded-tr-none'
                    : 'bg-white border border-slate-200 text-slate-800 shadow-xs rounded-tl-none'
                }`}
              >
                <div className="whitespace-pre-line">{msg.content}</div>
                {msg.role === 'assistant' && index === messages.length - 1 && (
                  <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
                    <span className="flex items-center">
                      <CheckCircle2 className="w-3 h-3 text-emerald-500 mr-1" />
                      {isAiGenerated ? 'Generated via AI' : 'Deterministic Grounded Engine'}
                    </span>
                    <span>Provider: {lastProvider}</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-start space-x-2.5">
              <div className="w-7 h-7 rounded-full bg-indigo-600 text-white flex items-center justify-center shrink-0">
                <Sparkles className="w-4 h-4 animate-spin" />
              </div>
              <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none px-4 py-3 text-xs text-slate-500 flex items-center space-x-2 shadow-xs">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-indigo-600" />
                <span>Consulting your diagnostic reports...</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Followup suggestions */}
        {suggestedFollowups.length > 0 && !loading && (
          <div className="p-3 bg-white border-t border-slate-100">
            <p className="text-[11px] font-medium text-slate-500 mb-1.5 flex items-center">
              <Info className="w-3 h-3 text-indigo-500 mr-1" />
              Suggested Follow-ups:
            </p>
            <div className="flex flex-wrap gap-1.5">
              {suggestedFollowups.map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => handleSendMessage(suggestion)}
                  className="text-[11px] text-left bg-slate-100 hover:bg-indigo-50 hover:text-indigo-700 text-slate-700 px-2.5 py-1 rounded-full border border-slate-200 transition-colors flex items-center"
                >
                  <span>{suggestion}</span>
                  <ChevronRight className="w-3 h-3 ml-1 shrink-0 text-slate-400" />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input box */}
        <div className="p-3 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center space-x-2"
          >
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Ask about your score, bullet points, or job match..."
              disabled={loading}
              className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !inputMessage.trim()}
              className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white rounded-xl transition-colors shadow-xs shrink-0"
              title="Send question"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
          <div className="mt-1.5 flex items-center justify-between text-[10px] text-slate-400">
            <span>PII is automatically redacted before AI evaluation</span>
            <span>Deterministic scores remain immutable</span>
          </div>
        </div>
      </div>
    </div>
  );
};
