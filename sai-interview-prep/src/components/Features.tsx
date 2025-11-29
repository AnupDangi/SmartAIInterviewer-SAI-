import FeatureCard from './FeatureCard';
import { Code2, Layout, MessageSquare, Sparkles } from 'lucide-react';

const Features = () => {
  const features = [
    {
      icon: <Code2 className="w-6 h-6" />,
      title: 'Coding Interviews',
      description: 'Practice data structures, algorithms, and problem-solving with real-time code execution and hints.',
    },
    {
      icon: <Layout className="w-6 h-6" />,
      title: 'System Design',
      description: 'Design scalable systems with interactive architecture diagrams and expert feedback on trade-offs.',
    },
    {
      icon: <MessageSquare className="w-6 h-6" />,
      title: 'Behavioral Practice',
      description: 'Master STAR method responses with AI-driven behavioral interview simulations.',
    },
    {
      icon: <Sparkles className="w-6 h-6" />,
      title: 'Real-time Feedback',
      description: 'Get instant, actionable feedback on your answers, communication, and technical accuracy.',
    },
  ];

  return (
    <section id="features" className="section-padding bg-background">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 fade-in-up">
            How SAI Helps You
          </h2>
          <p className="text-muted-foreground text-lg fade-in-up fade-in-up-delay-1">
            Comprehensive interview preparation powered by intelligent AI agents that adapt to your skill level.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              delay={index * 100}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Features;
