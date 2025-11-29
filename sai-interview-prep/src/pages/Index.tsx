import { useEffect } from 'react';
import { useAuth } from '@clerk/clerk-react';
import { useNavigate } from 'react-router-dom';
import Header from '@/components/Header';
import Hero from '@/components/Hero';
import Features from '@/components/Features';
import MultiAgent from '@/components/MultiAgent';
import Practice from '@/components/Practice';
import CTA from '@/components/CTA';
import Footer from '@/components/Footer';

const Index = () => {
  const { isSignedIn, isLoaded } = useAuth();
  const navigate = useNavigate();

  // Redirect authenticated users to dashboard
  useEffect(() => {
    if (isLoaded && isSignedIn) {
      navigate('/dashboard', { replace: true });
    }
  }, [isLoaded, isSignedIn, navigate]);

  // Show loading while checking auth
  if (!isLoaded) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Don't render landing page if user is signed in (will redirect)
  if (isSignedIn) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main>
        <Hero />
        <Features />
        <MultiAgent />
        <Practice />
        <CTA />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
