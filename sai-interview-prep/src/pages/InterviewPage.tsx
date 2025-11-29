import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useAuth } from "@clerk/clerk-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, InterviewSession } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ChatMessage } from "@/components/ChatMessage";
import { Send, ArrowLeft, Loader2, Clock, Bot } from "lucide-react";
import { toast } from "sonner";
import Header from "@/components/Header";

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
  const [userMessage, setUserMessage] = useState("");
  const [started, setStarted] = useState(false);
  const [openingQuestion, setOpeningQuestion] = useState<string | null>(null);
  const [sessionRunId, setSessionRunId] = useState<string | null>(null);  // Track current session run
  const [startTime] = useState<Date>(new Date());
  const [elapsedTime, setElapsedTime] = useState(0);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [openingQuestion]);

  // Timer effect
  useEffect(() => {
    if (!started) return;
    
    const interval = setInterval(() => {
      setElapsedTime(Math.floor((new Date().getTime() - startTime.getTime()) / 1000));
    }, 1000);

    return () => clearInterval(interval);
  }, [started, startTime]);

  // Format elapsed time
  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  // Start interview mutation
  const startInterviewMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      return api.startInterview(interviewId!, token || undefined);
    },
    onSuccess: (data) => {
      setOpeningQuestion(data.opening_question);
      setSessionRunId(data.session_run_id);  // Store the new session run ID
      setStarted(true);
      toast.success("Interview started!");
      // Clear any previous messages by invalidating the query
      queryClient.setQueryData(["interview-sessions", interviewId], []);
    },
    onError: (error) => {
      toast.error("Failed to start interview", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  // Load conversation history for current session run only
  const { data: sessions = [], isLoading: isLoadingHistory } = useQuery({
    queryKey: ["interview-sessions", interviewId, sessionRunId],
    queryFn: async () => {
      const token = await getToken();
      return api.getInterviewSessions(interviewId!, token || undefined, sessionRunId || undefined);
    },
    enabled: !!interviewId && started && !!sessionRunId,
  });

  // Convert sessions to messages
  const messages: Message[] = [];
  
  // Add opening question if available and no sessions yet
  if (openingQuestion && sessions.length === 0) {
    messages.push({
      id: "opening",
      role: "ai",
      content: openingQuestion,
      timestamp: new Date().toISOString(),
    });
  }

  // Add session messages (filter out placeholder messages)
  sessions.forEach((session: InterviewSession) => {
    // Skip placeholder messages from old sessions
    if (session.user_message === "[INTERVIEW_STARTED]") {
      return;
    }
    
    messages.push({
      id: session.id,
      role: "ai",
      content: session.ai_message,
      feedback: session.feedback,
      timestamp: session.created_at,
    });
    messages.push({
      id: `${session.id}-user`,
      role: "user",
      content: session.user_message,
      timestamp: session.created_at,
    });
  });

  // Send message mutation
  const sendMessageMutation = useMutation({
    mutationFn: async (message: string) => {
      const token = await getToken();
      return api.sendMessage(interviewId!, message, token || undefined, sessionRunId || undefined);
    },
    onSuccess: (data) => {
      setUserMessage("");
      // Invalidate query with session_run_id to refetch current session only
      queryClient.invalidateQueries({ queryKey: ["interview-sessions", interviewId, sessionRunId] });
      
      // Add the new AI message to the UI immediately
      if (data.ai_message) {
        // The query will refetch and update the messages
      }
    },
    onError: (error) => {
      toast.error("Failed to send message", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  // Auto-start interview on mount - ALWAYS creates a new session run
  useEffect(() => {
    if (interviewId && !started && !startInterviewMutation.isPending) {
      // Reset state to ensure fresh start
      setSessionRunId(null);
      setOpeningQuestion(null);
      setStarted(false);
      startInterviewMutation.mutate();
    }
  }, [interviewId]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userMessage.trim() || sendMessageMutation.isPending) return;
    
    sendMessageMutation.mutate(userMessage.trim());
  };

  if (!interviewId) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <div className="container-custom pt-24 pb-12">
          <Card>
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">Invalid interview ID</p>
              <Button onClick={() => navigate("/dashboard")} className="mt-4">
                Back to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      
      <main className="flex-1 container-custom pt-24 pb-12">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/dashboard")}
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold">AI Interview</h1>
                {started && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                    <Clock className="w-4 h-4" />
                    <span>{formatTime(elapsedTime)}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chat Container */}
          <Card className="mb-4">
            <CardContent className="p-6">
              <div className="h-[500px] overflow-y-auto mb-4 pr-2">
                {startInterviewMutation.isPending ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <span className="ml-2 text-muted-foreground">Starting interview...</span>
                  </div>
                ) : isLoadingHistory ? (
                  <div className="flex items-center justify-center h-full">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                    <span className="ml-2 text-muted-foreground">Loading conversation...</span>
                  </div>
                ) : messages.length === 0 ? (
                  <div className="flex items-center justify-center h-full text-muted-foreground">
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
                      <div className="flex gap-3 mb-6">
                        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                          <Bot className="w-4 h-4 text-primary" />
                        </div>
                        <div className="bg-muted rounded-lg px-4 py-3">
                          <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </>
                )}
              </div>

              {/* Input Form */}
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <Input
                  value={userMessage}
                  onChange={(e) => setUserMessage(e.target.value)}
                  placeholder="Type your answer..."
                  disabled={!started || sendMessageMutation.isPending}
                  className="flex-1"
                />
                <Button
                  type="submit"
                  disabled={!started || !userMessage.trim() || sendMessageMutation.isPending}
                >
                  {sendMessageMutation.isPending ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default InterviewPage;

