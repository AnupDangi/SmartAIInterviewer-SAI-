import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, InterviewSession } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatMessage } from "@/components/ChatMessage";
import CodeEditor from "@/components/CodeEditor";
import ControlBar from "@/components/ControlBar";
import { Send, Loader2, Bot, ChevronRight, ChevronLeft } from "lucide-react";
import { toast } from "sonner";

interface Message {
  id: string;
  role: "ai" | "user";
  content: string;
  feedback?: string | null;
  timestamp: string;
}

const InterviewPage = () => {
  const { id: interviewId } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // State
  const [userMessage, setUserMessage] = useState("");
  const [started, setStarted] = useState(false);
  const [openingQuestion, setOpeningQuestion] = useState<string | null>(null);
  const [sessionRunId, setSessionRunId] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [durationMinutes, setDurationMinutes] = useState(30);

  const [summary, setSummary] = useState<string | null>(null);

  // UI State
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOn, setIsVideoOn] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(true);
  const [isCodeOpen, setIsCodeOpen] = useState(false);

  const handleEndCall = async () => {
    try {
      const token = await getToken();
      const response = await api.endInterview(interviewId!, token || undefined, sessionRunId || undefined);
      if (response && response.summary) {
        setSummary(response.summary);
        toast.success("Interview ended. Summary generated.");
      } else {
        toast.success("Interview ended");
        navigate("/dashboard");
      }
    } catch (error) {
      console.error("Failed to end interview:", error);
      navigate("/dashboard");
    }
  };

  // Start interview mutation
  const startInterviewMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      return api.startInterview(interviewId!, token || undefined);
    },
    onSuccess: (data) => {
      setOpeningQuestion(data.opening_question);
      setSessionRunId(data.session_run_id);
      setStarted(true);
      toast.success("Interview started!");
      queryClient.setQueryData(["interview-sessions", interviewId], []);
    },
    onError: (error) => {
      toast.error("Failed to start interview", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  // Check for existing active session run on mount
  const { data: latestSession, isLoading: isLoadingLatest } = useQuery({
    queryKey: ["interview-latest-session", interviewId],
    queryFn: async () => {
      const token = await getToken();
      return api.getLatestSession(interviewId!, token || undefined);
    },
    enabled: !!interviewId && !started,
  });

  // Initialize from existing session if available
  useEffect(() => {
    if (isLoadingLatest) return;

    if (latestSession) {
      // Check if the last session was ended
      if (latestSession.user_message === "[SESSION_ENDED]") {
        // Start a new run
        if (!started && !startInterviewMutation.isPending) {
          startInterviewMutation.mutate();
        }
      } else if (latestSession.session_run_id) {
        // Resume existing run
        setSessionRunId(latestSession.session_run_id);
        setStarted(true);
      }
    } else if (!started && !startInterviewMutation.isPending) {
      // No history at all, start new
      startInterviewMutation.mutate();
    }
  }, [latestSession, isLoadingLatest, interviewId, started, startInterviewMutation]);

  // Fetch interview details for duration
  const { data: interview } = useQuery({
    queryKey: ["interview", interviewId],
    queryFn: async () => {
      const token = await getToken();
      return api.getInterview(interviewId!, token || undefined);
    },
    enabled: !!interviewId,
  });

  useEffect(() => {
    if (interview) {
      setDurationMinutes(interview.duration_minutes);
    }
  }, [interview]);

  // Load conversation history for current session run
  const { data: sessions = [], isLoading: isLoadingHistory } = useQuery({
    queryKey: ["interview-sessions", interviewId, sessionRunId],
    queryFn: async () => {
      const token = await getToken();
      return api.getInterviewSessions(interviewId!, token || undefined, sessionRunId || undefined);
    },
    enabled: !!interviewId && started && !!sessionRunId,
  });

  // Timer logic
  useEffect(() => {
    if (!started || !sessionRunId) return;

    // Find the start time from the sessions if available
    const startSession = sessions.find(s => s.user_message === "[INTERVIEW_STARTED]");
    let startTime = Date.now();

    if (startSession) {
      startTime = new Date(startSession.created_at).getTime();
    } else if (elapsedTime > 0) {
      // If we have elapsed time but no start session yet (rare), estimate start time
      startTime = Date.now() - (elapsedTime * 1000);
    }

    const updateTimer = () => {
      const now = Date.now();
      const secondsElapsed = Math.floor((now - startTime) / 1000);

      setElapsedTime(secondsElapsed);

      // Auto-end if time exceeded
      if (secondsElapsed >= durationMinutes * 60) {
        handleEndCall();
      }
    };

    // Initial update
    updateTimer();

    const timer = setInterval(updateTimer, 1000);

    return () => clearInterval(timer);
  }, [started, durationMinutes, sessions, sessionRunId]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  // Convert sessions to messages
  const messages: Message[] = [];

  const isOpeningQuestionInSessions = sessions.some(
    (s) => s.user_message === "[INTERVIEW_STARTED]" && s.ai_message === openingQuestion
  );

  if (openingQuestion && sessions.length === 0 && !isOpeningQuestionInSessions) {
    messages.push({
      id: "opening",
      role: "ai",
      content: openingQuestion,
      timestamp: new Date().toISOString(),
    });
  }

  sessions.forEach((session: InterviewSession) => {
    const isOpeningSession = session.user_message === "[INTERVIEW_STARTED]";

    // For opening session, only show AI message (the opening question)
    if (isOpeningSession) {
      messages.push({
        id: session.id,
        role: "ai",
        content: session.ai_message,
        feedback: session.feedback,
        timestamp: session.created_at,
      });
    } else {
      // For all other sessions: show user message FIRST, then AI response
      // This creates the proper flow: User answers → AI responds with next question
      messages.push({
        id: `${session.id}-user`,
        role: "user",
        content: session.user_message,
        timestamp: session.created_at,
      });

      messages.push({
        id: session.id,
        role: "ai",
        content: session.ai_message,
        feedback: session.feedback,
        timestamp: session.created_at,
      });
    }
  });

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, openingQuestion]);

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const token = await getToken();
      return api.sendMessage(interviewId!, message, token || undefined, sessionRunId || undefined);
    },
    onSuccess: (data) => {
      setUserMessage("");
      queryClient.invalidateQueries({ queryKey: ["interview-sessions", interviewId, sessionRunId] });
    },
    onError: (error) => {
      toast.error("Failed to send message", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userMessage.trim() || sendMessageMutation.isPending) return;
    sendMessageMutation.mutate(userMessage.trim());
  };

  const handleCodeSubmit = (code: string, language: string) => {
    const formattedMessage = `I have written the following ${language} code:\n\n\`\`\`${language}\n${code}\n\`\`\``;
    sendMessageMutation.mutate(formattedMessage);
    setIsCodeOpen(false);
    toast.success("Code submitted successfully!");
  };

  if (!interviewId) return null;

  if (summary) {
    return (
      <div className="h-screen w-screen bg-zinc-950 flex items-center justify-center p-4 overflow-y-auto">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 max-w-3xl w-full shadow-2xl">
          <h2 className="text-2xl font-bold mb-6 text-white">Interview Summary</h2>
          <div className="prose prose-invert max-w-none mb-8 whitespace-pre-wrap">
            {summary}
          </div>
          <Button
            onClick={() => navigate("/dashboard")}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white"
          >
            Return to Dashboard
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-screen bg-zinc-950 flex flex-col overflow-hidden text-zinc-100">
      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden relative">

        {/* Main Stage (Chat or Code) */}
        <div className="flex-1 flex flex-col relative p-4 md:p-6">
          {isCodeOpen ? (
            <div className="flex-1 rounded-xl overflow-hidden border border-zinc-800 shadow-2xl bg-[#1e1e1e]">
              <CodeEditor
                isOpen={true}
                onClose={() => setIsCodeOpen(false)}
                onSubmit={handleCodeSubmit}
              />
            </div>
          ) : (
            <div className="flex-1 flex flex-col bg-zinc-900/50 rounded-xl border border-zinc-800/50 overflow-hidden backdrop-blur-sm">
              {/* Chat Header */}
              <div className="p-4 border-b border-zinc-800 flex items-center justify-between bg-zinc-900/80">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-600 to-purple-700 flex items-center justify-center shadow-lg">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="font-semibold text-lg">SAI</h2>
                    <div className="flex items-center gap-2 text-xs text-zinc-400">
                      <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                      Online
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-sm font-mono bg-zinc-800 px-3 py-1 rounded-md border border-zinc-700">
                    {formatTime(elapsedTime)} / {durationMinutes}:00
                  </div>
                </div>
              </div>

              {/* Chat Messages */}
              <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
                {isLoadingLatest || startInterviewMutation.isPending ? (
                  <div className="flex items-center justify-center h-full text-zinc-500 gap-2">
                    <Loader2 className="w-5 h-5 animate-spin" />
                    <span className="text-sm">Connecting to session...</span>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-zinc-500 text-sm">
                    No messages yet
                  </div>
                ) : (
                  <>
                    {messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        role={message.role}
                        content={message.content}
                        feedback={message.feedback}
                        timestamp={message.timestamp}
                      />
                    ))}
                    {sendMessageMutation.isPending && (
                      <div className="flex gap-3 mb-4 animate-in fade-in slide-in-from-bottom-2">
                        <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-zinc-400" />
                        </div>
                        <div className="bg-zinc-800 rounded-lg px-4 py-3">
                          <Loader2 className="w-4 h-4 animate-spin text-zinc-400" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Chat Input */}
              <div className="p-4 md:p-6 border-t border-zinc-800 bg-zinc-900/80">
                <form onSubmit={handleSendMessage} className="flex gap-3 max-w-4xl mx-auto">
                  <Input
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    placeholder="Type your answer..."
                    disabled={!started || sendMessageMutation.isPending}
                    className="bg-zinc-800 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-blue-600 h-12 text-base shadow-inner"
                  />
                  <Button
                    type="submit"
                    size="icon"
                    disabled={!started || !userMessage.trim() || sendMessageMutation.isPending}
                    className="h-12 w-12 bg-blue-600 hover:bg-blue-700 text-white shadow-lg shadow-blue-900/20"
                  >
                    <Send className="w-5 h-5" />
                  </Button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Control Bar */}
      <ControlBar
        isMuted={isMuted}
        isVideoOn={isVideoOn}
        isChatOpen={true} // Always "open" in this view
        isCodeOpen={isCodeOpen}
        onToggleMute={() => setIsMuted(!isMuted)}
        onToggleVideo={() => setIsVideoOn(!isVideoOn)}
        onToggleChat={() => { }} // No-op in this layout
        onToggleCode={() => setIsCodeOpen(!isCodeOpen)}
        onEndCall={handleEndCall}
        hideVideoControls={true} // New prop to hide audio/video controls
      />
    </div>
  );
};

export default InterviewPage;
