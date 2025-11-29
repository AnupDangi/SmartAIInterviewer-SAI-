import { ArrowRight } from 'lucide-react';
import {
  SignedIn,
  SignedOut,
  SignUpButton,
} from "@clerk/clerk-react";

const CTA = () => {
  return (
    <section className="section-padding bg-secondary/30">
      <div className="container-custom">
        <div className="max-w-3xl mx-auto text-center fade-in-up">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4">
            Ready to ace your next interview?
          </h2>
          <p className="text-muted-foreground text-lg mb-8">
            Join thousands of engineers who have improved their interview skills with SAI.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <SignedOut>
              <SignUpButton mode="modal">
                <button className="btn-primary gap-2 group">
                  Start Practicing Now
                  <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
                </button>
              </SignUpButton>
            </SignedOut>
            <SignedIn>
              <button className="btn-primary gap-2 group">
                Start Practicing Now
                <ArrowRight className="w-4 h-4 transition-transform duration-200 group-hover:translate-x-1" />
              </button>
            </SignedIn>
            <button className="btn-secondary">
              View Demo
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};

export default CTA;
