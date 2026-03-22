'use client';

import { useState, useRef, useEffect } from 'react';
import { X, Send, Loader2, MessageSquare, Clock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useRecruiterQuery, useQueryHistory } from '@/hooks/useEvaluations';
import { QueryHistoryItem } from '@/types';
import { formatRelativeTime } from '@/lib/utils';

const EXAMPLE_QUERIES = [
  'Who is the best candidate overall?',
  'Which candidates have Python experience?',
  'Who has the most relevant project experience?',
  'Compare top 3 candidates briefly',
  'Which candidates are overqualified?',
];

interface RecruiterQueryProps {
  projectId: string;
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function RecruiterQuery({ projectId, isOpen, onClose }: RecruiterQueryProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const queryMutation = useRecruiterQuery();
  const { data: history } = useQueryHistory(projectId);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const sendMessage = async (question: string) => {
    if (!question.trim()) return;
    setInput('');

    const userMsg: Message = {
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const res = await queryMutation.mutateAsync({
        question,
        project_id: projectId,
      });
      const assistantMsg: Message = {
        role: 'assistant',
        content: res.answer,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errMsg: Message = {
        role: 'assistant',
        content: 'Sorry, I could not process that query. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 h-full w-96 bg-white border-l border-gray-200 shadow-xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 bg-indigo-600">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-white" />
          <span className="font-semibold text-white">Ask AI about Candidates</span>
        </div>
        <button onClick={onClose} className="text-white/80 hover:text-white transition-colors">
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="space-y-3">
            <p className="text-sm text-gray-500 text-center">
              Ask me anything about the candidates in this project.
            </p>
            <div className="space-y-2">
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">
                Example queries
              </p>
              {EXAMPLE_QUERIES.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="w-full text-left px-3 py-2 text-sm text-indigo-700 bg-indigo-50 border border-indigo-100 rounded-lg hover:bg-indigo-100 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>

            {history && history.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider flex items-center gap-1">
                  <Clock className="w-3 h-3" />
                  Recent Queries
                </p>
                {history.slice(0, 3).map((item: QueryHistoryItem) => (
                  <div key={item.id} className="px-3 py-2 bg-gray-50 rounded-lg">
                    <p className="text-xs font-medium text-gray-700">{item.question}</p>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{item.answer}</p>
                    <p className="text-xs text-gray-400 mt-1">{formatRelativeTime(item.created_at)}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white rounded-br-sm'
                  : 'bg-gray-100 text-gray-800 rounded-bl-sm'
              }`}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {queryMutation.isPending && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-2xl rounded-bl-sm px-4 py-3">
              <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage(input);
              }
            }}
            placeholder="Ask about candidates..."
            className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <Button
            size="icon"
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || queryMutation.isPending}
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
