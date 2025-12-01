import React, { useState } from 'react';
import Editor from '@monaco-editor/react';
import { Code, X, Play } from 'lucide-react';

interface CodeEditorProps {
    isOpen: boolean;
    onClose?: () => void;
    onSubmit: (code: string, language: string) => void;
    initialCode?: string;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ isOpen, onClose, onSubmit, initialCode = "" }) => {
    const [code, setCode] = useState<string>(initialCode || "# Write your code here\n");
    const [language, setLanguage] = useState<string>("python");
    // output state was unused in the original component, removing it or keeping it if needed for future?
    // It was unused in the JSX version provided in context. I'll remove it to be clean, or keep it if I suspect it's needed.
    // The user didn't ask to remove unused code, but TS might complain if unused.
    // I'll remove it as it wasn't used.

    if (!isOpen) return null;

    const handleSubmit = () => {
        onSubmit(code, language);
    };

    return (
        <div className="w-full h-full bg-[#1e1e1e] flex flex-col overflow-hidden border border-gray-800 animate-in fade-in duration-300">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 bg-[#252526] border-b border-gray-800 shrink-0">
                <div className="flex items-center space-x-4">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded bg-blue-600/20 flex items-center justify-center">
                            <Code className="w-4 h-4 text-blue-500" />
                        </div>
                        <h2 className="text-sm font-semibold text-zinc-200">Code Editor</h2>
                    </div>

                    <select
                        name='language'
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="text-xs rounded px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-zinc-200 focus:ring-1 focus:ring-blue-500 outline-none hover:bg-zinc-700 transition-colors cursor-pointer"
                    >
                        <option className='bg-zinc-800 text-zinc-200' value="python">Python</option>
                        <option className='bg-zinc-800 text-zinc-200' value="cpp">C++</option>
                        <option className='bg-zinc-800 text-zinc-200' value="c">C</option>
                        <option className='bg-zinc-800 text-zinc-200' value="java">Java</option>
                        <option className='bg-zinc-800 text-zinc-200' value="javascript">JavaScript</option>
                    </select>

                </div>

                {/* Close button only if onClose is provided (optional in this new layout) */}
                {onClose && (
                    <button
                        onClick={onClose}
                        className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded transition-all"
                        title="Close Editor"
                    >
                        <X className="w-4 h-4" />
                    </button>
                )}
            </div>

            {/* Editor Area */}
            <div className="flex-1 relative min-h-0">
                <Editor
                    height="100%"
                    defaultLanguage="python"
                    language={language}
                    value={code}
                    onChange={(value) => setCode(value || "")}
                    theme="vs-dark"
                    options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        padding: { top: 16, bottom: 16 },
                        lineNumbers: "on",
                        renderLineHighlight: "all",
                    }}
                />
            </div>

            {/* Footer */}
            <div className="px-4 py-3 bg-[#252526] border-t border-gray-800 flex justify-between items-center shrink-0">
                <div className="text-xs text-gray-500 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500"></span>
                    Ready
                </div>
                <div className="flex space-x-3">
                    <button
                        onClick={handleSubmit}
                        className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-md transition-all shadow-lg shadow-blue-900/20 flex items-center space-x-2 active:scale-95"
                    >
                        <Play className="w-3 h-3" />
                        <span>Run & Submit</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CodeEditor;
