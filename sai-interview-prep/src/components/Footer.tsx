const Footer = () => {
  const links = {
    Product: ['Features', 'Pricing', 'FAQ', 'Changelog'],
    Company: ['About', 'Blog', 'Careers', 'Contact'],
    Legal: ['Privacy', 'Terms', 'Security'],
  };

  return (
    <footer className="py-16 bg-background border-t border-border">
      <div className="container-custom">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="flex items-center gap-2 mb-4">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-sm">S</span>
              </div>
              <span className="font-semibold text-lg text-foreground">SAI</span>
            </div>
            <p className="text-sm text-muted-foreground max-w-xs">
              Your Smart AI Interviewer for comprehensive interview preparation.
            </p>
          </div>

          {/* Links */}
          {Object.entries(links).map(([category, items]) => (
            <div key={category}>
              <h4 className="font-medium text-foreground text-sm mb-4">{category}</h4>
              <ul className="space-y-3">
                {items.map((item) => (
                  <li key={item}>
                    <a
                      href="#"
                      className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                    >
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div className="pt-8 border-t border-border flex flex-col sm:flex-row justify-between items-center gap-4">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} SAI. All rights reserved.
          </p>
          <div className="flex items-center gap-6">
            <a
              href="#"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              Twitter
            </a>
            <a
              href="#"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              GitHub
            </a>
            <a
              href="#"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors duration-200"
            >
              LinkedIn
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
