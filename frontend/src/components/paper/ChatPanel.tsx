import React, { useEffect, useRef, useState } from 'react';
import { Box, CircularProgress, IconButton, Paper, Stack, TextField, Typography } from '@mui/material';
import CloseRoundedIcon from '@mui/icons-material/CloseRounded';
import SendRoundedIcon from '@mui/icons-material/SendRounded';
import { papersAPI } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatPanelProps {
  paperId: string;
  token: string;
  onClose: () => void;
}

const STARTER_PROMPTS = [
  'Explain the key equation in plain English',
  'Does the evaluation actually prove the main claim?',
  'What would I need to reproduce this?',
  'What does this paper assume the reader already knows?',
];

export const ChatPanel: React.FC<ChatPanelProps> = ({ paperId, token, onClose }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof bottomRef.current?.scrollIntoView === 'function') {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const send = async (text: string) => {
    if (!text.trim() || loading) return;
    const userMessage: Message = { role: 'user', content: text.trim() };
    const next = [...messages, userMessage];
    setMessages(next);
    setInput('');
    setLoading(true);
    try {
      const { reply } = await papersAPI.chat(paperId, next, token);
      setMessages([...next, { role: 'assistant', content: reply }]);
    } catch {
      setMessages([...next, { role: 'assistant', content: 'Something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper
      sx={{
        p: { xs: 2, md: 2.5 },
        borderRadius: 6,
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - 168px)',
        minHeight: 480,
      }}
    >
      {/* Header */}
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 1.5 }}>
        <Typography variant="h6">Chat with paper</Typography>
        <IconButton aria-label="close chat" size="small" onClick={onClose}>
          <CloseRoundedIcon fontSize="small" />
        </IconButton>
      </Stack>

      {/* Message list */}
      <Box sx={{ flex: 1, overflowY: 'auto', mb: 1.5 }}>
        {messages.length === 0 ? (
          <Stack spacing={1} sx={{ pt: 1 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', letterSpacing: 1 }}>
              Try one of these
            </Typography>
            {STARTER_PROMPTS.map((p) => (
              <Box
                key={p}
                component="button"
                onClick={() => send(p)}
                sx={{
                  textAlign: 'left',
                  p: 1.25,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 3,
                  cursor: 'pointer',
                  bgcolor: 'transparent',
                  fontFamily: 'inherit',
                  fontSize: 13,
                  color: 'text.primary',
                  '&:hover': { bgcolor: 'action.hover' },
                  width: '100%',
                }}
              >
                {p}
              </Box>
            ))}
          </Stack>
        ) : (
          <Stack spacing={1.25} sx={{ pt: 0.5 }}>
            {messages.map((msg, i) => (
              <Box
                key={i}
                sx={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '88%',
                  px: 1.75,
                  py: 1.25,
                  borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                  bgcolor: msg.role === 'user' ? 'primary.main' : 'action.hover',
                  color: msg.role === 'user' ? 'primary.contrastText' : 'text.primary',
                  border: '1px solid',
                  borderColor: msg.role === 'user' ? 'primary.main' : 'divider',
                }}
              >
                <Typography variant="body2" sx={{ lineHeight: 1.6 }}>{msg.content}</Typography>
              </Box>
            ))}
            {loading && (
              <Box sx={{ alignSelf: 'flex-start', px: 2, py: 1.25, bgcolor: 'action.hover', borderRadius: '14px 14px 14px 4px', border: '1px solid', borderColor: 'divider' }}>
                <CircularProgress size={14} />
              </Box>
            )}
            <div ref={bottomRef} />
          </Stack>
        )}
      </Box>

      {/* Input */}
      <Stack direction="row" spacing={1} alignItems="flex-end">
        <TextField
          fullWidth
          size="small"
          multiline
          maxRows={4}
          placeholder="Ask a question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              send(input);
            }
          }}
          disabled={loading}
        />
        <IconButton
          aria-label="send message"
          color="primary"
          onClick={() => send(input)}
          disabled={!input.trim() || loading}
          sx={{ border: '1px solid', borderColor: 'primary.main', borderRadius: 3 }}
        >
          <SendRoundedIcon fontSize="small" />
        </IconButton>
      </Stack>
      <Typography variant="caption" color="text.secondary" align="center" sx={{ mt: 0.75 }}>
        Rate-limited · 20 messages / min
      </Typography>
    </Paper>
  );
};
