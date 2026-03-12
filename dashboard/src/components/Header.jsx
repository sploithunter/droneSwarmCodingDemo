import React from 'react';
import ConnectionStatus from './ConnectionStatus';
import ThemeToggle from './ThemeToggle';

export default function Header() {
  return (
    <header className="header" data-testid="header">
      <h1 className="header-title">Drone Swarm Monitor</h1>
      <div className="header-controls">
        <ConnectionStatus />
        <ThemeToggle />
      </div>
    </header>
  );
}
