import { Bot, User } from "lucide-react";
import { cn } from "@/lib/utils";

interface ChatMessageProps {
  role: "ai" | "user";
  content: string;
  feedback?: string | null;
  timestamp?: string;
}

export const ChatMessage = ({ role, content, feedback, timestamp }: ChatMessageProps) => {
  const isAI = role === "ai";

  return (
    <div className={cn(
      "flex gap-3 mb-6",
      isAI ? "justify-start" : "justify-end"
    )}>
      {isAI && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <Bot className="w-4 h-4 text-primary" />
        </div>
      )}
      
      <div className={cn(
        "flex flex-col max-w-[80%]",
        isAI ? "items-start" : "items-end"
      )}>
        <div className={cn(
          "rounded-lg px-4 py-3",
          isAI 
            ? "bg-muted text-foreground" 
            : "bg-primary text-primary-foreground"
        )}>
          <p className="text-sm whitespace-pre-wrap">{content}</p>
        </div>
        
        {isAI && feedback && (
          <div className="mt-2 px-3 py-2 bg-muted/50 rounded-md border-l-2 border-primary/30">
            <p className="text-xs text-muted-foreground italic">
              <span className="font-medium">Feedback: </span>
              {feedback}
            </p>
          </div>
        )}
        
        {timestamp && (
          <span className="text-xs text-muted-foreground mt-1">
            {new Date(timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>
      
      {!isAI && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
          <User className="w-4 h-4 text-primary" />
        </div>
      )}
    </div>
  );
};

