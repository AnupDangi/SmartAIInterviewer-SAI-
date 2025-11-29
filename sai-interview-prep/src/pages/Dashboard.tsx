import { useState, useEffect } from "react";
import { useAuth, useUser } from "@clerk/clerk-react";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { api, Interview } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Plus, FileText, Calendar, Edit, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import Header from "@/components/Header";
import { StartInterviewForm } from "@/components/StartInterviewForm";

const Dashboard = () => {
  const { getToken } = useAuth();
  const { user } = useUser();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [editingInterview, setEditingInterview] = useState<Interview | null>(null);

  // Store Clerk token and ensure user exists in DB (only once)
  const [userInitialized, setUserInitialized] = useState(false);
  
  useEffect(() => {
    let isMounted = true;
    
    const initializeUser = async () => {
      if (getToken && !userInitialized) {
        try {
          const token = await getToken();
          if (token && isMounted) {
            localStorage.setItem("clerk_token", token);
            // Call /api/users/me to ensure user exists in database
            await api.getCurrentUser(token);
            if (isMounted) {
              setUserInitialized(true);
            }
          }
        } catch (error) {
          console.error("Failed to initialize user:", error);
        }
      }
    };
    
    initializeUser();
    
    return () => {
      isMounted = false;
    };
  }, [getToken, userInitialized]);

  // Fetch user interviews
  const { data: interviews = [], isLoading } = useQuery({
    queryKey: ["interviews"],
    queryFn: async () => {
      const token = await getToken();
      return api.getInterviews(token || undefined);
    },
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const handleInterviewCreated = (interviewId: string) => {
    queryClient.invalidateQueries({ queryKey: ["interviews"] });
    setShowForm(false);
    setEditingInterview(null);
    // TODO: Navigate to interview page when it's created
    // navigate(`/interview/${interviewId}`);
  };


  // Delete interview mutation
  const deleteMutation = useMutation({
    mutationFn: async (interviewId: string) => {
      const token = await getToken();
      return api.deleteInterview(interviewId, token || undefined);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["interviews"] });
      toast.success("Interview deleted successfully");
    },
    onError: (error) => {
      toast.error("Failed to delete interview", {
        description: error instanceof Error ? error.message : "Unknown error",
      });
    },
  });

  const handleEditClick = (interview: Interview) => {
    setEditingInterview(interview);
    setShowForm(true);
  };

  const handleEditSuccess = (interviewId: string) => {
    queryClient.invalidateQueries({ queryKey: ["interviews"] });
    setEditingInterview(null);
    setShowForm(false);
  };

  const handleEditCancel = () => {
    setEditingInterview(null);
    setShowForm(false);
  };

  const handleDeleteClick = (interview: Interview) => {
    if (window.confirm(`Are you sure you want to delete "${interview.title}"? This action cannot be undone.`)) {
      deleteMutation.mutate(interview.id);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container-custom pt-24 pb-12">
        <div className="max-w-7xl mx-auto">
          {/* Header Section */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold text-foreground mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              Welcome back, {user?.firstName || user?.emailAddresses[0]?.emailAddress || "User"}!
            </p>
          </div>

          {/* Show Form or Start Button */}
          {showForm ? (
            <div className="mb-8">
              <StartInterviewForm 
                onSuccess={editingInterview ? handleEditSuccess : handleInterviewCreated}
                onCancel={editingInterview ? handleEditCancel : () => setShowForm(false)}
                interview={editingInterview}
              />
            </div>
          ) : (
            <Card className="mb-8 border-primary/20 bg-primary/5">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Start New Interview
                </CardTitle>
                <CardDescription>
                  Create a new interview session with your CV and Job Description for personalized AI questions.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button
                  onClick={() => setShowForm(true)}
                  size="lg"
                  className="gap-2"
                >
                  <Plus className="w-4 h-4" />
                  Start New Interview
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Interviews List */}
          <div className="mb-4">
            <h2 className="text-2xl font-semibold text-foreground mb-4">Your Interviews</h2>
          </div>

          {isLoading ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Loading interviews...</p>
            </div>
          ) : interviews.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <FileText className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                <p className="text-muted-foreground mb-4">No interviews yet.</p>
                <Button onClick={() => setShowForm(true)} variant="outline">
                  Create Your First Interview
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4">
              {interviews.map((interview: Interview) => (
                <Card key={interview.id} className="hover:shadow-md transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2">
                          {interview.title}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-4 mt-2">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(interview.created_at)}
                          </span>
                          <span className="text-xs">
                            {interview.duration_minutes} minutes
                          </span>
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 mb-4">
                      {interview.job_description ? (
                        <div className="text-sm">
                          <span className="font-medium">Job Description: </span>
                          <span className="text-muted-foreground">
                            {interview.job_description.length > 100
                              ? `${interview.job_description.substring(0, 100)}...`
                              : interview.job_description}
                          </span>
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          Job Description: Not uploaded yet
                        </p>
                      )}
                      {interview.cv_summary ? (
                        <div className="text-sm">
                          <span className="font-medium">CV Summary: </span>
                          <span className="text-muted-foreground">
                            {interview.cv_summary.length > 100
                              ? `${interview.cv_summary.substring(0, 100)}...`
                              : interview.cv_summary}
                          </span>
                        </div>
                      ) : (
                        <p className="text-xs text-muted-foreground">
                          CV Summary: Processing or not uploaded
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="default"
                        size="sm"
                        onClick={() => navigate(`/interview/${interview.id}`)}
                      >
                        Start Interview
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEditClick(interview)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteClick(interview)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </main>

    </div>
  );
};

export default Dashboard;
