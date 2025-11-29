import { Bot, Brain, Lightbulb, Target } from 'lucide-react';

const MultiAgent = () => {
  const agents = [
    {
      icon: <Brain className="w-5 h-5" />,
      title: 'Interviewer Agent',
      description: 'Conducts realistic interviews',
    },
    {
      icon: <Lightbulb className="w-5 h-5" />,
      title: 'Hint Agent',
      description: 'Provides contextual guidance',
    },
    {
      icon: <Target className="w-5 h-5" />,
      title: 'Evaluation Agent',
      description: 'Scores your performance',
    },
    {
      icon: <Bot className="w-5 h-5" />,
      title: 'Feedback Agent',
      description: 'Delivers actionable insights',
    },
  ];

  return (
    <section id="how-it-works" className="section-padding bg-secondary/30">
      <div className="container-custom">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left content */}
          <div>
            <span className="inline-block text-xs font-medium text-muted-foreground uppercase tracking-wider mb-4 fade-in-up">
              Advanced Technology
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-6 fade-in-up fade-in-up-delay-1">
              Powered by Multi-Agent Intelligence
            </h2>
            <p className="text-muted-foreground text-lg mb-8 leading-relaxed fade-in-up fade-in-up-delay-2">
              Our system uses specialized AI agents working together to create the most realistic and helpful interview experience possible.
            </p>

            <div className="grid grid-cols-2 gap-4 fade-in-up fade-in-up-delay-3">
              {agents.map((agent) => (
                <div
                  key={agent.title}
                  className="flex items-start gap-3 p-4 rounded-xl bg-background border border-border transition-all duration-200 hover:border-primary/20"
                >
                  <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center flex-shrink-0">
                    <span className="text-muted-foreground">{agent.icon}</span>
                  </div>
                  <div>
                    <h4 className="font-medium text-foreground text-sm mb-0.5">{agent.title}</h4>
                    <p className="text-xs text-muted-foreground">{agent.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right visualization */}
          <div className="relative fade-in-up fade-in-up-delay-2">
            <div className="aspect-square max-w-md mx-auto relative">
              {/* Central hub */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 rounded-full bg-background border-2 border-primary/20 flex items-center justify-center shadow-soft-lg z-10">
                <span className="font-bold text-foreground">SAI</span>
              </div>

              {/* Orbiting agents */}
              {agents.map((agent, index) => {
                const angle = (index * 90 - 45) * (Math.PI / 180);
                const radius = 120;
                const x = Math.cos(angle) * radius;
                const y = Math.sin(angle) * radius;

                return (
                  <div
                    key={agent.title}
                    className="absolute top-1/2 left-1/2 w-16 h-16 rounded-full bg-background border border-border flex items-center justify-center shadow-soft-md transition-all duration-300 hover:shadow-soft-lg hover:scale-110"
                    style={{
                      transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`,
                    }}
                  >
                    <span className="text-muted-foreground">{agent.icon}</span>
                  </div>
                );
              })}

              {/* Connection lines */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {agents.map((_, index) => {
                  const angle = (index * 90 - 45) * (Math.PI / 180);
                  const radius = 120;
                  const x = 50 + (Math.cos(angle) * radius) / 4;
                  const y = 50 + (Math.sin(angle) * radius) / 4;

                  return (
                    <line
                      key={index}
                      x1="50%"
                      y1="50%"
                      x2={`${x}%`}
                      y2={`${y}%`}
                      className="stroke-border"
                      strokeWidth="1"
                      strokeDasharray="4 4"
                    />
                  );
                })}
              </svg>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default MultiAgent;
