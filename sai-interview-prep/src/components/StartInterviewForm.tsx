import { useState, useEffect } from "react";
import { useAuth } from "@clerk/clerk-react";
import { useMutation } from "@tanstack/react-query";
import { api, Interview } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Upload, FileText, X } from "lucide-react";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

interface StartInterviewFormProps {
  onSuccess?: (interviewId: string) => void;
  onCancel?: () => void;
  interview?: Interview | null; // For edit mode
}

export const StartInterviewForm = ({ onSuccess, onCancel, interview }: StartInterviewFormProps) => {
  const { getToken } = useAuth();
  const navigate = useNavigate();
  const isEditMode = !!interview;
  
  const [title, setTitle] = useState(interview?.title || "");
  const [durationMinutes, setDurationMinutes] = useState(interview?.duration_minutes || 30);
  const [jobDescriptionText, setJobDescriptionText] = useState("");
  const [jobDescriptionFile, setJobDescriptionFile] = useState<File | null>(null);
  const [cvFile, setCvFile] = useState<File | null>(null);

  // Update form when interview prop changes (for edit mode)
  useEffect(() => {
    if (interview) {
      setTitle(interview.title || "");
      setDurationMinutes(interview.duration_minutes || 30);
      // Note: We don't pre-fill JD text or files as they're already processed
      // User can upload new ones to replace existing
    }
  }, [interview]);

  const createInterviewMutation = useMutation({
    mutationFn: async () => {
      const token = await getToken();
      if (isEditMode && interview) {
        // Update existing interview
        return api.updateInterview(
          interview.id,
          {
            title,
            duration_minutes: durationMinutes,
          },
          token || undefined
        );
      } else {
        // Create new interview
        return api.createInterview(
          {
            title,
            duration_minutes: durationMinutes,
          },
          token || undefined
        );
      }
    },
    onSuccess: async (updatedInterview) => {
      const token = await getToken();
      const interviewId = isEditMode ? interview!.id : updatedInterview.id;
      
      // Upload files if provided - they will be processed by AI
      const uploadPromises = [];
      
      // If job description was pasted as text, process it via a text upload endpoint
      if (jobDescriptionText && !jobDescriptionFile) {
        uploadPromises.push(
          api.processJobDescriptionText(interviewId, jobDescriptionText, token || undefined)
        );
      } else if (jobDescriptionFile) {
        uploadPromises.push(
          api.uploadJobDescription(interviewId, jobDescriptionFile, token || undefined)
        );
      }
      
      if (cvFile) {
        uploadPromises.push(
          api.uploadCV(interviewId, cvFile, token || undefined)
        );
      }
      
      if (uploadPromises.length > 0) {
        await Promise.all(uploadPromises);
      }
      
      toast.success(
        isEditMode ? "Interview updated successfully!" : "Interview created successfully!",
        {
          description: `"${updatedInterview.title}" is ready to start`,
        }
      );
      
      if (onSuccess) {
        onSuccess(interviewId);
      } else {
        // Navigate to interview page (to be created later)
        navigate(`/interview/${interviewId}`);
      }
    },
    onError: (error) => {
      toast.error(
        isEditMode ? "Failed to update interview" : "Failed to create interview",
        {
          description: error instanceof Error ? error.message : "Unknown error",
        }
      );
    },
  });

  const handleJobDescriptionFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== "application/pdf") {
        toast.error("Invalid file type", {
          description: "Please upload a PDF file",
        });
        return;
      }
      setJobDescriptionFile(file);
      setJobDescriptionText(""); // Clear text if file is selected
    }
  };

  const handleCVFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type !== "application/pdf") {
        toast.error("Invalid file type", {
          description: "Please upload a PDF file",
        });
        return;
      }
      setCvFile(file);
    }
  };

  const removeJobDescriptionFile = () => {
    setJobDescriptionFile(null);
  };

  const removeCVFile = () => {
    setCvFile(null);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!title.trim()) {
      toast.error("Title is required");
      return;
    }
    
    // In edit mode, we can update even if no files are provided
    // In create mode, job description is optional (can be added later)
    // Files will be processed by AI when uploaded
    createInterviewMutation.mutate();
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{isEditMode ? "Edit Interview" : "Start New Interview"}</CardTitle>
        <CardDescription>
          {isEditMode 
            ? "Update your interview details, job description, or CV. Uploading new files will replace existing ones."
            : "Set up your interview with a job description and CV. We'll use AI to personalize the questions."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Interview Title */}
          <div className="space-y-2">
            <Label htmlFor="title">Interview Title *</Label>
            <Input
              id="title"
              placeholder="e.g., Senior Software Engineer at Google"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          {/* Duration */}
          <div className="space-y-2">
            <Label htmlFor="duration">Maximum Interview Duration (minutes)</Label>
            <Input
              id="duration"
              type="number"
              min="15"
              max="60"
              value={durationMinutes}
              onChange={(e) => setDurationMinutes(parseInt(e.target.value) || 30)}
            />
            <p className="text-xs text-muted-foreground">
              Default: 30 minutes. Range: 15 to 60 minutes.
            </p>
          </div>

          {/* Job Description */}
          <div className="space-y-2">
            <Label htmlFor="job-description">
              Job Description {isEditMode ? "(Optional - upload to replace existing)" : "*"}
            </Label>
            {isEditMode && interview?.job_description && (
              <p className="text-xs text-muted-foreground mb-2">
                Current: {interview.job_description.substring(0, 100)}
                {interview.job_description.length > 100 ? "..." : ""}
              </p>
            )}
            <div className="space-y-3">
              {/* Option A: Upload PDF */}
              <div>
                <Label htmlFor="jd-file" className="text-sm text-muted-foreground">
                  Option A: Upload PDF
                </Label>
                <div className="flex items-center gap-2 mt-1">
                  <Input
                    id="jd-file"
                    type="file"
                    accept=".pdf"
                    onChange={handleJobDescriptionFileChange}
                    className="hidden"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => document.getElementById("jd-file")?.click()}
                    className="gap-2"
                  >
                    <Upload className="w-4 h-4" />
                    {jobDescriptionFile ? jobDescriptionFile.name : "Upload PDF"}
                  </Button>
                  {jobDescriptionFile && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={removeJobDescriptionFile}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>

              {/* Option B: Paste Text */}
              <div>
                <Label htmlFor="jd-text" className="text-sm text-muted-foreground">
                  Option B: Paste Text
                </Label>
                <Textarea
                  id="jd-text"
                  placeholder="Paste the job description here..."
                  value={jobDescriptionText}
                  onChange={(e) => {
                    setJobDescriptionText(e.target.value);
                    if (e.target.value) {
                      setJobDescriptionFile(null); // Clear file if text is entered
                    }
                  }}
                  rows={6}
                  disabled={!!jobDescriptionFile}
                />
              </div>
            </div>
          </div>

          {/* CV Upload */}
          <div className="space-y-2">
            <Label htmlFor="cv-file">CV Upload {isEditMode ? "(Optional - upload to replace existing)" : "(Optional)"}</Label>
            <p className="text-xs text-muted-foreground mb-2">
              {isEditMode 
                ? "Upload a new CV PDF to replace the existing one. It will be processed by AI."
                : "Upload your CV as PDF. If not provided, you can add it later."}
            </p>
            {isEditMode && interview?.cv_summary && (
              <p className="text-xs text-muted-foreground mb-2">
                Current CV Summary: {interview.cv_summary.substring(0, 100)}
                {interview.cv_summary.length > 100 ? "..." : ""}
              </p>
            )}
            <div className="flex items-center gap-2">
              <Input
                id="cv-file"
                type="file"
                accept=".pdf"
                onChange={handleCVFileChange}
                className="hidden"
              />
              <Button
                type="button"
                variant="outline"
                onClick={() => document.getElementById("cv-file")?.click()}
                className="gap-2"
              >
                <FileText className="w-4 h-4" />
                {cvFile ? cvFile.name : "Upload CV PDF"}
              </Button>
              {cvFile && (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={removeCVFile}
                >
                  <X className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex gap-3 pt-4">
            <Button
              type="submit"
              disabled={createInterviewMutation.isPending}
              className="flex-1"
            >
              {createInterviewMutation.isPending 
                ? (isEditMode ? "Updating..." : "Creating...") 
                : (isEditMode ? "Update Interview" : "Create Interview")}
            </Button>
            {onCancel && (
              <Button
                type="button"
                variant="outline"
                onClick={onCancel}
              >
                Cancel
              </Button>
            )}
            {!isEditMode && (
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setTitle("");
                  setDurationMinutes(30);
                  setJobDescriptionText("");
                  setJobDescriptionFile(null);
                  setCvFile(null);
                }}
              >
                Reset
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

