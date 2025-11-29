import { Code, Mic, GitBranch } from 'lucide-react';

const Practice = () => {
  const practiceTypes = [
    {
      icon: <Code className="w-5 h-5" />,
      title: 'Live Coding Editor',
      description: 'Write and execute code in real-time with syntax highlighting and auto-completion.',
      visual: (
        <div className="bg-foreground/5 rounded-lg p-4 font-mono text-xs">
          <div className="flex items-center gap-2 mb-3 text-muted-foreground">
            <div className="w-3 h-3 rounded-full bg-destructive/40" />
            <div className="w-3 h-3 rounded-full bg-yellow-500/40" />
            <div className="w-3 h-3 rounded-full bg-green-500/40" />
          </div>
          <div className="space-y-1 text-muted-foreground">
            <div>
              <span className="text-blue-accent">def</span>{' '}
              <span className="text-foreground">twoSum</span>(nums, target):
            </div>
            <div className="pl-4">seen = {'{}'}</div>
            <div className="pl-4">
              <span className="text-blue-accent">for</span> i, n{' '}
              <span className="text-blue-accent">in</span> enumerate(nums):
            </div>
            <div className="pl-8">diff = target - n</div>
            <div className="pl-8">
              <span className="text-blue-accent">if</span> diff{' '}
              <span className="text-blue-accent">in</span> seen:
            </div>
            <div className="pl-12 text-foreground">
              <span className="text-blue-accent">return</span> [seen[diff], i]
            </div>
          </div>
        </div>
      ),
    },
    {
      icon: <Mic className="w-5 h-5" />,
      title: 'Voice Chat Interface',
      description: 'Practice verbal communication with real-time speech recognition.',
      visual: (
        <div className="space-y-3">
          <div className="flex items-end gap-2">
            <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
              <span className="text-xs text-primary font-medium">AI</span>
            </div>
            <div className="bg-secondary rounded-2xl rounded-bl-sm px-4 py-2 max-w-[200px]">
              <p className="text-xs text-foreground">Tell me about a challenging project you worked on.</p>
            </div>
          </div>
          <div className="flex items-end gap-2 justify-end">
            <div className="bg-primary/10 rounded-2xl rounded-br-sm px-4 py-2 max-w-[200px]">
              <p className="text-xs text-foreground">I led the migration of our monolith to microservices...</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
              <span className="text-xs text-muted-foreground font-medium">You</span>
            </div>
          </div>
        </div>
      ),
    },
    {
      icon: <GitBranch className="w-5 h-5" />,
      title: 'Architecture Canvas',
      description: 'Design system architectures with drag-and-drop components.',
      visual: (
        <div className="relative h-32">
          {/* Simplified architecture diagram */}
          <div className="absolute top-0 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-secondary rounded-lg text-xs text-foreground font-medium">
            Load Balancer
          </div>
          <div className="absolute top-8 left-1/2 w-px h-6 bg-border" />
          <div className="absolute top-14 left-0 right-0 flex justify-center gap-8">
            <div className="px-2 py-1 bg-blue-accent-light rounded text-xs text-foreground">Server 1</div>
            <div className="px-2 py-1 bg-blue-accent-light rounded text-xs text-foreground">Server 2</div>
            <div className="px-2 py-1 bg-blue-accent-light rounded text-xs text-foreground">Server 3</div>
          </div>
          <div className="absolute top-24 left-1/2 w-px h-4 bg-border" />
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 px-3 py-1.5 bg-secondary rounded-lg text-xs text-foreground font-medium">
            Database
          </div>
        </div>
      ),
    },
  ];

  return (
    <section id="practice" className="section-padding bg-background">
      <div className="container-custom">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-foreground mb-4 fade-in-up">
            Practice Like a Real Interview
          </h2>
          <p className="text-muted-foreground text-lg fade-in-up fade-in-up-delay-1">
            Experience interviews that feel authentic with our comprehensive suite of interactive tools.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {practiceTypes.map((type, index) => (
            <div
              key={type.title}
              className="card-elevated p-6 fade-in-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-secondary flex items-center justify-center text-muted-foreground">
                  {type.icon}
                </div>
                <h3 className="font-semibold text-foreground">{type.title}</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-6">{type.description}</p>
              <div className="border border-border rounded-xl p-4 bg-secondary/30">
                {type.visual}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default Practice;
