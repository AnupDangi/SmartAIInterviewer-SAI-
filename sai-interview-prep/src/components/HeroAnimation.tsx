import { useEffect, useState } from 'react';

const HeroAnimation = () => {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  return (
    <div className="relative w-full max-w-md mx-auto h-64 md:h-80">
      {/* Main AI face outline */}
      <svg
        viewBox="0 0 200 200"
        className="w-full h-full"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Background circles */}
        <circle
          cx="100"
          cy="100"
          r="80"
          className={`stroke-border transition-all duration-1000 ${mounted ? 'opacity-100' : 'opacity-0'}`}
          strokeWidth="0.5"
          strokeDasharray="4 4"
        />
        <circle
          cx="100"
          cy="100"
          r="60"
          className={`stroke-muted-foreground/20 transition-all duration-1000 delay-200 ${mounted ? 'opacity-100' : 'opacity-0'}`}
          strokeWidth="0.5"
        />

        {/* Flowing nodes */}
        {[0, 1, 2, 3, 4, 5].map((i) => (
          <g key={i} className={`animate-float`} style={{ animationDelay: `${i * 0.3}s` }}>
            <circle
              cx={100 + Math.cos((i * Math.PI) / 3) * 50}
              cy={100 + Math.sin((i * Math.PI) / 3) * 50}
              r="4"
              className={`fill-muted-foreground/30 transition-all duration-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}
              style={{ transitionDelay: `${i * 100 + 300}ms` }}
            />
            <line
              x1="100"
              y1="100"
              x2={100 + Math.cos((i * Math.PI) / 3) * 50}
              y2={100 + Math.sin((i * Math.PI) / 3) * 50}
              className={`stroke-muted-foreground/10 transition-all duration-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}
              strokeWidth="1"
              style={{ transitionDelay: `${i * 100 + 200}ms` }}
            />
          </g>
        ))}

        {/* Center AI core */}
        <circle
          cx="100"
          cy="100"
          r="12"
          className={`fill-primary/10 stroke-primary/30 transition-all duration-500 ${mounted ? 'scale-100' : 'scale-0'}`}
          strokeWidth="2"
          style={{ transformOrigin: 'center' }}
        />
        <circle
          cx="100"
          cy="100"
          r="6"
          className={`fill-primary/20 animate-pulse-soft transition-all duration-700 ${mounted ? 'opacity-100' : 'opacity-0'}`}
        />

        {/* Connection lines - drawn */}
        <path
          d={`M 100 88 Q 115 75 130 78`}
          className={`stroke-muted-foreground/20 ${mounted ? 'animate-draw-line' : ''}`}
          strokeWidth="1"
          fill="none"
          style={{ animationDelay: '0.5s' }}
        />
        <path
          d={`M 100 88 Q 85 75 70 78`}
          className={`stroke-muted-foreground/20 ${mounted ? 'animate-draw-line' : ''}`}
          strokeWidth="1"
          fill="none"
          style={{ animationDelay: '0.7s' }}
        />
      </svg>

      {/* Floating particles */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className={`absolute w-1 h-1 rounded-full bg-muted-foreground/20 animate-float transition-opacity duration-1000 ${mounted ? 'opacity-100' : 'opacity-0'}`}
            style={{
              left: `${20 + Math.random() * 60}%`,
              top: `${20 + Math.random() * 60}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${4 + Math.random() * 2}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
};

export default HeroAnimation;
