import HeroAnimation from './HeroAnimation';
import TypingEffect from './TypingEffect';
import { ArrowRight, Upload } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
  SignedIn,
  SignedOut,
  SignInButton,
  SignUpButton,
} from "@clerk/clerk-react";

const Hero = () => {
  const navigate = useNavigate();

  return (
    <section className="relative min-h-screen flex items-center pt-20 lg:pt-0">
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-secondary/30 via-background to-background pointer-events-none" />
      
      <div className="container-custom relative">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left content */}
          <div className="text-center lg:text-left">
            <div className="fade-in-up">
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-secondary text-muted-foreground text-xs font-medium mb-6">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-accent animate-pulse-soft" />
                AI-Powered Interview Prep
              </span>
            </div>

            <h1 className="fade-in-up fade-in-up-delay-1 text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground leading-tight mb-6">
              <span className="block">Want to prepare</span>
              <span className="block">for interviews??</span>
              <span className="block text-muted-foreground">
                <TypingEffect text="Your SAI is here." speed={80} />
              </span>
            </h1>

            <p className="fade-in-up fade-in-up-delay-2 text-lg text-muted-foreground max-w-xl mx-auto lg:mx-0 mb-8 leading-relaxed">
              Your Smart AI Interviewer that helps you practice coding, system design, and real interview questions — with feedback powered by real AI agents.
            </p>

            <div className="fade-in-up fade-in-up-delay-3 flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <SignedOut>
                <SignUpButton mode="modal">
                  <button className="btn-primary gap-2 group">
                    Start Interview
                    <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
                  </button>
                </SignUpButton>
                <SignUpButton mode="modal">
                  <button className="btn-secondary gap-2">
                    <Upload className="w-4 h-4" />
                    Upload CV & Job Description
                  </button>
                </SignUpButton>
              </SignedOut>
              <SignedIn>
                <button 
                  onClick={() => navigate('/dashboard')}
                  className="btn-primary gap-2 group"
                >
                  Start Interview
                  <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
                </button>
                <button 
                  onClick={() => navigate('/dashboard')}
                  className="btn-secondary gap-2"
                >
                  <Upload className="w-4 h-4" />
                  Upload CV & Job Description
                </button>
              </SignedIn>
            </div>

            {/* Social proof */}
            <div className="fade-in-up fade-in-up-delay-4 mt-12 pt-8 border-t border-border">
              <p className="text-xs text-muted-foreground mb-3">Trusted by engineers from</p>
              <div className="flex items-center justify-center lg:justify-start gap-8 opacity-40">
                <span className="text-sm font-medium text-foreground">Google</span>
                <span className="text-sm font-medium text-foreground">Meta</span>
                <span className="text-sm font-medium text-foreground">Amazon</span>
                <span className="text-sm font-medium text-foreground">Microsoft</span>
              </div>
            </div>
          </div>

          {/* Right animation */}
          <div className="fade-in-up fade-in-up-delay-2 hidden lg:block">
            <HeroAnimation />
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
