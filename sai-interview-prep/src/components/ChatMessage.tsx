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
      "flex gap-4 mb-6 animate-in fade-in slide-in-from-bottom-2 duration-300",
      isAI ? "justify-start" : "justify-end"
    )}>
      {isAI && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-md">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}

      <div className={cn(
        "flex flex-col max-w-[80%]",
        isAI ? "items-start" : "items-end"
      )}>
        <div className={cn(
          "rounded-2xl px-5 py-4 shadow-sm",
          isAI
            ? "bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-800 dark:text-gray-100 rounded-tl-none"
            : "bg-blue-600 text-white rounded-tr-none"
        )}>
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
        </div>

        {isAI && feedback && (
          <div className="mt-2 px-4 py-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-xl border border-yellow-100 dark:border-yellow-900/50">
            <p className="text-xs text-yellow-800 dark:text-yellow-200">
              <span className="font-semibold block mb-1">Feedback:</span>
              {feedback}
            </p>
          </div>
        )}

        {timestamp && (
          <span className="text-[10px] text-gray-400 mt-1.5 px-1">
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {!isAI && (
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center shadow-sm">
          <User className="w-5 h-5 text-gray-500 dark:text-gray-300" />
        </div>
      )}
    </div>
  );
};

