import { Mic, MicOff, Video, VideoOff, MessageSquare, Code, PhoneOff } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ControlBarProps {
    isMuted: boolean;
    isVideoOn: boolean;
    isChatOpen: boolean;
    isCodeOpen: boolean;
    onToggleMute: () => void;
    onToggleVideo: () => void;
    onToggleChat: () => void;
    onToggleCode: () => void;
    onEndCall: () => void;
    hideVideoControls?: boolean;
}

const ControlBar = ({
    isMuted,
    isVideoOn,
    isChatOpen,
    isCodeOpen,
    onToggleMute,
    onToggleVideo,
    onToggleChat,
    onToggleCode,
    onEndCall,
    hideVideoControls = false,
}: ControlBarProps) => {
    return (
        <div className="h-20 bg-zinc-900 border-t border-zinc-800 flex items-center justify-center px-4 gap-4 sm:gap-8">
            {/* Audio/Video Controls */}
            {!hideVideoControls && (
                <div className="flex gap-2">
                    <ControlButton
                        icon={isMuted ? MicOff : Mic}
                        label={isMuted ? "Unmute" : "Mute"}
                        isActive={!isMuted}
                        onClick={onToggleMute}
                        variant="secondary"
                    />
                    <ControlButton
                        icon={isVideoOn ? Video : VideoOff}
                        label={isVideoOn ? "Stop Video" : "Start Video"}
                        isActive={isVideoOn}
                        onClick={onToggleVideo}
                        variant="secondary"
                    />
                </div>
            )}

            {/* Main Features */}
            <div className="flex gap-2">
                <ControlButton
                    icon={Code}
                    label="Code"
                    isActive={isCodeOpen}
                    onClick={onToggleCode}
                    activeColor="text-blue-400"
                />
                <ControlButton
                    icon={MessageSquare}
                    label="Chat"
                    isActive={isChatOpen}
                    onClick={onToggleChat}
                    activeColor="text-blue-400"
                />
            </div>

            {/* End Call */}
            <Button
                variant="destructive"
                className="rounded-xl px-6 bg-red-600 hover:bg-red-700 text-white"
                onClick={onEndCall}
            >
                <PhoneOff className="w-5 h-5 mr-2" />
                End
            </Button>
        </div>
    );
};

interface ControlButtonProps {
    icon: React.ElementType;
    label: string;
    isActive?: boolean;
    onClick: () => void;
    variant?: "primary" | "secondary";
    activeColor?: string;
}

const ControlButton = ({
    icon: Icon,
    label,
    isActive,
    onClick,
    variant = "primary",
    activeColor = "text-white"
}: ControlButtonProps) => {
    return (
        <button
            onClick={onClick}
            className={cn(
                "flex flex-col items-center gap-1 p-2 rounded-lg transition-colors min-w-[64px]",
                isActive ? "text-white" : "text-zinc-400 hover:bg-zinc-800"
            )}
        >
            <div className={cn(
                "p-2 rounded-xl transition-all",
                isActive && variant === "primary" ? "bg-zinc-700" : "",
                isActive && variant === "secondary" ? "bg-zinc-800" : "",
                !isActive && "bg-transparent"
            )}>
                <Icon className={cn("w-6 h-6", isActive ? activeColor : "text-zinc-400")} />
            </div>
            <span className="text-[10px] font-medium">{label}</span>
        </button>
    );
};

export default ControlBar;
